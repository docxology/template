"""Analysis adapter for the canonical audited Python stage supervisor."""

from __future__ import annotations

import math
import hashlib
import json
import time
import uuid
from dataclasses import replace
from pathlib import Path

from infrastructure.core.files.secure_write import atomic_write_text_confined, unlink_confined
from infrastructure.core.pipeline.fingerprints import source_fingerprint, source_content_fingerprint, canonical_digest
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.stage_launch import launch_python_stage
from infrastructure.core.runtime._python_env import validate_analysis_script_path
from infrastructure.core.runtime.python_binding import (
    AnalysisRuntimeUnavailable,
    analysis_runtime_binding,
    select_analysis_python,
)


def analysis_stage_key(script_path: Path, project_root: Path) -> str:
    """Distinct, stable project-relative keys include nested script directories."""
    return "analysis:" + script_path.absolute().relative_to(project_root.absolute()).as_posix()


def analysis_receipt_path(project_root: Path, run_id: str, stage_key: str) -> Path:
    """Caller values cannot redirect ignored runtime evidence outside its root."""
    run = hashlib.sha256(run_id.encode()).hexdigest()
    stage = hashlib.sha256(stage_key.encode()).hexdigest()
    return project_root / "output/.pipeline/analysis" / run / f"{stage}.json"


def launch_analysis_script(
    script_path: Path,
    repo_root: Path,
    project_root: Path,
    cmd: list[str],
    env: dict[str, str],
    deadline: float,
    *,
    stage_key: str | None = None,
    cwd: Path | None = None,
) -> StageOutcome:
    """Run the actual nominated runtime without resolver or dependency acquisition."""
    key = stage_key or analysis_stage_key(script_path, project_root)
    if type(deadline) not in (int, float) or not math.isfinite(deadline):
        raise ValueError("Analysis deadline must be finite")
    run_id = env.get("PIPELINE_RUN_ID") or uuid.uuid4().hex
    raw_receipt: dict[str, object] = {}
    before: dict[str, object] | None = None
    after: dict[str, object] | None = None
    result: StageOutcome | None = None
    try:
        if time.monotonic() >= deadline:
            raise TimeoutError("Analysis deadline expired before admission")
        script = validate_analysis_script_path(script_path, project_root)
        selected = select_analysis_python(project_root)
        if cmd != [str(selected), str(script)]:
            raise ValueError("Analysis command differs from its nominated interpreter and script")
        runtime = analysis_runtime_binding(project_root, interpreter=selected)
        source = source_fingerprint(repo_root, project_root)
        before = {
            "source_digest": source,
            "source_content_digest": source_content_fingerprint(repo_root, project_root),
            "runtime_digest": canonical_digest(runtime),
            "runtime_binding": runtime,
        }
        result = launch_python_stage(
            repo=repo_root,
            project=project_root,
            argv=cmd,
            env=env,
            deadline=deadline,
            stage_key=key,
            run_id=run_id,
            source_digest=source,
            definition=None,
            skip_path=project_root / "output/.pipeline/unused-analysis-skip.json",
            allow_skip=False,
            interpreter=selected,
            analysis_runtime=runtime,
            analysis_receipt=raw_receipt,
            cwd=cwd,
        )
        actual_runtime = analysis_runtime_binding(project_root, interpreter=selected)
        after = {
            "source_digest": source_fingerprint(repo_root, project_root),
            "source_content_digest": source_content_fingerprint(repo_root, project_root),
            "runtime_digest": canonical_digest(actual_runtime),
            "runtime_binding": actual_runtime,
        }
        if actual_runtime != runtime:
            raise ValueError("Selected analysis runtime changed during execution")
        if after["source_digest"] != source:
            raise ValueError("Analysis controller source changed during execution")
    except KeyboardInterrupt:
        result = (
            replace(result, status=StageStatus.INTERRUPTED, diagnostic="Analysis supervisor interrupted")
            if result is not None
            else _unreturned_outcome(
                key,
                raw_receipt,
                StageStatus.INTERRUPTED,
                "Analysis supervisor interrupted; no verified leaf exit",
            )
        )
    except TimeoutError as exc:
        result = (
            replace(result, status=StageStatus.TIMED_OUT, diagnostic=str(exc))
            if result is not None
            else _unreturned_outcome(key, raw_receipt, StageStatus.TIMED_OUT, str(exc))
        )
    except (AnalysisRuntimeUnavailable, OSError, ValueError) as exc:
        if result is None:
            result = _unreturned_outcome(key, raw_receipt, StageStatus.BLOCKED, f"Analysis admission refused: {exc}")
        else:
            state = result.status if not result.complete else StageStatus.BLOCKED
            result = replace(result, status=state, diagnostic=f"{result.diagnostic}; analysis custody refused: {exc}")
    assert result is not None
    if time.monotonic() >= deadline and result.status is not StageStatus.INTERRUPTED:
        result = replace(
            result, status=StageStatus.TIMED_OUT, diagnostic=f"{result.diagnostic}; analysis deadline exhausted"
        )
    return _persist_analysis_result(
        repo_root,
        project_root,
        run_id,
        env.get("PIPELINE_PLAN_DIGEST", ""),
        result,
        before,
        after,
        raw_receipt or None,
        deadline,
    )


def _unreturned_outcome(key: str, validated: dict[str, object], state: StageStatus, diagnostic: str) -> StageOutcome:
    """Retain a launcher-validated original if its scratch cleanup was interrupted."""
    completion = validated.get("completion")
    original = completion.get("original_exit_code") if isinstance(completion, dict) else None
    original = original if type(original) is int and 0 <= original <= 255 else None
    if original is not None:
        diagnostic = diagnostic.replace("; no verified leaf exit", "") + "; verified original leaf exit retained"
    return StageOutcome(
        key, state, original, diagnostic, attempt_exit_codes=(original,) if original is not None else ()
    )


def _persist_analysis_result(
    repo: Path,
    project: Path,
    run_id: str,
    plan_digest: str,
    result: StageOutcome,
    before: dict[str, object] | None,
    after: dict[str, object] | None,
    worker: dict[str, object] | None,
    deadline: float,
) -> StageOutcome:
    """An incomplete or missing worker receipt cannot become completion evidence."""
    target = analysis_receipt_path(project, run_id, result.stage_key)
    record = {
        "schema": "template-analysis-leaf/1",
        "run_id": run_id,
        "stage_key": result.stage_key,
        "plan_digest": plan_digest,
        "controller_before": before,
        "controller_after": after,
        "worker": worker,
        "outcome": result.to_dict(),
        "complete": result.complete,
        "dependency_proof": "metadata-record-declarations",
        "cache_reuse_authorized": False,
    }
    attempted = False
    try:
        if result.complete and (worker is None or before is None or after != before):
            raise ValueError("Analysis completion requires unchanged controller and actual worker evidence")
        # This invocation owns its run/stage evidence slot. Mark ownership
        # before rename: interruption during the writer's final fsync must
        # invalidate a possibly promoted receipt, including prior retry data.
        attempted = True
        atomic_write_text_confined(project, target, json.dumps(record, sort_keys=True) + "\n", mode=0o600)
        if result.complete and before is not None:
            actual = analysis_runtime_binding(project)
            if (
                canonical_digest(actual) != before["runtime_digest"]
                or source_fingerprint(repo, project) != before["source_digest"]
            ):
                result = replace(
                    result,
                    status=StageStatus.BLOCKED,
                    diagnostic="Analysis source/runtime changed during evidence promotion",
                )
                record.update(outcome=result.to_dict(), complete=False)
                atomic_write_text_confined(project, target, json.dumps(record, sort_keys=True) + "\n", mode=0o600)
        if time.monotonic() >= deadline and result.status is not StageStatus.INTERRUPTED:
            result = replace(
                result, status=StageStatus.TIMED_OUT, diagnostic=f"{result.diagnostic}; evidence deadline exhausted"
            )
            record.update(outcome=result.to_dict(), complete=False)
            atomic_write_text_confined(project, target, json.dumps(record, sort_keys=True) + "\n", mode=0o600)
    except KeyboardInterrupt:
        result = replace(
            result, status=StageStatus.INTERRUPTED, diagnostic=f"{result.diagnostic}; evidence promotion interrupted"
        )
        if attempted:
            result = _remove_promoted(project, target, result)
    except (OSError, ValueError) as exc:
        state = result.status if not result.complete else StageStatus.FAILED
        result = replace(result, status=state, diagnostic=f"{result.diagnostic}; analysis evidence refused: {exc}")
        if attempted:
            result = _remove_promoted(project, target, result)
    return result


def _remove_promoted(project: Path, target: Path, result: StageOutcome) -> StageOutcome:
    try:
        unlink_confined(project, target)
    except KeyboardInterrupt:
        return replace(
            result, status=StageStatus.INTERRUPTED, diagnostic=f"{result.diagnostic}; evidence removal interrupted"
        )
    except (OSError, ValueError) as exc:
        return replace(result, diagnostic=f"{result.diagnostic}; owned evidence removal refused: {exc}")
    return result


__all__ = ["analysis_receipt_path", "analysis_stage_key", "launch_analysis_script"]
