"""Pipeline execution system for research projects.

This module provides pipeline execution functionality for research projects,
extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import logging
import time
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

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.checkpoint_manager = CheckpointManager(
            project_name=config.project_name, repo_root=config.repo_root
        )

        # Define log file path (will be created by _setup_log_file_handler)
        log_dir = config.project_dir / "output" / "logs"
        log_file = log_dir / "pipeline.log"
        self.log_file = log_file  # Store for later access
        self._log_handler: logging.FileHandler | None = None  # Track our file handler

        # Set up log file handler initially
        # NOTE: This will be called again after clean stage to recreate the log file
        self._setup_log_file_handler()

        # Unified telemetry collector (lazy: loads config from pipeline.yaml)
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

    def _init_telemetry(self) -> None:
        """Initialize the telemetry collector from pipeline YAML config."""
        from infrastructure.core.pipeline.dag import load_telemetry_config

        project_yaml = self.config.project_dir / "pipeline.yaml"
        default_yaml = (
            self.config.repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
        )
        yaml_path = project_yaml if project_yaml.exists() else default_yaml

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
        project_yaml = self.config.project_dir / "pipeline.yaml"
        default_yaml = (
            self.config.repo_root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml"
        )

        yaml_path = None
        if project_yaml.exists():
            yaml_path = project_yaml
            logger.info(f"Using project-specific pipeline: {yaml_path}")
        elif default_yaml.exists():
            yaml_path = default_yaml
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

        # Hardcoded fallback when no pipeline.yaml is available (e.g. tests)
        logger.debug("No pipeline.yaml found — using hardcoded stage list")
        stages: list[StageSpec] = []
        if not skip_clean:
            stages.append(StageSpec("Clean Output Directories", self._run_clean_outputs))
        stages.append(StageSpec("Environment Setup", self._run_setup_environment))
        if not self.config.skip_infra:
            stages.append(StageSpec("Infrastructure Tests", self.run_infrastructure_tests))
        stages.append(StageSpec("Project Tests", self.run_project_tests))
        stages.append(StageSpec("Project Analysis", self._run_analysis))
        stages.append(StageSpec("PDF Rendering", self._run_pdf_rendering))
        stages.append(StageSpec("Output Validation", self._run_validation))
        if include_llm and not self.config.skip_llm:
            stages.append(StageSpec("LLM Scientific Review", self._run_llm_review))
            stages.append(StageSpec("LLM Translations", self._run_llm_translations))
        stages.append(StageSpec("Copy Outputs", self._run_copy_outputs))
        return stages

    # -- Pipeline execution --------------------------------------------------

    def execute_full_pipeline(self) -> list[PipelineStageResult]:
        """Execute complete pipeline (tests -> analysis -> PDF -> validate -> copy -> LLM).

        Returns:
            List of stage results
        """
        logger.info(f"Executing full pipeline for project '{self.config.project_name}'")

        if self.config.resume:
            return self._resume_pipeline()

        skip_clean = not self.config.clean
        return self._execute_pipeline(
            self._build_stage_list(include_llm=True, skip_clean=skip_clean)
        )

    def execute_core_pipeline(self) -> list[PipelineStageResult]:
        """Execute core pipeline (tests -> analysis -> PDF -> validate -> copy).

        Returns:
            List of stage results
        """
        logger.info(f"Executing core pipeline for project '{self.config.project_name}'")

        if self.config.resume:
            return self._resume_pipeline()

        skip_clean = not self.config.clean
        return self._execute_pipeline(
            self._build_stage_list(include_llm=False, skip_clean=skip_clean)
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

        # Finalize telemetry report
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

        # Telemetry: start tracking
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

