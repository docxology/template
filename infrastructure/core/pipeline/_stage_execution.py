"""Extracted pipeline stage execution steps for :class:`PipelineExecutor`."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from infrastructure.core.logging.utils import get_logger, log_pipeline_stage_with_eta
from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.pipeline.hooks import (
    HookEvent,
    StageHookContext,
    any_hook_failed,
    run_stage_hooks,
    summarize_hook_failures,
)
from infrastructure.core.pipeline.types import PipelineStageResult, StageSpec

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
        success=True,
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
    run_dir,
    stage_hooks,
    start_time: float,
) -> PipelineStageResult | None:
    """Run pre stage hooks."""
    pre_context = StageHookContext(
        project_name=executor.config.project_name,
        stage_name=stage_name,
        stage_num=stage_num,
        run_dir=run_dir,
        status="running",
    )
    pre_hook_results = run_stage_hooks(stage_hooks, HookEvent.PRE_STAGE, pre_context)
    if not any_hook_failed(pre_hook_results):
        return None
    duration = time.time() - start_time
    error_message = summarize_hook_failures(pre_hook_results)
    record_stage_telemetry(
        executor,
        stage_name=stage_name,
        stage_num=stage_num,
        success=False,
        exit_code=1,
        error_message=error_message,
    )
    return PipelineStageResult(
        stage_num=stage_num,
        stage_name=stage_name,
        success=False,
        duration=duration,
        exit_code=1,
        error_message=error_message,
    )


def invoke_stage_function(stage_func: Callable[[], bool], *, retry_policy: int) -> bool:
    """Process invoke stage function."""
    attempts = max(1, retry_policy + 1)
    for attempt in range(1, attempts + 1):
        try:
            success = stage_func()
        except Exception:
            if attempt < attempts:
                logger.warning(
                    "Stage raised an exception; retrying (%d/%d)",
                    attempt,
                    retry_policy,
                )
                continue
            raise
        if success:
            return True
        if attempt < attempts:
            logger.warning(
                "Stage returned failure; retrying (%d/%d)",
                attempt,
                retry_policy,
            )
    return False


def record_stage_telemetry(
    executor: PipelineExecutor,
    *,
    stage_name: str,
    stage_num: int,
    success: bool,
    exit_code: int = 0,
    error_message: str = "",
) -> None:
    """Process record stage telemetry."""
    if executor._telemetry is None:
        return
    executor._telemetry.end_stage(
        stage_name,
        stage_num,
        success=success,
        exit_code=exit_code,
        error_message=error_message,
    )


def log_stage_start(
    executor: PipelineExecutor,
    *,
    stage_num: int,
    stage_name: str,
    pipeline_start: float | None,
) -> None:
    """Process log stage start."""
    if pipeline_start is not None:
        log_pipeline_stage_with_eta(
            stage_num,
            executor.config.total_stages,
            stage_name,
            pipeline_start,
            logger,
        )
    else:
        logger.info(f"Stage {stage_num}: {stage_name}")


def handle_post_stage_success(
    executor: PipelineExecutor,
    *,
    stage_num: int,
    stage_name: str,
    duration: float,
    run_dir,
    stage_hooks,
    stage_spec: StageSpec | None,
    hitl_controller: HitlController,
    stage_contract,
) -> PipelineStageResult:
    """Process handle post stage success."""
    logger.info(f"✓ Stage {stage_num} completed successfully ({duration:.1f}s)")
    post_context = StageHookContext(
        project_name=executor.config.project_name,
        stage_name=stage_name,
        stage_num=stage_num,
        run_dir=run_dir,
        status="success",
    )
    post_hook_results = run_stage_hooks(stage_hooks, HookEvent.POST_STAGE, post_context)
    if any_hook_failed(post_hook_results):
        error_message = summarize_hook_failures(post_hook_results)
        record_stage_telemetry(
            executor,
            stage_name=stage_name,
            stage_num=stage_num,
            success=False,
            exit_code=1,
            error_message=error_message,
        )
        return PipelineStageResult(
            stage_num=stage_num,
            stage_name=stage_name,
            success=False,
            duration=duration,
            exit_code=1,
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
        )
        pause_hook_results = run_stage_hooks(stage_hooks, HookEvent.ON_PAUSE, pause_context)
        if any_hook_failed(pause_hook_results):
            error_message = summarize_hook_failures(pause_hook_results)
            record_stage_telemetry(
                executor,
                stage_name=stage_name,
                stage_num=stage_num,
                success=False,
                exit_code=1,
                error_message=error_message,
            )
            return PipelineStageResult(
                stage_num=stage_num,
                stage_name=stage_name,
                success=False,
                duration=duration,
                exit_code=1,
                error_message=error_message,
            )
        hitl_pause = True
        lessons = (f"HITL pause requested: {reason}",)
    elif stage_spec is not None and executor.control_config.smart_pause_action == "pause":
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
    run_dir,
    stage_hooks,
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
    )
    fail_hook_results = run_stage_hooks(stage_hooks, HookEvent.ON_FAIL, fail_context)
    error_message = summarize_hook_failures(fail_hook_results)
    record_stage_telemetry(
        executor,
        stage_name=stage_name,
        stage_num=stage_num,
        success=False,
        exit_code=1,
        error_message=error_message,
    )
    return PipelineStageResult(
        stage_num=stage_num,
        stage_name=stage_name,
        success=False,
        duration=duration,
        exit_code=1,
        error_message=error_message,
    )


def handle_stage_exception(
    executor: PipelineExecutor,
    *,
    stage_num: int,
    stage_name: str,
    duration: float,
    run_dir,
    stage_hooks,
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
    )
    fail_hook_results = run_stage_hooks(stage_hooks, HookEvent.ON_FAIL, fail_context)
    hook_error = summarize_hook_failures(fail_hook_results)
    error_message = "; ".join(part for part in (str(exc), hook_error) if part)
    record_stage_telemetry(
        executor,
        stage_name=stage_name,
        stage_num=stage_num,
        success=False,
        exit_code=1,
        error_message=error_message,
    )
    return PipelineStageResult(
        stage_num=stage_num,
        stage_name=stage_name,
        success=False,
        duration=duration,
        exit_code=1,
        error_message=error_message,
        exception_type=type(exc).__name__,
    )


def execute_stage(
    executor: PipelineExecutor,
    stage_num: int,
    stage_name: str,
    stage_func: Callable[[], bool],
    pipeline_start: float | None = None,
    *,
    stage_spec: StageSpec | None = None,
) -> PipelineStageResult:
    """Execute a single pipeline stage with hooks, HITL, and telemetry."""
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
    stage_contract = effective_stage_spec.contract
    stage_hooks = effective_stage_spec.hooks
    run_dir = executor.config.project_dir / "output"
    run_dir.mkdir(parents=True, exist_ok=True)
    hitl_controller = HitlController(
        project_output_dir=run_dir,
        control=executor.control_config,
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

    try:
        success = invoke_stage_function(stage_func, retry_policy=stage_contract.retry_policy)
        duration = time.time() - start_time
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
