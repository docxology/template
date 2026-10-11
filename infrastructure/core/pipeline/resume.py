"""Pipeline checkpoint and resume logic.

Handles saving pipeline state after each stage and resuming from the last
successful checkpoint. Separated from executor.py for single-responsibility:
this module handles *persistence and recovery*, while executor.py handles
*orchestration*.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from infrastructure.core.runtime.checkpoint import StageResult
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.outcomes import StageOutcome, StageStatus
from infrastructure.core.pipeline.hitl import HitlController
from infrastructure.core.pipeline.artifact_contracts import capture_inputs
from infrastructure.core.pipeline.types import (
    PipelineConfig,
    PipelineControlConfig,
    PipelineStageResult,
    StageSpec,
)

if TYPE_CHECKING:
    from infrastructure.core.runtime.checkpoint import CheckpointManager
    from infrastructure.core.pipeline.plan import ExecutionPlan

logger = get_logger(__name__)


def _checkpoint_exit_code(result: PipelineStageResult) -> int:
    """Store successful-prefix status separately from a later human pause."""
    if result.hitl_pause and result.outcome is not None:
        if result.outcome.in_process_completed:
            return 0
        if result.outcome.child_exit_code is not None:
            return result.outcome.child_exit_code
    return result.exit_code


class PipelineResumeMixin(ABC):
    """Mixin providing checkpoint save/load and pipeline resume capability.

    Host class contract — the following attributes MUST be provided by the host
    class (e.g. ``PipelineExecutor``) before any mixin method is called:

    - ``config``: a :class:`PipelineConfig` instance with project settings.
      Sub-attributes accessed: ``clean``, ``mode``, ``total_stages``.
    - ``checkpoint_manager``: a :class:`CheckpointManager` instance managing
      the checkpoint file for the active project.

    These are declared as class-level annotations (not assigned) so that the
    type checker can see them without ``PipelineResumeMixin`` constructing them.
    """

    # Host-class contract — declared as annotations so the type system sees them.
    config: PipelineConfig
    checkpoint_manager: "CheckpointManager"
    control_config: PipelineControlConfig
    _plan_digest: str
    run_id: str
    execution_plan: ExecutionPlan | None

    @abstractmethod
    def _build_stage_list(self, skip_clean: bool) -> list[StageSpec]:
        """Build ordered stage list (implemented by host class)."""

    @abstractmethod
    def _execute_pipeline(self, stages: list[StageSpec]) -> list[PipelineStageResult]:
        """Execute all stages (implemented by host class)."""

    @abstractmethod
    def _run_stage_and_checkpoint(
        self,
        stage_num: int,
        stage_spec: StageSpec,
        results: list[PipelineStageResult],
        pipeline_start: float,
    ) -> PipelineStageResult:
        """Run one stage and save checkpoint (implemented by host class)."""

    def _resume_pipeline(self, stages: list[StageSpec] | None = None) -> list[PipelineStageResult]:
        """Resume pipeline from checkpoint.

        Returns:
            List of stage results from resumed execution
        """
        logger.info("Resuming pipeline from checkpoint")
        if stages is None:
            stages = self._build_stage_list(skip_clean=not self.config.clean)

        from infrastructure.core.pipeline.fingerprints import tool_reuse_refusal
        from infrastructure.core.runtime.python_binding import ANALYSIS_REUSE_REFUSAL, is_analysis_capability

        refusal = tool_reuse_refusal(self.config.repo_root, self.config.project_dir)
        if refusal is not None:
            diagnostic = f"Resume refused: {refusal}; preserve the checkpoint and rerun without --resume"
            return [
                PipelineStageResult(
                    0,
                    "Resume",
                    False,
                    0.0,
                    75,
                    diagnostic,
                    stage_completed=False,
                    stage_key="resume",
                    outcome=StageOutcome("resume", StageStatus.BLOCKED, None, diagnostic),
                )
            ]

        checkpoint, error_message = self.checkpoint_manager.load_validated_checkpoint()
        if checkpoint is None:
            diagnostic = f"Resume refused: {error_message}. Preserve the checkpoint; rerun without --resume."
            logger.warning(diagnostic)
            return [
                PipelineStageResult(
                    0,
                    "Resume",
                    False,
                    0.0,
                    75,
                    diagnostic,
                    stage_completed=False,
                    stage_key="resume",
                    outcome=StageOutcome("resume", StageStatus.BLOCKED, None, diagnostic),
                )
            ]

        expected_prefix = tuple(spec.key for spec in stages[: len(checkpoint.stage_results)])
        recorded_prefix = tuple(stored.context.get("stage_key") for stored in checkpoint.stage_results)
        if checkpoint.total_stages != len(stages) or recorded_prefix != expected_prefix:
            diagnostic = "Checkpoint stage identities differ from the exact current plan prefix; resume refused"
            return [
                PipelineStageResult(
                    0,
                    "Resume",
                    False,
                    0.0,
                    75,
                    diagnostic,
                    stage_completed=False,
                    stage_key="resume",
                    outcome=StageOutcome("resume", StageStatus.BLOCKED, None, diagnostic),
                )
            ]
        requested = self.execution_plan.stages if self.execution_plan is not None else ()
        completed_keys = {
            str(stored.context.get("stage_key", "")) for stored in checkpoint.stage_results if stored.completed
        }
        if any(
            stage.key in completed_keys and is_analysis_capability(stage.key, stage.script, stage.method)
            for stage in requested
        ) or any(key in completed_keys and is_analysis_capability(key) for key in expected_prefix):
            diagnostic = f"Resume refused: {ANALYSIS_REUSE_REFUSAL}; preserve the checkpoint and rerun without --resume"
            return [
                PipelineStageResult(
                    0,
                    "Resume",
                    False,
                    0.0,
                    75,
                    diagnostic,
                    stage_completed=False,
                    stage_key="resume",
                    outcome=StageOutcome("resume", StageStatus.BLOCKED, None, diagnostic),
                )
            ]
        try:
            for spec, stored in zip(stages, checkpoint.stage_results, strict=False):
                digest = stored.context.get("input_digest")
                if (
                    not isinstance(digest, str)
                    or len(digest) != 64
                    or capture_inputs(self.config, spec.contract).digest != digest
                ):
                    raise ValueError("Consumed input identity changed or is absent from the checkpoint")
        except (ValueError, OSError) as exc:
            diagnostic = f"Resume refused: {exc}; preserve the checkpoint and start a fresh run"
            return [
                PipelineStageResult(
                    0,
                    "Resume",
                    False,
                    0.0,
                    75,
                    diagnostic,
                    stage_completed=False,
                    stage_key="resume",
                    outcome=StageOutcome("resume", StageStatus.BLOCKED, None, diagnostic),
                )
            ]
        if checkpoint.run_id:
            self.run_id = checkpoint.run_id
            self.checkpoint_manager.run_id = checkpoint.run_id
        if checkpoint.stage_results and checkpoint.stage_results[-1].context.get("hitl_pause"):
            paused_spec = stages[len(checkpoint.stage_results) - 1]
            controller = HitlController(
                project_output_dir=self.config.runtime_output_dir,
                control=self.control_config,
                run_id=self.run_id,
                plan_digest=self._plan_digest,
                repo_root=self.config.repo_root,
            )
            decision = controller.decision_for_stage(paused_spec)
            if decision not in {"approve", "resume"}:
                state = (
                    StageStatus.REJECTED
                    if decision == "reject"
                    else StageStatus.ABORTED
                    if decision == "abort"
                    else StageStatus.PAUSED
                )
                diagnostic = (
                    "Human decision required for completed stage"
                    if decision is None
                    else f"Bound human decision: {decision}"
                )
                return [
                    PipelineStageResult(
                        len(checkpoint.stage_results),
                        paused_spec.name,
                        False,
                        0.0,
                        75 if state == StageStatus.PAUSED else 1,
                        diagnostic,
                        stage_completed=True,
                        stage_key=paused_spec.key or paused_spec.name,
                        outcome=StageOutcome(
                            paused_spec.key or paused_spec.name,
                            state,
                            child_exit_code=checkpoint.stage_results[-1].context.get("child_exit_code"),
                            diagnostic=diagnostic,
                        ),
                    )
                ]

        # Rebuild stage list based on configured pipeline type (clean always skipped on resume)
        self._current_stage_count = len(stages)

        # Convert prior results into PipelineStageResult objects for reporting continuity
        resumed_results: list[PipelineStageResult] = []
        for i, sr in enumerate(checkpoint.stage_results, 1):
            stage_key = str(sr.context.get("stage_key", ""))
            original_skip = sr.status == "skipped"
            reusable = self.execution_plan is not None and any(
                stage.key == stage_key and stage.cacheable for stage in self.execution_plan.stages
            )
            status = StageStatus.SKIPPED if original_skip else StageStatus.CACHED if reusable else StageStatus.SUCCEEDED
            resumed_results.append(
                PipelineStageResult(
                    stage_num=i,
                    stage_name=sr.name,
                    success=sr.completed,
                    duration=sr.duration,
                    exit_code=sr.exit_code,
                    stage_key=stage_key,
                    input_digest=str(sr.context.get("input_digest", "")),
                    output_digest=str(sr.context.get("output_digest", "")),
                    outcome=StageOutcome(
                        stage_key,
                        status,
                        child_exit_code=sr.context.get("child_exit_code", sr.exit_code),
                        diagnostic=str(sr.context.get("error_message", "")),
                        attempt_count=sr.context.get("attempt_count", 1),
                        attempt_exit_codes=tuple(sr.context.get("attempt_exit_codes", ())),
                        reason=str(sr.context.get("reason", "")) if original_skip else "validated_checkpoint",
                        receipt_validated=True,
                        in_process_completed=sr.context.get("in_process_completed", False),
                    ),
                )
            )

        # Identify remaining stages by matching stage names against checkpoint stage_results in-order.
        # Sequential pointer (not set) because order must be preserved: a stage is only "done" if
        # it was the NEXT expected stage in sequence, preventing false-matches on duplicate names.
        completed_names = [sr.context.get("stage_key") for sr in checkpoint.stage_results]
        completed_idx = 0
        remaining: list[StageSpec] = []
        for stage_spec in stages:
            if completed_idx < len(completed_names) and stage_spec.key == completed_names[completed_idx]:
                completed_idx += 1
                continue

            remaining.append(stage_spec)

        if completed_idx != len(completed_names):
            diagnostic = "Checkpoint stage identities differ from current plan; resume refused"
            return [
                PipelineStageResult(
                    0,
                    "Resume",
                    False,
                    0.0,
                    75,
                    diagnostic,
                    stage_completed=False,
                    stage_key="resume",
                    outcome=StageOutcome("resume", StageStatus.BLOCKED, None, diagnostic),
                )
            ]

        logger.info(f"Resuming from stage {len(resumed_results) + 1} ({len(remaining)} stage(s) remaining)")

        # Execute remaining stages, continuing checkpoint numbering from prior completed count
        pipeline_start = checkpoint.pipeline_start_time
        executed_stage_num = len(resumed_results)
        for stage_spec in remaining:
            executed_stage_num += 1
            result = self._run_stage_and_checkpoint(executed_stage_num, stage_spec, resumed_results, pipeline_start)
            if not result.success or result.hitl_pause:
                break

        finalize = getattr(self, "_finalize_pipeline_run", None)
        if callable(finalize):
            finalize(pipeline_start, resumed_results)
        else:
            lesson_writer = getattr(self, "_write_run_lessons_report", None)
            if callable(lesson_writer):
                lesson_writer(resumed_results)

        return resumed_results

    def _save_checkpoint(self, pipeline_start: float, last_stage: int, results: list[PipelineStageResult]) -> None:
        """Save pipeline checkpoint.

        Args:
            pipeline_start: Pipeline start time
            last_stage: Last completed stage number
            results: Stage results so far
        """
        # Convert to checkpoint format
        checkpoint_results = [
            StageResult(
                name=r.stage_name,
                exit_code=_checkpoint_exit_code(r),
                duration=r.duration,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                completed=(r.success or r.hitl_pause) and r.stage_completed,
                status=(
                    "skipped"
                    if r.outcome is not None and r.outcome.child_exit_code == 2 and r.outcome.receipt_validated
                    else "succeeded"
                )
                if r.hitl_pause and r.stage_completed
                else r.outcome.status.value
                if r.outcome is not None
                else ("succeeded" if r.success else "failed"),
                context={
                    "stage_num": r.stage_num,
                    "stage_key": r.stage_key,
                    "receipt_validated": r.outcome.receipt_validated if r.outcome is not None else False,
                    "reason": r.outcome.reason if r.outcome is not None else "",
                    "attempt_count": r.outcome.attempt_count if r.outcome is not None else 1,
                    "attempt_exit_codes": list(r.outcome.attempt_exit_codes) if r.outcome is not None else [],
                    "in_process_completed": r.outcome.in_process_completed if r.outcome is not None else False,
                    "input_digest": r.input_digest,
                    "output_digest": r.output_digest,
                    "child_exit_code": r.outcome.child_exit_code if r.outcome is not None else None,
                    "stage_name": r.stage_name,
                    "success": r.success,
                    "exit_code": r.exit_code,
                    "hitl_pause": r.hitl_pause,
                    "stage_completed": r.stage_completed,
                    "lessons": list(r.lessons),
                    "error_message": r.error_message,
                    "exception_type": r.exception_type,
                },
            )
            for r in results
        ]

        self.checkpoint_manager.save_checkpoint(
            pipeline_start_time=pipeline_start,
            last_stage_completed=last_stage,
            stage_results=checkpoint_results,
            total_stages=getattr(self, "_current_stage_count", None) or self.config.total_stages,
        )
