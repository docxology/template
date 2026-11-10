"""Whole-run deadline and lock composition for every resolved-plan executor."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.pipeline.execution_custody import execution_guard_result
from infrastructure.core.pipeline.execution_records import write_execution_record
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.report_finalization import finalize_execution_reports
from infrastructure.core.pipeline.types import PipelineConfig, PipelineStageResult

if TYPE_CHECKING:
    from infrastructure.core.pipeline.executor import PipelineExecutor
    from infrastructure.core.pipeline.plan import ExecutionPlan


def compose_run_deadline(budget: float, supplied: float | None) -> float:
    """Clamp the worker deadline without changing the frozen plan or its digest."""
    deadline = time.monotonic() + budget
    if supplied is not None:
        if type(supplied) not in {int, float} or not math.isfinite(supplied):
            raise ValueError("Supervising run deadline must be finite")
        deadline = min(deadline, supplied)
    return deadline


@dataclass(frozen=True)
class PreparedPipelineRun:
    """Keep the immutable selected plan and original preflight deadline together."""

    plan: ExecutionPlan
    deadline: float

    def expired(self) -> bool:
        """Check the original deadline at the caller's preflight boundary."""
        return time.monotonic() >= self.deadline


def prepare_pipeline_run(
    config: PipelineConfig,
    *,
    deadline_monotonic: float | None = None,
    skip_clean: bool | None = None,
    target_stage: str | None = None,
) -> PreparedPipelineRun:
    """Resolve the selected plan before creating runtime or log resources."""
    from infrastructure.core.pipeline.plan import compile_execution_plan

    deadline = deadline_monotonic
    if deadline is None:
        deadline = compose_run_deadline(config.run_timeout_seconds, None)
    plan = compile_execution_plan(config, skip_clean=skip_clean, target_stage=target_stage)
    return PreparedPipelineRun(plan, deadline)


def execute_resolved_plan(
    executor: PipelineExecutor, plan: ExecutionPlan, *, deadline_monotonic: float | None = None
) -> list[PipelineStageResult]:
    """Keep lock waiting, child execution, resume and reporting within one deadline."""
    started = time.monotonic()
    if plan.project != executor.config.project_name or plan.mode != executor.config.mode:
        raise ValueError("Execution plan does not match the selected project and mode")
    # Public callers can construct dataclasses directly. Admit the exact frozen
    # contract and its targets without recomputing a planner or invoking a child.
    plan = plan.from_dict(plan.to_dict(), expected_digest=plan.digest)
    deadline = min(
        started + plan.run_timeout_seconds,
        compose_run_deadline(plan.run_timeout_seconds, deadline_monotonic),
    )
    from infrastructure.core.pipeline.runtime_namespace import validate_shared_runtime

    validate_shared_runtime(executor.config, plan)
    plan.admit_targets(executor.config.repo_root)
    executor._install_execution_plan(plan)
    executor._run_deadline = deadline
    stages = plan.bind(executor)
    guard = execution_guard_result(
        config=executor.config,
        plan=plan,
        deadline=deadline,
        stage_key=plan.expected_stage_keys[0] if plan.expected_stage_keys else "execution",
    )
    # A refused lock attempt must not overwrite the active holder's execution record.
    if guard is not None:
        return [guard]
    try:
        with project_output_lock(executor.config.project_dir, timeout=max(0.0, deadline - time.monotonic())):
            guard = execution_guard_result(
                config=executor.config,
                plan=plan,
                deadline=deadline,
                stage_key=plan.expected_stage_keys[0] if plan.expected_stage_keys else "execution",
            )
            if guard is not None:
                return write_execution_record(executor, [guard])
            results = (
                executor._resume_pipeline(stages) if executor.config.resume else executor._execute_pipeline(stages)
            )
            if executor.run_result(results).complete:
                guard = execution_guard_result(config=executor.config, plan=plan, deadline=deadline, completion=True)
                if guard is not None:
                    results.append(guard)
            results = write_execution_record(executor, results)
            reported_results = finalize_execution_reports(executor, results)
            if reported_results == results:
                # Successful reporting already verified the persisted record bytes.
                return reported_results
            return write_execution_record(executor, reported_results)
    except TimeoutError as exc:
        return [
            PipelineStageResult(
                0,
                "Project lock",
                False,
                0.0,
                124,
                str(exc),
                stage_completed=False,
                stage_key="project_lock",
                outcome=StageOutcome("project_lock", StageStatus.TIMED_OUT, None, str(exc)),
            )
        ]


__all__ = [
    "PreparedPipelineRun",
    "compose_run_deadline",
    "execute_resolved_plan",
    "prepare_pipeline_run",
]
