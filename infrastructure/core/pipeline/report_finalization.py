"""Supervised final reports within the executor's finite run deadline."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.execution_boundary import build_bounded_env, run_bounded_subprocess
from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.core.pipeline.execution_custody import execution_guard_result
from infrastructure.core.pipeline.fingerprints import canonical_digest, paths_digest
from infrastructure.core.pipeline.execution_records import execution_record_payload
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.types import PipelineStageResult

if TYPE_CHECKING:
    from infrastructure.core.pipeline.executor import PipelineExecutor

_BOOTSTRAP = (
    "import runpy,sys;"
    "sys.path.insert(0,sys.argv.pop(1));"
    "runpy.run_module('infrastructure.core.pipeline.report_worker',run_name='__main__')"
)
REPORT_RECEIPT_SCHEMA = "template-report-finalization/1"
REPORT_FILES = ("pipeline_report.json", "pipeline_report.html", "pipeline_report.md")


def _failure(state: StageStatus, diagnostic: str, child_code: int | None = None) -> PipelineStageResult:
    code = (
        124
        if state is StageStatus.TIMED_OUT
        else 130
        if state is StageStatus.INTERRUPTED
        else 75
        if state is StageStatus.BLOCKED
        else 1
    )
    return PipelineStageResult(
        0,
        "Final reporting",
        False,
        0.0,
        code,
        diagnostic,
        stage_completed=False,
        stage_key="report_finalization",
        outcome=StageOutcome(
            "report_finalization",
            state,
            child_code,
            diagnostic,
            attempt_exit_codes=() if child_code is None else (child_code,),
        ),
    )


def finalize_execution_reports(
    executor: PipelineExecutor, results: list[PipelineStageResult]
) -> list[PipelineStageResult]:
    """Require a fresh bound report receipt; preserve failure/interruption precedence."""
    plan = executor.execution_plan
    assert plan is not None
    guard = execution_guard_result(
        config=executor.config,
        plan=plan,
        deadline=executor._run_deadline,
        completion=True,
        stage_key="report_finalization",
        stage_name="Final reporting",
    )
    if guard is not None:
        return [*results, guard]
    output = executor.config.runtime_output_dir
    receipt_path = output / ".pipeline" / "report_finalization.json"
    code: int | None = None
    try:
        record_path = output / ".pipeline" / "execution.json"
        record_bytes = read_bytes_confined(output, record_path)
        if canonical_digest(json.loads(record_bytes)) != canonical_digest(execution_record_payload(executor, results)):
            raise ValueError("Persisted execution record differs from current outcomes")
        record_digest = hashlib.sha256(record_bytes).hexdigest()
        original = paths_digest((output,), stable_output=True)
        remaining = min(120.0, executor._run_deadline - time.monotonic())
        if remaining <= 0:
            return [*results, _failure(StageStatus.TIMED_OUT, "Run deadline exhausted before reporting")]
        implementation_root = Path(__file__).resolve().parents[3]
        # A new empty bytecode namespace prevents old cached .pyc from standing
        # in for the source identity just checked by the controller.
        with tempfile.TemporaryDirectory(prefix="template-report-worker-") as temporary:
            cache = str(Path(temporary).resolve())
            bootstrap = (
                bytecode_audit_bootstrap(
                    (
                        implementation_root / "infrastructure",
                        executor.config.repo_root / "scripts",
                        executor.config.project_dir / "src",
                    ),
                    Path(cache),
                )
                + _BOOTSTRAP
            )
            child = run_bounded_subprocess(
                [
                    sys.executable,
                    "-I",
                    "-X",
                    f"pycache_prefix={cache}",
                    "-c",
                    bootstrap,
                    str(implementation_root),
                    "--repo-root",
                    str(executor.config.repo_root),
                    "--project",
                    executor.config.project_name,
                    "--projects-dir",
                    executor.config.projects_dir,
                    "--run-id",
                    executor.run_id,
                    "--plan-digest",
                    plan.digest,
                    "--record-digest",
                    record_digest,
                    "--pycache-prefix",
                    cache,
                    *(["--shared-infrastructure"] if executor.config.shared_infrastructure else []),
                ],
                cwd=executor.config.repo_root,
                env=build_bounded_env(),
                timeout=remaining,
            )
        code = child.original_returncode
        if code in {130, -2} or child.returncode in {130, -2}:
            return [*results, _failure(StageStatus.INTERRUPTED, "Final reporting interrupted", code)]
        if child.timed_out or code == 124 or child.returncode == 124:
            return [
                *results,
                _failure(StageStatus.TIMED_OUT, "Final reporting exceeded its remaining run budget", code),
            ]
        if code is not None and code not in {0, 75} and child.custody_refused:
            return [
                *results,
                _failure(StageStatus.FAILED, f"Final reporting child failed before custody refusal: {code}", code),
            ]
        if child.custody_refused or child.returncode == 75:
            return [
                *results,
                _failure(
                    StageStatus.BLOCKED,
                    f"Final reporting custody refused: {child.command_error or child.stderr[-2048:]}",
                    code,
                ),
            ]
        if child.returncode != 0 or child.command_error:
            return [
                *results,
                _failure(
                    StageStatus.FAILED,
                    f"Final reporting failed: {child.command_error or child.stderr[-2048:] or child.stdout[-2048:] or f'child exit {code}'}",
                    code,
                ),
            ]
        payload = json.loads(read_bytes_confined(output, receipt_path))
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != REPORT_RECEIPT_SCHEMA
            or payload.get("shared_infrastructure", False) is not executor.config.shared_infrastructure
            or payload.get("run_id") != executor.run_id
            or payload.get("plan_digest") != plan.digest
            or payload.get("source_identity") != plan.source_identity
            or payload.get("execution_record_digest") != record_digest
            or payload.get("status") != "succeeded"
            or payload.get("files") is None
        ):
            raise ValueError("Final report receipt does not bind this run and source")
        if read_bytes_confined(output, record_path) != record_bytes:
            raise ValueError("Execution record changed during reporting")
        files = payload["files"]
        if not isinstance(files, dict) or set(files) != set(REPORT_FILES):
            raise ValueError("Final reporting omitted a required format")
        for name in REPORT_FILES:
            if hashlib.sha256(read_bytes_confined(output, output / "reports" / name)).hexdigest() != files[name]:
                raise ValueError("Final report content differs from the consumed receipt")
        if paths_digest((output,), stable_output=True) != original:
            return [*results, _failure(StageStatus.BLOCKED, "Stable deliverables changed during reporting", code)]
        guard = execution_guard_result(
            config=executor.config,
            plan=plan,
            deadline=executor._run_deadline,
            completion=True,
            stage_key="report_finalization",
            stage_name="Final reporting",
        )
        if guard is not None:
            assert guard.outcome is not None
            guard.outcome = replace(
                guard.outcome, child_exit_code=code, attempt_exit_codes=() if code is None else (code,)
            )
            return [*results, guard]
        return results
    except KeyboardInterrupt:
        return [*results, _failure(StageStatus.INTERRUPTED, "Final reporting interrupted", code)]
    except (OSError, ValueError) as exc:
        return [*results, _failure(StageStatus.FAILED, f"Final report custody failed: {exc}", code)]


__all__ = ["finalize_execution_reports"]
