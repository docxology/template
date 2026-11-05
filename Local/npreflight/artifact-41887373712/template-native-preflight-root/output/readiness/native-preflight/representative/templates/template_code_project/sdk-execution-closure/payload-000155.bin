"""Extracted pipeline stage execution steps for :class:`PipelineExecutor`."""

from __future__ import annotations

import time
from dataclasses import replace
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.pipeline.observability import record_stage_telemetry, log_stage_start
from infrastructure.core.pipeline.hooks import (
    HookEvent,
    StageHookContext,
    any_hook_failed,
    hook_failure_exit_code,
    run_stage_hooks,
    summarize_hook_failures,
)
from infrastructure.core.pipeline.types import (
    PipelineStageResult,
    StageContract,
    StageHooks,
    StageSpec,
    PipelineControlConfig,
)
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus, attach_stage_outcome
from infrastructure.core.pipeline.artifact_contracts import (
    InputContractError,
    InputSnapshot,
    capture_inputs,
    contract_failure,
)
from infrastructure.core.pipeline.stage_admission import original_stage_admission, validate_stage_admission

if TYPE_CHECKING:
    from infrastructure.core.pipeline.executor import PipelineExecutor

logger = get_logger(__name__)


def maybe_hitl_pause_before_stage(
    executor: PipelineExecutor,
    *,
    stage_num: int,
    stage_name: str,
    stage_spec: StageSpec,
    hitl_controller: HitlController,
    start_time: float,
) -> PipelineStageResult | None:
    """Process maybe hitl pause before stage."""
    if not hitl_controller.should_pause_before(stage_num, stage_spec):
        return None
    reason = hitl_controller.pause_reason(
        stage_num=stage_num,
        stage_spec=stage_spec,
        default="checkpoint",
    )
    hitl_controller.pause(
        stage_num=stage_num,
        stage_name=stage_name,
        reason=reason,
        context_summary=stage_spec.contract.definition_of_done,
        stage_spec=stage_spec,
    )
    duration = time.time() - start_time
    if executor._telemetry is not None:
        executor._telemetry.end_stage(stage_name, stage_num, success=True)
    return PipelineStageResult(
        stage_num=stage_num,
        stage_name=stage_name,
        success=False,
        duration=duration,
        hitl_pause=True,
        stage_completed=False,
        lessons=(f"HITL pause before stage: {reason}",),
    )


def run_pre_stage_hooks(
    executor: PipelineExecutor,
    *,
    stage_num: int,
    stage_name: str,
    run_dir: Path,
    stage_hooks: StageHooks,
    start_time: float,
) -> PipelineStageResult | None:
    """Run pre stage hooks."""
    pre_context = StageHookContext(
        project_name=executor.config.project_name,
        stage_name=stage_name,
        stage_num=stage_num,
        run_dir=run_dir,
        status="running",
        deadline_monotonic=getattr(executor, "_stage_deadline", None),
    )
    pre_hook_results = run_stage_hooks(stage_hooks, HookEvent.PRE_STAGE, pre_context)
    if not any_hook_failed(pre_hook_results):
        return None
    duration = time.time() - start_time
    error_message = summarize_hook_failures(pre_hook_results)
    exit_code = hook_failure_exit_code(pre_hook_results)
    record_stage_telemetry(
        executor,
        stage_name=stage_name,
        stage_num=stage_num,
        success=False,
        exit_code=exit_code,
        error_message=error_message,
    )
    return PipelineStageResult(
        stage_num=stage_num,
        stage_name=stage_name,
        success=False,
        duration=duration,
        exit_code=exit_code,
        error_message=error_message,
    )


def invoke_stage_function(
    stage_func: Callable[[], bool | StageOutcome],
    *,
    retry_policy: int,
    before_attempt: Callable[[], StageOutcome | None] | None = None,
) -> bool | StageOutcome:
    """Retry only a positively classified retryable stage outcome."""
    attempts = max(1, retry_policy + 1)
    codes: list[int] = []
    previous: StageOutcome | None = None
    for attempt in range(1, attempts + 1):
        guard = before_attempt() if before_attempt is not None else None
        if guard is not None:
            if previous is not None:
                dominant = (
                    guard
                    if guard.status is StageStatus.INTERRUPTED
                    else previous
                    if previous.status is StageStatus.INTERRUPTED
                    else guard
                    if guard.status is StageStatus.TIMED_OUT
                    else previous
                    if previous.status is StageStatus.TIMED_OUT
                    else previous
                    if previous.status in {StageStatus.FAILED, StageStatus.REJECTED, StageStatus.ABORTED}
                    else guard
                )
                guard = replace(
                    dominant,
                    diagnostic="; ".join(filter(None, (previous.diagnostic, guard.diagnostic))),
                    child_exit_code=previous.child_exit_code,
                    retryable=False,
                )
            return replace(guard, attempt_count=max(1, attempt - 1), attempt_exit_codes=tuple(codes))
        value = stage_func()
        if not isinstance(value, StageOutcome):
            if type(value) is not bool:
                raise TypeError("Stage executable must return bool or StageOutcome")
            return value
        if value.child_exit_code is not None:
            codes.append(value.child_exit_code)
        value = replace(value, attempt_count=attempt, attempt_exit_codes=tuple(codes))
        previous = value
        if value.complete or not value.retryable or attempt == attempts:
            return value
        logger.warning("Retrying classified stage failure (%d/%d)", attempt, retry_policy)
    return False


def handle_post_stage_success(
    executor: PipelineExecutor,
    *,
    stage_num: int,
    stage_name: str,
    duration: float,
    run_dir: Path,
    stage_hooks: StageHooks,
    stage_spec: StageSpec | None,
    hitl_controller: HitlController,
    stage_contract: StageContract,
) -> PipelineStageResult:
    """Process handle post stage success."""
    logger.info(f"✓ Stage {stage_num} completed successfully ({duration:.1f}s)")
    post_context = StageHookContext(
        project_name=executor.config.project_name,
        stage_name=stage_name,
        stage_num=stage_num,
        run_dir=run_dir,
        status="success",
        deadline_monotonic=getattr(executor, "_stage_deadline", None),
    )
    post_hook_results = run_stage_hooks(stage_hooks, HookEvent.POST_STAGE, post_context)
    if any_hook_failed(post_hook_results):
        error_message = summarize_hook_failures(post_hook_results)
        record_stage_telemetry(
            executor,
            stage_name=stage_name,
            stage_num=stage_num,
            success=False,
            exit_code=hook_failure_exit_code(post_hook_results),
            error_message=error_message,
        )
        return PipelineStageResult(
            stage_num=stage_num,
            stage_name=stage_name,
            success=False,
            duration=duration,
            exit_code=hook_failure_exit_code(post_hook_results),
            error_message=error_message,
        )

    hitl_pause = False
    lessons: tuple[str, ...] = ()
    if stage_spec is not None and hitl_controller.should_pause_after(stage_num, stage_spec):
        reason = hitl_controller.pause_reason(
            stage_num=stage_num,
            stage_spec=stage_spec,
            default="checkpoint",
        )
        hitl_controller.pause(
            stage_num=stage_num,
            stage_name=stage_name,
            reason=reason,
            context_summary=stage_contract.definition_of_done,
            stage_spec=stage_spec,
        )
        pause_context = StageHookContext(
            project_name=executor.config.project_name,
            stage_name=stage_name,
            stage_num=stage_num,
            run_dir=run_dir,
            status="paused",
            deadline_monotonic=getattr(executor, "_stage_deadline", None),
        )
        pause_hook_results = run_stage_hooks(stage_hooks, HookEvent.ON_PAUSE, pause_context)
        if any_hook_failed(pause_hook_results):
            error_message = summarize_hook_failures(pause_hook_results)
            exit_code = hook_failure_exit_code(pause_hook_results)
            record_stage_telemetry(
                executor,
                stage_name=stage_name,
                stage_num=stage_num,
                success=False,
                exit_code=exit_code,
                error_message=error_message,
            )
            return PipelineStageResult(
                stage_num=stage_num,
                stage_name=stage_name,
                success=False,
                duration=duration,
                exit_code=exit_code,
                error_message=error_message,
            )
        hitl_pause = True
        lessons = (f"HITL pause requested: {reason}",)
    elif (
        stage_spec is not None
        and (
            executor.execution_plan.smart_pause_action
            if executor.execution_plan
            else executor.control_config.smart_pause_action
        )
        == "pause"
    ):
        from infrastructure.core.pipeline.smart_pause import compute_pause_recommendations

        recommendations = compute_pause_recommendations(run_dir)
        if recommendations:
            reason = "smart_pause"
            hitl_controller.pause(
                stage_num=stage_num,
                stage_name=stage_name,
                reason=reason,
                context_summary=recommendations[0].evidence[0] if recommendations[0].evidence else "",
                stage_spec=stage_spec,
            )
            hitl_pause = True
            lessons = (f"SmartPause requested: {recommendations[0].reason_codes[0]}",)

    record_stage_telemetry(executor, stage_name=stage_name, stage_num=stage_num, success=True)
    return PipelineStageResult(
        stage_num=stage_num,
        stage_name=stage_name,
        success=True,
        duration=duration,
        hitl_pause=hitl_pause,
        lessons=lessons,
    )


def handle_stage_failure(
    executor: PipelineExecutor,
    *,
    stage_num: int,
    stage_name: str,
    duration: float,
    run_dir: Path,
    stage_hooks: StageHooks,
    error_detail: str = "stage returned false",
) -> PipelineStageResult:
    """Process handle stage failure."""
    from infrastructure.core.errors import STAGE_FAILED

    logger.error(STAGE_FAILED.format(stage_num=stage_num))
    fail_context = StageHookContext(
        project_name=executor.config.project_name,
        stage_name=stage_name,
        stage_num=stage_num,
        run_dir=run_dir,
        status="failed",
        error_message=error_detail,
        deadline_monotonic=getattr(executor, "_stage_deadline", None),
    )
    fail_hook_results = run_stage_hooks(stage_hooks, HookEvent.ON_FAIL, fail_context)
    error_message = "; ".join(part for part in (error_detail, summarize_hook_failures(fail_hook_results)) if part)
    exit_code = hook_failure_exit_code(fail_hook_results)
    record_stage_telemetry(
        executor,
        stage_name=stage_name,
        stage_num=stage_num,
        success=False,
        exit_code=exit_code,
        error_message=error_message,
    )
    return PipelineStageResult(
        stage_num=stage_num,
        stage_name=stage_name,
        success=False,
        duration=duration,
        exit_code=exit_code,
        error_message=error_message,
    )


def handle_stage_exception(
    executor: PipelineExecutor,
    *,
    stage_num: int,
    stage_name: str,
    duration: float,
    run_dir: Path,
    stage_hooks: StageHooks,
    exc: Exception,
) -> PipelineStageResult:
    """Process handle stage exception."""
    from infrastructure.core.errors import STAGE_EXCEPTION

    logger.error(STAGE_EXCEPTION.format(stage_num=stage_num, error=exc))
    fail_context = StageHookContext(
        project_name=executor.config.project_name,
        stage_name=stage_name,
        stage_num=stage_num,
        run_dir=run_dir,
        status="failed",
        error_message=str(exc),
        deadline_monotonic=getattr(executor, "_stage_deadline", None),
    )
    fail_hook_results = run_stage_hooks(stage_hooks, HookEvent.ON_FAIL, fail_context)
    hook_error = summarize_hook_failures(fail_hook_results)
    error_message = "; ".join(part for part in (str(exc), hook_error) if part)
    exit_code = hook_failure_exit_code(fail_hook_results)
    record_stage_telemetry(
        executor,
        stage_name=stage_name,
        stage_num=stage_num,
        success=False,
        exit_code=exit_code,
        error_message=error_message,
    )
    return PipelineStageResult(
        stage_num=stage_num,
        stage_name=stage_name,
        success=False,
        duration=duration,
        exit_code=exit_code,
        error_message=error_message,
        exception_type=type(exc).__name__,
    )


def execute_stage(
    executor: PipelineExecutor,
    stage_num: int,
    stage_name: str,
    stage_func: Callable[[], bool | StageOutcome],
    pipeline_start: float | None = None,
    *,
    stage_spec: StageSpec | None = None,
    input_snapshot: InputSnapshot | None = None,
) -> PipelineStageResult:
    """Execute a single stage and attach its stable typed outcome on every path."""
    key = (stage_spec.key if stage_spec else None) or stage_name
    executor._active_stage_key = key
    executor._last_child_outcome = None
    policy = (
        stage_spec.policy
        if stage_spec is not None and stage_spec.policy is not None
        else executor.control_config.stage_policies.get(stage_num)
    )
    stage_budget = policy.timeout_seconds if policy else executor.config.run_timeout_seconds
    executor._stage_deadline = min(
        time.monotonic() + stage_budget,
        executor._run_deadline or time.monotonic() + executor.config.run_timeout_seconds,
    )
    try:
        result = _execute_stage(
            executor,
            stage_num,
            stage_name,
            stage_func,
            pipeline_start,
            stage_spec=stage_spec,
            input_snapshot=input_snapshot,
        )
    except KeyboardInterrupt:
        result = PipelineStageResult(
            stage_num, stage_name, False, 0.0, 130, "Execution interrupted", stage_completed=False
        )
    except Exception as exc:  # noqa: BLE001 — runtime custody/launch refusals are executed failures
        result = PipelineStageResult(
            stage_num, stage_name, False, 0.0, 1, str(exc), stage_completed=False, exception_type=type(exc).__name__
        )
    finally:
        executor._active_stage_admission = None
    return attach_stage_outcome(result, executor._last_child_outcome, key)


def _execute_stage(
    executor: PipelineExecutor,
    stage_num: int,
    stage_name: str,
    stage_func: Callable[[], bool | StageOutcome],
    pipeline_start: float | None = None,
    *,
    stage_spec: StageSpec | None = None,
    input_snapshot: InputSnapshot | None = None,
) -> PipelineStageResult:
    """Run stage hooks, policy, and the selected executable target."""
    start_time = time.time()

    log_stage_start(
        executor,
        stage_num=stage_num,
        stage_name=stage_name,
        pipeline_start=pipeline_start,
    )

    if executor._telemetry is not None:
        executor._telemetry.start_stage(stage_name, stage_num)

    effective_stage_spec = stage_spec or StageSpec(stage_name, stage_func)
    try:
        snapshot = (
            input_snapshot
            if input_snapshot is not None
            else capture_inputs(executor.config, effective_stage_spec.contract)
        )
    except (OSError, ValueError) as exc:
        return contract_failure(stage_num, effective_stage_spec, InputContractError(str(exc)))
    stage_contract = effective_stage_spec.contract
    stage_hooks = effective_stage_spec.hooks
    run_dir = executor.config.runtime_output_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    control = (
        PipelineControlConfig(
            hitl_mode=executor.execution_plan.hitl_mode,
            smart_pause_action=executor.execution_plan.smart_pause_action,
            stage_policies={stage_num: effective_stage_spec.policy} if effective_stage_spec.policy is not None else {},
        )
        if executor.execution_plan
        else replace(
            executor.control_config,
            stage_policies={**executor.control_config.stage_policies, stage_num: effective_stage_spec.policy},
        )
        if effective_stage_spec.policy is not None
        else executor.control_config
    )
    hitl_controller = HitlController(
        project_output_dir=run_dir,
        control=control,
        run_id=executor.run_id,
        plan_digest=executor._plan_digest,
        repo_root=executor.config.repo_root,
        project_dir=executor.config.project_dir,
    )
    decision = hitl_controller.decision_for_stage(effective_stage_spec)
    if decision in {"reject", "abort"}:
        state = StageStatus.REJECTED if decision == "reject" else StageStatus.ABORTED
        return PipelineStageResult(
            stage_num,
            stage_name,
            False,
            0.0,
            1,
            f"Bound human decision: {decision}",
            stage_completed=False,
            stage_key=effective_stage_spec.key or stage_name,
            outcome=StageOutcome(effective_stage_spec.key or stage_name, state, 1, f"Bound human decision: {decision}"),
        )

    hitl_before = maybe_hitl_pause_before_stage(
        executor,
        stage_num=stage_num,
        stage_name=stage_name,
        stage_spec=effective_stage_spec,
        hitl_controller=hitl_controller,
        start_time=start_time,
    )
    if hitl_before is not None:
        return hitl_before

    # Approval is consumed once, but its original bytes remain authoritative
    # across hooks and every retry. Never recapture a hook's replacement input.
    admission = original_stage_admission(
        snapshot,
        effective_stage_spec,
        hitl_controller,
        shared_infrastructure=executor.config.shared_infrastructure,
    )
    executor._active_stage_admission = admission

    pre_failure = run_pre_stage_hooks(
        executor,
        stage_num=stage_num,
        stage_name=stage_name,
        run_dir=run_dir,
        stage_hooks=stage_hooks,
        start_time=start_time,
    )
    if pre_failure is not None:
        return pre_failure

    def admit_attempt() -> StageOutcome | None:
        from infrastructure.core.pipeline.execution_custody import execution_guard_result

        guard = execution_guard_result(
            config=executor.config,
            plan=executor.execution_plan,
            deadline=executor._stage_deadline,
            stage_num=stage_num,
            stage_name=stage_name,
            stage_key=executor._active_stage_key,
        )
        if guard is not None:
            return guard.outcome
        try:
            validate_stage_admission(
                admission,
                repo=executor.config.repo_root,
                project=executor.config.project_dir,
                run_id=executor.run_id,
                plan_digest=executor._plan_digest,
                stage_key=executor._active_stage_key,
            )
        except (OSError, ValueError) as exc:
            return StageOutcome(executor._active_stage_key, StageStatus.BLOCKED, None, str(exc))
        return None

    try:
        success = invoke_stage_function(
            stage_func, retry_policy=stage_contract.retry_policy, before_attempt=admit_attempt
        )
        if type(success) is bool:
            # The function really returned; no child process existed. Preserve
            # that observation through later hooks, gates and source guards.
            executor._last_child_outcome = StageOutcome(
                executor._active_stage_key,
                StageStatus.SUCCEEDED if success else StageStatus.FAILED,
                None,
                in_process_completed=success,
            )
        if isinstance(success, StageOutcome):
            if success.stage_key != executor._active_stage_key:
                raise ValueError("Stage executable returned an outcome for another stage")
            executor._last_child_outcome = success
        duration = time.time() - start_time
        if isinstance(success, StageOutcome) and success.status in {StageStatus.BLOCKED, StageStatus.TIMED_OUT}:
            return PipelineStageResult(
                stage_num,
                stage_name,
                False,
                duration,
                124 if success.status is StageStatus.TIMED_OUT else 75,
                success.diagnostic,
                stage_completed=False,
                stage_key=success.stage_key,
                outcome=success,
            )
        if success:
            return handle_post_stage_success(
                executor,
                stage_num=stage_num,
                stage_name=stage_name,
                duration=duration,
                run_dir=run_dir,
                stage_hooks=stage_hooks,
                stage_spec=stage_spec,
                hitl_controller=hitl_controller,
                stage_contract=stage_contract,
            )
        return handle_stage_failure(
            executor,
            stage_num=stage_num,
            stage_name=stage_name,
            duration=duration,
            run_dir=run_dir,
            stage_hooks=stage_hooks,
            error_detail=success.diagnostic if isinstance(success, StageOutcome) else "stage returned false",
        )
    except Exception as exc:  # noqa: BLE001 — stage executor isolates failures into PipelineStageResult
        duration = time.time() - start_time
        return handle_stage_exception(
            executor,
            stage_num=stage_num,
            stage_name=stage_name,
            duration=duration,
            run_dir=run_dir,
            stage_hooks=stage_hooks,
            exc=exc,
        )
