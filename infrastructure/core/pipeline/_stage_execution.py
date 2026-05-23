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
) -> PipelineStageResult | None:
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
    error_message = summarize_hook_failures(pre_hook_results)
    return PipelineStageResult(
        stage_num=stage_num,
        stage_name=stage_name,
        success=False,
        duration=0.0,
        exit_code=1,
        error_message=error_message,
    )


def invoke_stage_function(stage_func: Callable[[], bool], *, retry_policy: int) -> bool:
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
