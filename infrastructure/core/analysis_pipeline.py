"""Analysis-stage pipeline runner.

Executes a project's analysis scripts (the ordered list returned by
:func:`infrastructure.core.script_discovery.discover_analysis_scripts`) under
the standard subprocess contract used by Stage-02:

* Each script is invoked with the project's preferred interpreter (project-local
  ``.venv`` when present, the running interpreter otherwise — see
  :func:`infrastructure.core.runtime.environment.build_analysis_script_cmd_and_env`).
* Per-script timeout from ``ANALYSIS_SCRIPT_TIMEOUT_SEC`` (default 7200s).
* Sub-stage progress reporting with EMA-based ETA.
* Audited held-source execution, selected-runtime admission, and typed outcomes.

This module exists so that ``scripts/pipeline/stage_02_analysis.py`` can stay a thin
orchestrator that only parses CLI arguments and dispatches here.
"""

import shlex
import time
import os
import uuid
from collections.abc import Mapping
from pathlib import Path

from infrastructure.core.analysis_evidence import AnalysisRunEvidence
from infrastructure.core.analysis_timeout import analysis_run_timeout_seconds, parse_analysis_script_timeout_sec
from infrastructure.core.execution_policy import apply_execution_policy
from infrastructure.core.analysis_launch import analysis_stage_key, launch_analysis_script
from infrastructure.core.exceptions import ScriptExecutionError
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.fingerprints import canonical_digest, source_fingerprint
from infrastructure.core.logging.utils import (
    get_logger,
    log_operation,
    log_success,
)
from infrastructure.core.progress import SubStageProgress
from infrastructure.core.runtime.environment import build_analysis_script_cmd_and_env
from infrastructure.core.runtime.python_binding import AnalysisRuntimeUnavailable
from infrastructure.core.project_paths import resolve_project_root

logger = get_logger(__name__)


def run_analysis_script_outcome(
    script_path: Path,
    repo_root: Path,
    project_name: str = "project",
    *,
    run_id: str | None = None,
    plan_digest: str | None = None,
    deadline: float | None = None,
    base_env: Mapping[str, str] | None = None,
) -> StageOutcome:
    """Execute a single analysis script under the Stage-02 contract.

    Args:
        script_path: Path to the analysis script (typically ``projects/<name>/scripts/*.py``).
        repo_root: Repository root.
        project_name: Project name under ``projects/``.

    Returns:
        The original child outcome, with supervisory timeout/interruption and
        source/runtime refusals distinguished from executed failures.

    Raises:
        ScriptExecutionError: If subprocess invocation itself fails (not when the
            script exits non-zero — that is reported via the return value).
    """
    project_root = resolve_project_root(repo_root, project_name)
    try:
        key = analysis_stage_key(script_path, project_root)
    except ValueError as exc:
        return StageOutcome("analysis:invalid-path", StageStatus.FAILED, None, str(exc))
    logger.info("")
    logger.info("  Script: %s", script_path.resolve())
    logger.info("  Project root: %s", project_root.resolve())
    logger.info("  Working directory (subprocess cwd): %s", repo_root.resolve())

    try:
        cmd, env = build_analysis_script_cmd_and_env(script_path, project_root, repo_root, base_env=base_env)
    except AnalysisRuntimeUnavailable as exc:
        logger.error("Analysis runtime unavailable: %s", exc)
        return StageOutcome(key, StageStatus.BLOCKED, None, str(exc))
    except (OSError, ValueError) as exc:
        logger.error("Refusing invalid analysis script: %s", exc)
        return StageOutcome(key, StageStatus.FAILED, None, str(exc))
    logger.info("  Command: %s", " ".join(shlex.quote(str(part)) for part in cmd))

    project_venv = project_root / ".venv"
    if project_venv.is_dir():
        logger.info("  Using project-local venv: %s", project_venv.resolve())

    timeout_sec = parse_analysis_script_timeout_sec(env)
    logger.info(
        "  Per-script timeout: %.3fs (default 7200s; override via ANALYSIS_SCRIPT_TIMEOUT_SEC)",
        timeout_sec,
    )

    if run_id is not None:
        env["PIPELINE_RUN_ID"] = run_id
    if plan_digest is not None:
        env["PIPELINE_PLAN_DIGEST"] = plan_digest
    started = time.monotonic()
    leaf_deadline = started + timeout_sec
    if deadline is not None:
        leaf_deadline = min(leaf_deadline, deadline)
    try:
        with log_operation(f"Execute {script_path.name}", logger):
            result = launch_analysis_script(
                script_path, repo_root, project_root, cmd, env, leaf_deadline, stage_key=key
            )
    except Exception as e:  # noqa: BLE001 — wrap as ScriptExecutionError for callers
        raise ScriptExecutionError(
            f"Failed to execute {script_path.name}",
            context={"script": str(script_path), "error": str(e)},
        ) from e

    elapsed = time.monotonic() - started
    log_fn = logger.info if result.complete else logger.error
    log_fn(
        "  Finished %s in %.1fs (%s; original child exit %s)",
        script_path.name,
        elapsed,
        result.status,
        result.child_exit_code,
    )
    if result.diagnostic:
        logger.error("  %s", result.diagnostic)

    if not result.complete:
        logger.info("  Troubleshooting:")
        logger.info("    - Run script manually: python3 %s", script_path)
        logger.info("    - Check script syntax: python3 -m py_compile %s", script_path)
        logger.info("    - Verify dependencies: Check imports in %s", script_path.name)
        logger.info("    - Review script logs above for specific error details")

    return result


def run_analysis_script(script_path: Path, repo_root: Path, project_name: str = "project") -> int:
    """Return the original leaf exit unless a typed supervisory state takes precedence."""
    result = run_analysis_script_outcome(script_path, repo_root, project_name)
    if result.status is StageStatus.INTERRUPTED:
        return 130
    if result.status is StageStatus.TIMED_OUT:
        return 124
    if result.status in {StageStatus.PAUSED, StageStatus.BLOCKED}:
        return 75
    return result.child_exit_code if result.child_exit_code is not None else 1


def run_analysis_pipeline(
    scripts: list[Path],
    repo_root: Path,
    project_name: str = "project",
    *,
    base_env: Mapping[str, str] | None = None,
) -> int:
    """Execute all analysis scripts in sequence.

    Args:
        scripts: Configuration-declared or lexicographic-fallback script paths
            from ``discover_analysis_scripts``.
        repo_root: Repository root.
        project_name: Project name under ``projects/``.

    Returns:
        Complete ``0``; interruption ``130``; timeout ``124``; executed failure
        ``1``; runtime/source block ``75``. Original outcomes remain in diagnostics.
    """
    logger.info("[STAGE-02] Executing analysis pipeline...")
    if not scripts:
        logger.info("  No analysis scripts found - skipping stage")
        return 0

    project_root = resolve_project_root(repo_root, project_name)
    expected = tuple(analysis_stage_key(script, project_root) for script in scripts)
    if len(expected) != len(set(expected)):
        raise ValueError("Analysis execution requires unique script identities")
    environment = apply_execution_policy(dict(os.environ if base_env is None else base_env), repo_root)
    deadline = time.monotonic() + analysis_run_timeout_seconds(len(scripts), environment)
    policy = {
        key: environment[key]
        for key in (
            "SOURCE_DATE_EPOCH",
            "TEMPLATE_EXECUTION_MODE",
            "TEMPLATE_DETERMINISTIC",
            "TEMPLATE_BUILD_EPOCH_SOURCE",
        )
    }
    source = source_fingerprint(repo_root, project_root)
    run_id = environment.get("PIPELINE_RUN_ID") or uuid.uuid4().hex
    plan_digest = environment.get("PIPELINE_PLAN_DIGEST") or canonical_digest(
        {
            "schema": "template-analysis-selection/1",
            "expected_stage_keys": expected,
            "source_digest": source,
            "policy": policy,
        }
    )
    evidence = AnalysisRunEvidence(repo_root, project_root, run_id, plan_digest, expected, source, deadline, policy)
    successful: list[str] = []
    failed: list[str] = []
    outcomes: list[StageOutcome] = []
    progress = SubStageProgress(total=len(scripts), stage_name="Analysis Pipeline", use_ema=True)

    for i, script in enumerate(scripts, 1):
        progress.start_substage(i, f"{project_name}/{script.name}")
        try:
            if source_fingerprint(repo_root, project_root) != source:
                raise ValueError("Analysis source changed before the next producer")
            outcome = run_analysis_script_outcome(
                script,
                repo_root,
                project_name,
                run_id=run_id,
                plan_digest=plan_digest,
                deadline=deadline,
                base_env=environment,
            )
        except KeyboardInterrupt:
            outcome = StageOutcome(expected[i - 1], StageStatus.INTERRUPTED, None, "Analysis supervisor interrupted")
        except ScriptExecutionError as exc:
            outcome = StageOutcome(expected[i - 1], StageStatus.FAILED, None, str(exc))
        except (OSError, ValueError) as exc:
            outcome = StageOutcome(expected[i - 1], StageStatus.BLOCKED, None, str(exc))
        outcomes.append(outcome)
        try:
            evidence.admit_leaf(outcome)
        except KeyboardInterrupt:
            outcomes.append(StageOutcome("analysis:evidence", StageStatus.INTERRUPTED, None, "Leaf audit interrupted"))
        except (OSError, ValueError) as exc:
            outcomes.append(StageOutcome("analysis:evidence", StageStatus.BLOCKED, None, str(exc)))
        progress.complete_substage()
        if i % 2 == 0 or i == len(scripts):
            progress.log_progress()
        (successful if outcome.complete else failed).append(script.name)
        if len(outcomes) > i or outcome.status in {StageStatus.INTERRUPTED, StageStatus.TIMED_OUT, StageStatus.BLOCKED}:
            logger.error(
                "  Analysis stopped after %s (%s); remaining producers did not execute", script.name, outcome.status
            )
            break

    if successful:
        listed = ", ".join(f"{project_name}/{name}" for name in successful)
        log_success(
            f"Analysis scripts completed: {len(successful)}/{len(scripts)} ({listed})",
            logger,
        )

    if failed:
        logger.error("\n%d script(s) failed:", len(failed))
        for name in failed:
            logger.error("  Failed: %s", name)
        logger.info("\n  Troubleshooting:")
        logger.info("    - Review error messages above for each failed script")
        logger.info("    - Run scripts individually to isolate issues")
        logger.info("    - Check script dependencies and imports")
        logger.info("    - Verify input data files exist if required")
    return evidence.finish(outcomes).exit_code


__all__ = [
    "run_analysis_pipeline",
    "run_analysis_script",
    "run_analysis_script_outcome",
]
