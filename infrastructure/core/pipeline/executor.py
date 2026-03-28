"""Pipeline execution system for research projects.

This module provides pipeline execution functionality for research projects,
extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Callable

from infrastructure.core.runtime.checkpoint import CheckpointManager
from infrastructure.core.logging.utils import (
    get_logger,
    log_pipeline_stage_with_eta,
    setup_logger,
    setup_root_log_file_handler,
)
from infrastructure.core.errors import (
    PIPELINE_STAGE_FAILED,
    STAGE_EXCEPTION,
    STAGE_FAILED,
)
from infrastructure.core.pipeline.resume import PipelineResumeMixin
from infrastructure.core.pipeline.stages import PipelineStageMixin
from infrastructure.core.pipeline.types import (
    PipelineConfig,
    PipelineStageResult,
    StageSpec,
)
from infrastructure.core.telemetry import TelemetryCollector, TelemetryConfig

logger = get_logger(__name__)



class PipelineExecutor(PipelineStageMixin, PipelineResumeMixin):
    """Execute research project pipeline stages."""

    def __init__(self, config: PipelineConfig):
        """Initialize pipeline executor.

        Sets up per-project log file that captures all pipeline execution logs
        (Python + subprocess output). Log file is located at:
        projects/{project_name}/output/logs/pipeline.log

        Note: construction performs lightweight file I/O — it creates the log directory
        (``mkdir -p``), opens the log file handler, and reads ``pipeline.yaml`` to
        configure telemetry reporters.  These operations are intentional: the executor
        cannot function without its log file, and the YAML load is a simple path probe
        (existence check + YAML parse) on a small config file.  They are not deferred
        because there is no meaningful "lazy" moment for a log handler — it must be
        ready before the first stage runs.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.checkpoint_manager = CheckpointManager(
            project_name=config.project_name, repo_root=config.repo_root
        )

        # Log file: projects/{project_name}/output/logs/pipeline.log
        # Recreated by _setup_log_file_handler after clean stage deletes it.
        self.log_file = config.project_dir / "output" / "logs" / "pipeline.log"
        self._log_handler: logging.FileHandler | None = None
        self._setup_log_file_handler()

        # Telemetry collector (lazy: reads pipeline.yaml for enabled reporters)
        self._telemetry: TelemetryCollector | None = None
        self._init_telemetry()

    def _setup_log_file_handler(self) -> None:
        """Set up or recreate the log file handler.

        Called during init and after the clean stage (which may delete the log file).
        Delegates root-logger file handler management to logging_utils.
        """
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        setup_logger(__name__, log_file=self.log_file)

        if self._log_handler is not None:
            try:
                self._log_handler.close()
            except OSError as e:
                logger.debug(f"Failed to close log handler: {e}")

        self._log_handler = setup_root_log_file_handler(self.log_file)
        logger.debug(f"Set up log file handler: {self.log_file}")

    def _resolve_pipeline_yaml(self) -> Path:
        """Return the pipeline YAML path to use: project-specific if it exists, else default."""
        project_yaml = self.config.project_dir / "pipeline.yaml"
        default_yaml = (
            self.config.repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
        )
        return project_yaml if project_yaml.exists() else default_yaml

    def _init_telemetry(self) -> None:
        """Initialize the telemetry collector from pipeline YAML config."""
        from infrastructure.core.pipeline.dag import load_telemetry_config

        yaml_path = self._resolve_pipeline_yaml()

        telem_config = TelemetryConfig()  # defaults
        if yaml_path.exists():
            loaded = load_telemetry_config(yaml_path)
            if loaded is not None:
                telem_config = loaded

        output_dir = self.config.project_dir / "output"
        self._telemetry = TelemetryCollector(
            config=telem_config,
            project_name=self.config.project_name,
            output_dir=output_dir,
        )
        self._telemetry.capture_system_info()

    # -- Stage list construction ---------------------------------------------

    def _build_stage_list(self, include_llm: bool, skip_clean: bool) -> list[StageSpec]:
        """Build canonical stage list by loading the declarative pipeline DAG.

        Resolution order:
        1. ``projects/{name}/pipeline.yaml`` (project-specific override)
        2. ``infrastructure/core/pipeline/pipeline.yaml`` (default definition)
        3. Hardcoded fallback (for tests or missing config)

        Tag-based filtering applies ``skip_clean``, ``skip_infra``, and ``skip_llm``
        flags without modifying the YAML source.
        """
        from infrastructure.core.pipeline.dag import PipelineDAG

        # Resolve YAML path: project-specific → default → fallback
        resolved = self._resolve_pipeline_yaml()
        yaml_path: Path | None = None
        if resolved.exists():
            yaml_path = resolved
            if resolved == self.config.project_dir / "pipeline.yaml":
                logger.info(f"Using project-specific pipeline: {yaml_path}")
            else:
                logger.debug(f"Using default pipeline: {yaml_path}")

        if yaml_path is not None:
            dag = PipelineDAG.from_yaml(yaml_path)

            # Apply flag-based filtering via tags
            exclude_tags: set[str] = set()
            if not include_llm or self.config.skip_llm:
                exclude_tags.add("llm")
            if skip_clean:
                dag.remove_stage("Clean Output Directories")
            if self.config.skip_infra:
                dag.remove_stage("Infrastructure Tests")

            if exclude_tags:
                dag.filter_tags(exclude=exclude_tags)

            return dag.to_stage_specs(self)

        # Hardcoded fallback when no pipeline.yaml is available (e.g. tests).
        # Applies the same skip_clean/skip_infra/skip_llm flags as the YAML path above.
        logger.debug("No pipeline.yaml found — using hardcoded stage list")
        skip_llm = not include_llm or self.config.skip_llm
        all_stages: list[StageSpec] = [
            StageSpec("Clean Output Directories", self._run_clean_outputs),
            StageSpec("Environment Setup", self._run_setup_environment),
            StageSpec("Infrastructure Tests", self.run_infrastructure_tests),
            StageSpec("Project Tests", self.run_project_tests),
            StageSpec("Project Analysis", self._run_analysis),
            StageSpec("PDF Rendering", self._run_pdf_rendering),
            StageSpec("Output Validation", self._run_validation),
            StageSpec("LLM Scientific Review", self._run_llm_review),
            StageSpec("LLM Translations", self._run_llm_translations),
            StageSpec("Copy Outputs", self._run_copy_outputs),
        ]
        skip_names: set[str] = set()
        if skip_clean:
            skip_names.add("Clean Output Directories")
        if self.config.skip_infra:
            skip_names.add("Infrastructure Tests")
        if skip_llm:
            skip_names.update({"LLM Scientific Review", "LLM Translations"})
        return [s for s in all_stages if s.name not in skip_names]

    # -- Pipeline execution --------------------------------------------------

    def execute_full_pipeline(self) -> list[PipelineStageResult]:
        """Execute complete pipeline (tests -> analysis -> PDF -> validate -> copy -> LLM)."""
        logger.info(f"Executing full pipeline for project '{self.config.project_name}'")
        return self._run_pipeline(include_llm=True)

    def execute_core_pipeline(self) -> list[PipelineStageResult]:
        """Execute core pipeline (tests -> analysis -> PDF -> validate -> copy)."""
        logger.info(f"Executing core pipeline for project '{self.config.project_name}'")
        return self._run_pipeline(include_llm=False)

    def _run_pipeline(self, include_llm: bool) -> list[PipelineStageResult]:
        """Shared implementation for execute_full_pipeline and execute_core_pipeline."""
        if self.config.resume:
            return self._resume_pipeline()
        skip_clean = not self.config.clean
        return self._execute_pipeline(
            self._build_stage_list(include_llm=include_llm, skip_clean=skip_clean)
        )

    def _run_stage_and_checkpoint(
        self,
        stage_num: int,
        stage_spec: StageSpec,
        results: list[PipelineStageResult],
        pipeline_start: float,
    ) -> PipelineStageResult:
        """Execute a stage, append to results, and checkpoint on success."""
        result = self._execute_stage(stage_num, stage_spec.name, stage_spec.func, pipeline_start)
        results.append(result)
        if not result.success:
            logger.error(
                PIPELINE_STAGE_FAILED.format(stage_num=stage_num, stage_name=stage_spec.name)
            )
        else:
            self._save_checkpoint(pipeline_start, stage_num, results)
        return result

    def _execute_pipeline(self, stages: list[StageSpec]) -> list[PipelineStageResult]:
        """Execute pipeline stages."""
        results: list[PipelineStageResult] = []
        pipeline_start = time.time()

        for stage_num, stage_spec in enumerate(stages, 1):
            result = self._run_stage_and_checkpoint(stage_num, stage_spec, results, pipeline_start)
            if not result.success:
                break

        if self._telemetry is not None:
            total_duration = time.time() - pipeline_start
            self._telemetry.finalize(total_duration=total_duration)

        return results

    def _execute_stage(
        self,
        stage_num: int,
        stage_name: str,
        stage_func: Callable[[], bool],
        pipeline_start: float | None = None,
    ) -> PipelineStageResult:
        """Execute single pipeline stage with timing and error handling.

        Args:
            stage_num: Stage number
            stage_name: Stage name
            stage_func: Function to execute
            pipeline_start: Pipeline start time for ETA calculation (optional)

        Returns:
            Stage result
        """
        start_time = time.time()

        # Use enhanced stage logging with ETA if pipeline start time available
        if pipeline_start is not None:
            log_pipeline_stage_with_eta(
                stage_num, self.config.total_stages, stage_name, pipeline_start, logger
            )
        else:
            logger.info(f"Stage {stage_num}: {stage_name}")

        if self._telemetry is not None:
            self._telemetry.start_stage(stage_name, stage_num)

        try:
            success = stage_func()

            duration = time.time() - start_time

            if success:
                logger.info(f"✓ Stage {stage_num} completed successfully ({duration:.1f}s)")
                if self._telemetry is not None:
                    self._telemetry.end_stage(stage_name, stage_num, success=True)
                return PipelineStageResult(
                    stage_num=stage_num,
                    stage_name=stage_name,
                    success=True,
                    duration=duration,
                )
            else:
                logger.error(STAGE_FAILED.format(stage_num=stage_num))
                if self._telemetry is not None:
                    self._telemetry.end_stage(stage_name, stage_num, success=False, exit_code=1)
                return PipelineStageResult(
                    stage_num=stage_num,
                    stage_name=stage_name,
                    success=False,
                    duration=duration,
                    exit_code=1,
                )

        except Exception as e:  # noqa: BLE001 — intentional: stage executor isolates all failures into PipelineStageResult
            duration = time.time() - start_time
            logger.error(STAGE_EXCEPTION.format(stage_num=stage_num, error=e))
            if self._telemetry is not None:
                self._telemetry.end_stage(
                    stage_name, stage_num, success=False, exit_code=1, error_message=str(e)
                )
            return PipelineStageResult(
                stage_num=stage_num,
                stage_name=stage_name,
                success=False,
                duration=duration,
                exit_code=1,
                error_message=str(e),
                exception_type=type(e).__name__,
            )

