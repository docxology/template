"""Pipeline execution system for research projects.

This module provides pipeline execution functionality for research projects,
extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Callable

from infrastructure.core.runtime.checkpoint import CheckpointManager, StageResult
from infrastructure.core.runtime.environment import get_python_command, get_subprocess_env
from infrastructure.core.logging.utils import (
    flush_file_handlers,
    get_logger,
    log_pipeline_stage_with_eta,
    setup_logger,
    setup_root_log_file_handler,
)
from infrastructure.core.errors import (
    PIPELINE_STAGE_FAILED,
    SCRIPT_EXECUTION_FAILED,
    STAGE_EXCEPTION,
    STAGE_FAILED,
)
from infrastructure.core.files.cleanup import clean_output_directories
from infrastructure.core.pipeline.types import (
    PipelineConfig,
    PipelineStageResult,
    StageSpec,
)
from infrastructure.core.telemetry import TelemetryCollector, TelemetryConfig

logger = get_logger(__name__)



class PipelineExecutor:
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

    def execute_full_pipeline(self) -> list[PipelineStageResult]:
        """Execute complete pipeline (tests → analysis → PDF → validate → copy → LLM).

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
        """Execute core pipeline (tests → analysis → PDF → validate → copy).

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

    def _run_clean_outputs(self) -> bool:
        """Clean output directories for a fresh run.

        After cleaning, recreates the log file handler since clean_output_directories
        may have deleted the log file.

        Returns:
            True if cleaning succeeded, False on error.
        """
        logger.info("Cleaning output directories...")
        try:
            clean_output_directories(self.config.repo_root, self.config.project_name)
        except Exception as e:
            logger.error(f"Failed to clean output directories: {e}")
            return False

        # Recreate log file handler after clean deleted the log directory
        # This ensures logs for subsequent stages are captured
        self._setup_log_file_handler()
        logger.info(f"Recreated pipeline log file: {self.log_file}")
        return True

    def _run_setup_environment(self) -> bool:
        return self._run_script("00_setup_environment.py", "--project", self.config.project_name)

    def run_infrastructure_tests(self) -> bool:
        """Public API used by multi-project orchestrator."""
        # Provide a project name for report output location; infra tests themselves should not depend on project src.  # noqa: E501
        return self._run_script(
            "01_run_tests.py", "--infra-only", "--verbose", "--project", self.config.project_name
        )

    def run_project_tests(self) -> bool:
        return self._run_script(
            "01_run_tests.py", "--project-only", "--verbose", "--project", self.config.project_name
        )

    def _run_analysis(self) -> bool:
        return self._run_script("02_run_analysis.py", "--project", self.config.project_name)

    def _run_pdf_rendering(self) -> bool:
        return self._run_script("03_render_pdf.py", "--project", self.config.project_name)

    def _run_validation(self) -> bool:
        return self._run_script("04_validate_output.py", "--project", self.config.project_name)

    def _run_llm_review(self) -> bool:
        """Run LLM scientific review.

        Uses allow_skip_code=True to treat exit code 2 (Ollama not available) as success.
        """
        return self._run_script(
            "06_llm_review.py",
            "--reviews-only",
            "--project",
            self.config.project_name,
            allow_skip_code=True,
        )

    def _run_llm_translations(self) -> bool:
        """Run LLM translations.

        Uses allow_skip_code=True to treat exit code 2 (no languages configured or Ollama unavailable) as success.
        """
        return self._run_script(
            "06_llm_review.py",
            "--translations-only",
            "--project",
            self.config.project_name,
            allow_skip_code=True,
        )

    def _run_copy_outputs(self) -> bool:
        """Run output copying."""
        logger.info("Running output copying...")

        # Flush log handlers before copying to ensure log file is written
        flush_file_handlers()
        if not self._verify_log_file():
            logger.warning("Log file not verified before copy - may be missing or empty")

        return self._run_script("05_copy_outputs.py", "--project", self.config.project_name)

    def _verify_log_file(self) -> bool:
        """Check that the log file exists and has content.

        Returns:
            True if log file exists and has content, False otherwise
        """
        if self.log_file.exists():
            try:
                size = self.log_file.stat().st_size
                if size > 0:
                    logger.debug(f"Log file verified: {self.log_file} ({size:,} bytes)")
                    return True
                else:
                    logger.warning(f"Log file exists but is empty: {self.log_file}")
                    return False
            except OSError as e:
                logger.warning(f"Failed to verify log file: {e}")
                return False
        else:
            logger.warning(f"Log file not found: {self.log_file}")
            return False

    def _run_script(self, script_name: str, *args: str, allow_skip_code: bool = False) -> bool:
        """Run a script with given arguments.

        Args:
            script_name: Name of script in scripts/ directory
            *args: Arguments to pass to script
            allow_skip_code: If True, treat exit code 2 as success (graceful skip)

        Returns:
            True if script succeeded (or skipped gracefully if allow_skip_code=True), False otherwise
        """
        script_path = self.config.repo_root / "scripts" / script_name

        cmd = get_python_command() + [str(script_path)] + list(args)
        logger.debug(f"Running: {' '.join(cmd)}")

        # Get clean environment dict with uv compatibility (handles VIRTUAL_ENV warnings)
        env = get_subprocess_env()
        env.setdefault("MPLBACKEND", "Agg")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PROJECT_ROOT", str(self.config.repo_root))

        # Ensure project src is on PYTHONPATH for stage scripts that import project code.
        project_src = self.config.project_dir / "src"
        pythonpath_parts = [
            str(self.config.repo_root),
            str(self.config.repo_root / "infrastructure"),
        ]
        if project_src.exists():
            pythonpath_parts.append(str(project_src))
        existing = env.get("PYTHONPATH")
        if existing:
            pythonpath_parts.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

        try:
            # Stream subprocess output to console for long-running stages; still capture exit code.
            result = subprocess.run(
                cmd, cwd=self.config.repo_root, env=env, check=False, timeout=7200
            )

            # Exit code 0 = success
            if result.returncode == 0:
                return True

            # Exit code 2 = graceful skip (e.g., Ollama not available)
            if allow_skip_code and result.returncode == 2:
                logger.info(f"Stage skipped gracefully (exit code 2): {script_name}")
                return True

            return False
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            logger.error(SCRIPT_EXECUTION_FAILED.format(script_name=script_name, error=e))
            return False
