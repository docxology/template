"""Pipeline checkpoint and resume logic.

Handles saving pipeline state after each stage and resuming from the last
successful checkpoint. Separated from executor.py for single-responsibility:
this module handles *persistence and recovery*, while executor.py handles
*orchestration*.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import time

from infrastructure.core.runtime.checkpoint import StageResult
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.types import (
    PipelineStageResult,
    StageSpec,
)

logger = get_logger(__name__)


class PipelineResumeMixin:
    """Mixin providing checkpoint save/load and pipeline resume capability.

    Expects the host class to provide:
        - self.config: PipelineConfig (with skip_llm, clean, total_stages)
        - self.checkpoint_manager: CheckpointManager
        - self._build_stage_list(include_llm, skip_clean): method
        - self._execute_pipeline(stages): method
        - self._run_stage_and_checkpoint(stage_num, stage_spec, results, pipeline_start): method
    """

    def _start_fresh(self) -> list[PipelineStageResult]:
        """Run the pipeline from scratch, bypassing any checkpoint."""
        skip_clean = not self.config.clean
        stages = self._build_stage_list(include_llm=not self.config.skip_llm, skip_clean=skip_clean)
        return self._execute_pipeline(stages)

    def _resume_pipeline(self) -> list[PipelineStageResult]:
        """Resume pipeline from checkpoint.

        Returns:
            List of stage results from resumed execution
        """
        logger.info("Resuming pipeline from checkpoint")

        is_valid, error_message = self.checkpoint_manager.validate_checkpoint()
        if not is_valid:
            logger.warning(f"Checkpoint invalid, starting fresh: {error_message}")
            return self._start_fresh()

        checkpoint = self.checkpoint_manager.load_checkpoint()
        if checkpoint is None:
            logger.warning("No checkpoint found, starting fresh")
            return self._start_fresh()

        # Rebuild stage list based on configured pipeline type (clean always skipped on resume)
        stages = self._build_stage_list(include_llm=not self.config.skip_llm, skip_clean=True)

        # Convert prior results into PipelineStageResult objects for reporting continuity
        resumed_results: list[PipelineStageResult] = []
        for i, sr in enumerate(checkpoint.stage_results, 1):
            resumed_results.append(
                PipelineStageResult(
                    stage_num=i,
                    stage_name=sr.name,
                    success=(sr.exit_code == 0 and sr.completed),
                    duration=sr.duration,
                    exit_code=sr.exit_code,
                )
            )

        # Identify remaining stages by matching stage names against checkpoint stage_results in-order.
        # Sequential pointer (not set) because order must be preserved: a stage is only "done" if
        # it was the NEXT expected stage in sequence, preventing false-matches on duplicate names.
        completed_names = [sr.name for sr in checkpoint.stage_results]
        completed_idx = 0
        remaining: list[StageSpec] = []
        for stage_spec in stages:
            stage_name = stage_spec.name
            if (
                completed_idx < len(completed_names)
                and stage_name == completed_names[completed_idx]
            ):
                completed_idx += 1
                continue

            remaining.append(stage_spec)

        if completed_idx != len(completed_names):
            logger.warning(
                "Checkpoint stages did not match configured pipeline stages; starting fresh to avoid inconsistency"  # noqa: E501
            )
            return self._start_fresh()

        logger.info(
            f"Resuming from stage {len(resumed_results) + 1} ({len(remaining)} stage(s) remaining)"
        )

        # Execute remaining stages, continuing checkpoint numbering from prior completed count
        pipeline_start = checkpoint.pipeline_start_time
        executed_stage_num = len(resumed_results)
        for stage_spec in remaining:
            executed_stage_num += 1
            result = self._run_stage_and_checkpoint(
                executed_stage_num, stage_spec, resumed_results, pipeline_start
            )
            if not result.success:
                break

        return resumed_results

    def _save_checkpoint(
        self, pipeline_start: float, last_stage: int, results: list[PipelineStageResult]
    ) -> None:
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
                exit_code=r.exit_code,
                duration=r.duration,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                completed=r.success,
            )
            for r in results
        ]

        self.checkpoint_manager.save_checkpoint(
            pipeline_start_time=pipeline_start,
            last_stage_completed=last_stage,
            stage_results=checkpoint_results,
            total_stages=self.config.total_stages,
        )
