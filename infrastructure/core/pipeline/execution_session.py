"""Whole-run deadline and lock composition for every resolved-plan executor."""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from infrastructure.core.files.project_lock import project_output_lock
from infrastructure.core.pipeline.execution_custody import execution_guard_result
from infrastructure.core.pipeline.execution_records import write_execution_record
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.report_finalization import finalize_execution_reports
from infrastructure.core.pipeline.types import PipelineStageResult

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
    executor.execution_plan = plan
    executor._plan_digest = plan.digest
    executor.config.total_stages = len(plan.stages)
    executor._artifact_manifest_boundary_keys = frozenset(
        stage.key for stage in plan.stages if stage.validation_boundary
    )
    executor._artifact_manifest_boundary_names = frozenset(
        stage.name for stage in plan.stages if stage.validation_boundary
    )
    executor.checkpoint_manager.expected_plan_digest = plan.digest
    executor.checkpoint_manager.expected_source_digest = plan.source_identity
    executor.checkpoint_manager.run_id = executor.run_id
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
            results = finalize_execution_reports(executor, results)
            return write_execution_record(executor, results)
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


__all__ = ["compose_run_deadline", "execute_resolved_plan"]
