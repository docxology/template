"""Frozen multi-project plans and a finite, independently guarded subprocess scheduler."""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Sequence, TYPE_CHECKING

from infrastructure.core._bounded_run_guardian import (
    BoundedRunGuardian,
    GuardianCustodyError,
    start_bounded_run_guardian,
)
from infrastructure.core.execution_boundary import (
    build_bounded_env,
    build_bounded_run_env,
    _complete_bounded_run_cleanup,
    terminate_process_tree,
)
from infrastructure.core.files.secure_write import append_text_confined, read_bytes_confined
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap
from infrastructure.core.pipeline.plan import ExecutionPlan, compile_execution_plan
from infrastructure.core.pipeline.outcomes import RunResult, StageOutcome, StageStatus
from infrastructure.core.pipeline.types import PipelineConfig, PipelineStageResult
from infrastructure.core.pipeline.multi_project_output import BoundedWorkerOutput

if TYPE_CHECKING:
    from infrastructure.project.project_info import ProjectInfo

WORKER_SCHEMA = "template-multi-project-worker/2"


def _worker_bootstrap(implementation: Path, project: Path) -> str:
    """Audit actual module execution before importing the worker's public code."""
    return (
        "import runpy,sys\nsys.pycache_prefix=sys.argv.pop(1)\nsys.dont_write_bytecode=False\n"
        + bytecode_audit_bootstrap(
            (implementation / "infrastructure", implementation / "scripts", project / "src"), None
        )
        + "sys.path.insert(0,sys.argv.pop(1))\n"
        "runpy.run_module('infrastructure.core.pipeline.multi_project_worker',run_name='__main__')\n"
    )


@dataclass(frozen=True)
class ProjectExecutionSpec:
    config: PipelineConfig
    plan: ExecutionPlan

    def to_dict(self) -> dict[str, Any]:
        config = self.config
        return {
            "config": {
                "project_name": config.project_name,
                "repo_root": str(config.repo_root),
                "projects_dir": config.projects_dir,
                "clean": config.clean,
                "skip_infra": config.skip_infra,
                "resume": config.resume,
                "shared_infrastructure": config.shared_infrastructure,
                "mode": config.mode,
                "run_timeout_seconds": config.run_timeout_seconds,
                "pipeline_path": str(config.pipeline_path) if config.pipeline_path is not None else None,
            },
            "plan": self.plan.to_dict(),
            "plan_digest": self.plan.digest,
        }


def validate_budget(seconds: float) -> None:
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("multi-project run timeout must be positive and finite")


def selected_project_config(
    project: ProjectInfo | str,
    repo_root: Path,
    *,
    mode: str,
    resume: bool,
    timeout: float,
) -> PipelineConfig:
    """Construct the canonical selected-project policy without resolving a plan."""
    validate_budget(timeout)
    if not isinstance(mode, str) or mode not in {"core", "live"}:
        raise ValueError(f"Invalid execution mode: {mode}")
    name = project if isinstance(project, str) else project.qualified_name
    projects_dir = "projects"
    if not isinstance(project, str):
        try:
            projects_dir = project.path.absolute().relative_to(repo_root.absolute()).parts[0]
        except ValueError, IndexError:
            pass
    return PipelineConfig(
        name,
        repo_root,
        projects_dir=projects_dir,
        skip_infra=True,
        mode=mode,
        resume=resume,
        run_timeout_seconds=timeout,
    )


def freeze_project_plans(
    projects: Sequence[ProjectInfo | str],
    repo_root: Path,
    *,
    mode: str,
    resume: bool,
    timeout: float,
) -> tuple[ProjectExecutionSpec, ...]:
    """Compile every selected effective definition before any shared gate or worker."""
    validate_budget(timeout)
    if not isinstance(mode, str) or mode not in {"core", "live"}:
        raise ValueError(f"Invalid execution mode: {mode}")
    specs = []
    for project in projects:
        config = selected_project_config(project, repo_root, mode=mode, resume=resume, timeout=timeout)
        plan = compile_execution_plan(config)
        if not plan.stages:
            raise ValueError(f"Selected project has no executable stages: {config.project_name}")
        specs.append(ProjectExecutionSpec(config, plan))
    names = tuple(spec.plan.project for spec in specs)
    if len(set(names)) != len(names):
        raise ValueError("Duplicate selected project identities")
    return tuple(specs)


def selected_shared_config(specs: tuple[ProjectExecutionSpec, ...]) -> PipelineConfig:
    """Construct the once-only shared-test policy without resolving a plan."""
    if not specs:
        raise ValueError("Shared infrastructure requires selected projects")
    first = next((spec for spec in specs if spec.plan.project.startswith("templates/")), specs[0])
    return PipelineConfig(
        first.config.project_name,
        first.config.repo_root,
        projects_dir=first.config.projects_dir,
        clean=False,
        shared_infrastructure=True,
        pipeline_path=first.config.repo_root / "infrastructure/core/pipeline/pipeline.yaml",
        run_timeout_seconds=first.config.run_timeout_seconds,
    )


def freeze_shared_plan(specs: tuple[ProjectExecutionSpec, ...]) -> ProjectExecutionSpec:
    config = selected_shared_config(specs)
    return ProjectExecutionSpec(config, compile_execution_plan(config, target_stage="infra_tests"))


def results_from_payload(rows: Any) -> list[PipelineStageResult]:
    """Refuse malformed or contradictory stage evidence at the worker boundary."""
    if not isinstance(rows, list):
        raise ValueError("Worker stage results must be a list")
    expected = {field.name for field in fields(PipelineStageResult)}
    result = []
    for raw in rows:
        if not isinstance(raw, dict) or set(raw) != expected or not isinstance(raw["outcome"], dict):
            raise ValueError("Worker must return complete typed stage evidence")
        row = dict(raw)
        for name in ("success", "hitl_pause", "stage_completed"):
            if type(row[name]) is not bool:
                raise ValueError("Worker stage flags must be exact booleans")
        if (
            type(row["stage_num"]) is not int
            or row["stage_num"] < 0
            or type(row["exit_code"]) is not int
            or isinstance(row["duration"], bool)
            or not isinstance(row["duration"], (int, float))
            or not math.isfinite(row["duration"])
            or row["duration"] < 0
        ):
            raise ValueError("Worker stage numeric evidence is invalid")
        if any(
            not isinstance(row[name], str)
            for name in ("stage_name", "error_message", "exception_type", "stage_key", "input_digest", "output_digest")
        ):
            raise ValueError("Worker stage text evidence must be strings")
        if not isinstance(row["lessons"], list) or any(not isinstance(item, str) for item in row["lessons"]):
            raise ValueError("Worker stage lessons must be a string list")
        outcome = dict(row["outcome"])
        if set(outcome) != {field.name for field in fields(StageOutcome)}:
            raise ValueError("Worker stage outcome requires exact evidence fields")
        if any(not isinstance(outcome[name], str) for name in ("stage_key", "diagnostic", "reason", "status")):
            raise ValueError("Worker outcome text evidence must be strings")
        if not isinstance(outcome["attempt_exit_codes"], list):
            raise ValueError("Worker attempt codes must be a list")
        outcome["status"] = StageStatus(outcome["status"])
        outcome["attempt_exit_codes"] = tuple(outcome["attempt_exit_codes"])
        row["outcome"] = StageOutcome(**outcome)
        row["lessons"] = tuple(row["lessons"])
        if row["stage_key"] != row["outcome"].stage_key or row["success"] != row["outcome"].complete:
            raise ValueError("Worker stage and outcome identities or completion differ")
        result.append(PipelineStageResult(**row))
    return result


def runtime_failure(
    spec: ProjectExecutionSpec,
    state: StageStatus,
    diagnostic: str,
    code: int | None = None,
    rows: list[PipelineStageResult] | None = None,
) -> tuple[list[PipelineStageResult], RunResult]:
    exit_code = (
        130
        if state is StageStatus.INTERRUPTED
        else 124
        if state is StageStatus.TIMED_OUT
        else 75
        if state is StageStatus.BLOCKED
        else 1
    )
    outcome = StageOutcome("multi_project_runtime", state, code, diagnostic)
    results = [
        *(rows or []),
        PipelineStageResult(
            0,
            "Multi-project runtime",
            False,
            0.0,
            exit_code,
            diagnostic,
            stage_completed=False,
            stage_key=outcome.stage_key,
            outcome=outcome,
        ),
    ]
    return results, RunResult.from_results(results, spec.plan.expected_stage_keys)


@dataclass
class _Running:
    spec: ProjectExecutionSpec
    process: subprocess.Popen[bytes]
    guardian: BoundedRunGuardian | None
    token: str
    nonce: str
    receipt: Path
    directory: Path
    output: BoundedWorkerOutput
    cleanup_done: bool = False
    cleanup_error: str = ""
    custody_error: GuardianCustodyError | None = None

    def close(self, *, terminate: bool) -> str:
        if self.cleanup_done:
            if self.custody_error is not None:
                raise self.custody_error
            return self.cleanup_error
        if terminate or self.process.poll() is None:
            terminate_process_tree(self.process.pid, group_id=self.process.pid)
        error = ""
        try:
            error = _complete_bounded_run_cleanup(self.guardian, self.token)
        except GuardianCustodyError as exc:
            self.custody_error = exc
        finally:
            with contextlib.suppress(subprocess.TimeoutExpired):
                self.process.wait(timeout=5)
            output_error = self.output.finish()
            self.cleanup_done = True
            self.cleanup_error = error or output_error
        if self.custody_error is not None:
            raise self.custody_error
        return self.cleanup_error


def _launch(spec: ProjectExecutionSpec, directory: Path, deadline: float) -> _Running:
    if time.monotonic() >= deadline:
        raise TimeoutError("whole multi-project deadline exhausted before worker launch")
    nonce = uuid.uuid4().hex
    directory.mkdir()
    payload = {"schema_version": WORKER_SCHEMA, "nonce": nonce, "deadline_monotonic": deadline, **spec.to_dict()}
    content = json.dumps(payload, sort_keys=True, allow_nan=False).encode()
    request = directory / "request.json"
    request.write_bytes(content)
    request.chmod(0o400)
    receipt = directory / "result.json"
    # The guardian stays credential-free. The worker receives the same base
    # environment the parent used to compile and admit this plan (as in
    # single-project execution); a stripped worker environment would make the
    # worker's own source/environment admission refuse its parent's plan.
    environment = build_bounded_env()
    process_env, token = build_bounded_run_env(dict(os.environ))
    output = None
    guardian = None
    process = None
    try:
        guardian = start_bounded_run_guardian(environment, deadline_monotonic=deadline)
        if time.monotonic() >= deadline:
            raise TimeoutError("whole multi-project deadline exhausted during guardian startup")
        implementation = Path(__file__).resolve().parents[3]
        command = [
            sys.executable,
            "-I",
            "-c",
            _worker_bootstrap(implementation, spec.config.project_dir),
            str(directory / "bytecode"),
            str(implementation),
            "--request",
            str(request),
            "--request-sha256",
            hashlib.sha256(content).hexdigest(),
            "--receipt",
            str(receipt),
        ]
        process = subprocess.Popen(
            command,
            cwd=spec.config.repo_root,
            env=process_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        assert process.stdout is not None
        output = BoundedWorkerOutput(process.stdout)
        if guardian is not None:
            guardian.arm(root_pid=process.pid, run_token=token, deadline_monotonic=deadline)
        return _Running(spec, process, guardian, token, nonce, receipt, directory, output)
    except BaseException as original:
        if process is not None:
            terminate_process_tree(process.pid, group_id=process.pid)
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=5)
        cleanup_custody = None
        try:
            _complete_bounded_run_cleanup(guardian, token)
        except GuardianCustodyError as exc:
            cleanup_custody = exc
        finally:
            if output is not None:
                output.finish()
                output.close()
        if cleanup_custody is not None and not isinstance(original, (KeyboardInterrupt, TimeoutError)):
            raise cleanup_custody from original
        raise


def _finish(
    running: _Running, deadline: float, state: StageStatus | None = None
) -> tuple[list[PipelineStageResult], RunResult]:
    rows: list[PipelineStageResult] = []
    custody_error: GuardianCustodyError | None = None
    try:
        try:
            cleanup_error = running.close(terminate=state is not None)
        except GuardianCustodyError as exc:
            custody_error = exc
            cleanup_error = running.cleanup_error
        child_code = running.process.returncode
        if state is StageStatus.INTERRUPTED:
            return runtime_failure(
                running.spec, StageStatus.INTERRUPTED, "Whole multi-project run interrupted", child_code
            )
        if child_code in {130, -2}:
            return runtime_failure(
                running.spec, StageStatus.INTERRUPTED, "Actual project worker interrupted", child_code
            )
        if child_code == 124:
            return runtime_failure(running.spec, StageStatus.TIMED_OUT, "Actual project worker timed out", child_code)
        content = running.output.read()
        append_text_confined(
            running.spec.config.runtime_output_dir,
            running.spec.config.runtime_output_dir / "logs/multi_project_worker.log",
            content.decode(errors="replace"),
        )
        if running.output.overflow.is_set():
            raise ValueError("Worker output exceeded its 8 MiB bound")
        if state is not None:
            return runtime_failure(running.spec, state, "Whole multi-project run interrupted or timed out", child_code)
        if cleanup_error:
            raise ValueError(cleanup_error)
        payload = json.loads(read_bytes_confined(running.directory, running.receipt))
        plan = running.spec.plan
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != WORKER_SCHEMA
            or payload.get("nonce") != running.nonce
            or type(payload.get("shared_infrastructure")) is not bool
            or payload["shared_infrastructure"] != running.spec.config.shared_infrastructure
            or payload.get("project") != plan.project
            or payload.get("plan_digest") != plan.digest
            or payload.get("source_identity") != plan.source_identity
            or payload.get("environment_identity") != plan.environment_identity
            or payload.get("expected_stage_keys") != list(plan.expected_stage_keys)
        ):
            raise ValueError("Worker receipt differs from the parent's frozen plan and invocation")
        rows = results_from_payload(payload["stage_results"])
        run = RunResult.from_results(rows, plan.expected_stage_keys)
        if (
            child_code != run.exit_code
            or type(payload.get("exit_code")) is not int
            or payload["exit_code"] != run.exit_code
        ):
            raise ValueError("Worker child exit and typed aggregate evidence differ")
        if custody_error is not None:
            return runtime_failure(running.spec, state or StageStatus.BLOCKED, str(custody_error), child_code, rows)
        if time.monotonic() >= deadline:
            return runtime_failure(
                running.spec, StageStatus.TIMED_OUT, "Whole deadline expired after worker cleanup", child_code, rows
            )
        from infrastructure.core.pipeline.execution_custody import execution_guard_result

        guard = execution_guard_result(config=running.spec.config, plan=plan, deadline=deadline, completion=True)
        if guard is not None:
            rows.append(guard)
            return rows, RunResult.from_results(rows, plan.expected_stage_keys)
        return rows, run
    except KeyboardInterrupt:
        with contextlib.suppress(GuardianCustodyError):
            running.close(terminate=True)
        return runtime_failure(
            running.spec, StageStatus.INTERRUPTED, "Multi-project cleanup interrupted", running.process.returncode, rows
        )
    except (OSError, ValueError, TypeError, KeyError) as exc:
        failure_state = (
            StageStatus.INTERRUPTED
            if state is StageStatus.INTERRUPTED or running.process.returncode in {130, -2}
            else StageStatus.TIMED_OUT
            if running.process.returncode == 124
            else state or (StageStatus.BLOCKED if custody_error is not None else StageStatus.FAILED)
        )
        diagnostic = f"{custody_error}; {exc}" if custody_error is not None else str(exc)
        return runtime_failure(running.spec, failure_state, diagnostic, running.process.returncode, rows)
    finally:
        running.output.close()


def execute_frozen_specs(
    specs: tuple[ProjectExecutionSpec, ...],
    *,
    workers: int,
    deadline: float,
) -> tuple[dict[str, list[PipelineStageResult]], dict[str, RunResult]]:
    """Schedule fresh workers; queue, startup, children, locks and cleanup share one deadline."""
    if type(deadline) not in {int, float} or not math.isfinite(deadline):
        raise ValueError("Multi-project supervising deadline must be finite")
    if type(workers) is not int or workers < 1:
        raise ValueError("multi-project workers must be a positive integer")
    from infrastructure.core.pipeline.runtime_namespace import validate_shared_runtime

    for spec in specs:
        validate_shared_runtime(spec.config, spec.plan)
    rows: dict[str, list[PipelineStageResult]] = {}
    runs: dict[str, RunResult] = {}
    active: dict[int, _Running] = {}
    pending = list(enumerate(specs))
    stopped: StageStatus | None = None
    with tempfile.TemporaryDirectory(prefix="template-multi-project-") as scratch:
        scratch_root = Path(scratch).resolve(strict=True)
        try:
            while active or pending:
                if time.monotonic() >= deadline:
                    stopped = StageStatus.TIMED_OUT
                    break
                while pending and len(active) < workers:
                    index, spec = pending[0]
                    try:
                        active[index] = _launch(spec, scratch_root / str(index), deadline)
                        pending.pop(0)
                    except TimeoutError:
                        stopped = StageStatus.TIMED_OUT
                        break
                    except GuardianCustodyError as exc:
                        pending.pop(0)
                        rows[spec.plan.project], runs[spec.plan.project] = runtime_failure(
                            spec, StageStatus.BLOCKED, str(exc)
                        )
                    except (OSError, ValueError, RuntimeError) as exc:
                        pending.pop(0)
                        rows[spec.plan.project], runs[spec.plan.project] = runtime_failure(
                            spec, StageStatus.FAILED, str(exc)
                        )
                if stopped is not None:
                    break
                completed = [
                    index
                    for index, task in active.items()
                    if task.process.poll() is not None or task.output.overflow.is_set() or task.output.error
                ]
                for index in completed:
                    task = active[index]
                    rows[task.spec.plan.project], runs[task.spec.plan.project] = _finish(task, deadline)
                    del active[index]
                    if runs[task.spec.plan.project].exit_code == 130:
                        stopped = StageStatus.INTERRUPTED
                        break
                if stopped is not None:
                    break
                if active:
                    time.sleep(min(0.025, max(0, deadline - time.monotonic())))
        except KeyboardInterrupt:
            stopped = StageStatus.INTERRUPTED
        finally:
            for task in active.values():
                rows[task.spec.plan.project], runs[task.spec.plan.project] = _finish(
                    task, deadline, stopped or StageStatus.FAILED
                )
            for _, spec in pending:
                rows[spec.plan.project], runs[spec.plan.project] = runtime_failure(
                    spec, stopped or StageStatus.FAILED, "Worker not launched before whole-run stop"
                )
    return (
        {spec.plan.project: rows[spec.plan.project] for spec in specs},
        {spec.plan.project: runs[spec.plan.project] for spec in specs},
    )
