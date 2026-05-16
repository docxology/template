"""Analysis-stage pipeline runner.

Executes a project's analysis scripts (the lexicographic list returned by
:func:`infrastructure.core.script_discovery.discover_analysis_scripts`) under
the standard subprocess contract used by Stage-02:

* Each script is invoked with the project's preferred interpreter (project-local
  ``.venv`` when present, root venv otherwise — see
  :func:`infrastructure.core.runtime.environment.build_analysis_script_cmd_and_env`).
* Per-script timeout from ``ANALYSIS_SCRIPT_TIMEOUT_SEC`` (default 7200s).
* Sub-stage progress reporting with EMA-based ETA.

This module exists so that ``scripts/02_run_analysis.py`` can stay a thin
orchestrator that only parses CLI arguments and dispatches here.
"""

import shlex
import subprocess  # nosec B404
import time
from pathlib import Path

from infrastructure.core.analysis_timeout import parse_analysis_script_timeout_sec
from infrastructure.core.exceptions import ScriptExecutionError
from infrastructure.core.logging.utils import (
    get_logger,
    log_operation,
    log_success,
)
from infrastructure.core.progress import SubStageProgress
from infrastructure.core.runtime.environment import build_analysis_script_cmd_and_env
from infrastructure.project.discovery import resolve_project_root

logger = get_logger(__name__)


def run_analysis_script(
    script_path: Path,
    repo_root: Path,
    project_name: str = "project",
) -> int:
    """Execute a single analysis script under the Stage-02 contract.

    Args:
        script_path: Path to the analysis script (typically ``projects/<name>/scripts/*.py``).
        repo_root: Repository root.
        project_name: Project name under ``projects/``.

    Returns:
        The script's exit code. ``0`` indicates success.

    Raises:
        ScriptExecutionError: If subprocess invocation itself fails (not when the
            script exits non-zero — that is reported via the return value).
    """
    project_root = resolve_project_root(repo_root, project_name)
    logger.info("")
    logger.info("  Script: %s", script_path.resolve())
    logger.info("  Project root: %s", project_root.resolve())
    logger.info("  Working directory (subprocess cwd): %s", repo_root.resolve())

    cmd, env = build_analysis_script_cmd_and_env(script_path, project_root, repo_root)
    logger.info("  Command: %s", " ".join(shlex.quote(str(part)) for part in cmd))

    project_venv = project_root / ".venv"
    if project_venv.is_dir():
        logger.info("  Using project-local venv: %s", project_venv.resolve())

    timeout_sec = parse_analysis_script_timeout_sec()
    if timeout_sec is None:
        logger.info("  Per-script timeout: unlimited (ANALYSIS_SCRIPT_TIMEOUT_SEC unset or 0/none/unlimited)")
    else:
        logger.info(
            "  Per-script timeout: %.0fs (default 7200s; override via ANALYSIS_SCRIPT_TIMEOUT_SEC)",
            timeout_sec,
        )

    started = time.monotonic()
    try:
        with log_operation(f"Execute {script_path.name}", logger):
            result = subprocess.run(  # nosec B603
                cmd,
                cwd=str(repo_root),
                capture_output=False,
                check=False,
                env=env,
                timeout=timeout_sec,
            )
    except Exception as e:  # noqa: BLE001 — wrap as ScriptExecutionError for callers
        raise ScriptExecutionError(
            f"Failed to execute {script_path.name}",
            context={"script": str(script_path), "error": str(e)},
        ) from e

    elapsed = time.monotonic() - started
    log_fn = logger.info if result.returncode == 0 else logger.error
    log_fn("  Finished %s in %.1fs (exit %s)", script_path.name, elapsed, result.returncode)

    if result.returncode != 0:
        logger.info("  Troubleshooting:")
        logger.info("    - Run script manually: python3 %s", script_path)
        logger.info("    - Check script syntax: python3 -m py_compile %s", script_path)
        logger.info("    - Verify dependencies: Check imports in %s", script_path.name)
        logger.info("    - Review script logs above for specific error details")

    return result.returncode


def run_analysis_pipeline(
    scripts: list[Path],
    repo_root: Path,
    project_name: str = "project",
) -> int:
    """Execute all analysis scripts in sequence.

    Args:
        scripts: Lexicographic list of script paths (from ``discover_analysis_scripts``).
        repo_root: Repository root.
        project_name: Project name under ``projects/``.

    Returns:
        ``0`` if every script exited successfully, ``1`` otherwise.
    """
    logger.info("[STAGE-02] Executing analysis pipeline...")
    if not scripts:
        logger.info("  No analysis scripts found - skipping stage")
        return 0

    successful: list[str] = []
    failed: list[str] = []
    progress = SubStageProgress(total=len(scripts), stage_name="Analysis Pipeline", use_ema=True)

    for i, script in enumerate(scripts, 1):
        progress.start_substage(i, f"{project_name}/{script.name}")
        rc = run_analysis_script(script, repo_root, project_name)
        progress.complete_substage()
        if i % 2 == 0 or i == len(scripts):
            progress.log_progress()
        (successful if rc == 0 else failed).append(script.name)

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
        return 1

    return 0


__all__ = [
    "run_analysis_pipeline",
    "run_analysis_script",
]
