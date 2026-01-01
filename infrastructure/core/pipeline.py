"""Pipeline execution system for research projects.

This module provides pipeline execution functionality for research projects,
extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from infrastructure.core.logging_utils import get_logger, log_operation, log_stage_with_eta
from infrastructure.core.checkpoint import CheckpointManager, StageResult
from infrastructure.core.environment import get_python_command, get_subprocess_env

logger = get_logger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution."""
    project_name: str
    repo_root: Path
    clean: bool = True
    skip_infra: bool = False
    skip_llm: bool = False
    resume: bool = False
    total_stages: int = 9


@dataclass
class PipelineStageResult:
    """Result from a pipeline stage execution."""
    stage_num: int
    stage_name: str
    success: bool
    duration: float
    exit_code: int = 0
    error_message: str = ""


class PipelineExecutor:
    """Execute research project pipeline stages."""

    def __init__(self, config: PipelineConfig):
        """Initialize pipeline executor.

        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.checkpoint_manager = CheckpointManager(project_name=config.project_name)

    def execute_full_pipeline(self) -> list[PipelineStageResult]:
        """Execute complete pipeline (tests → analysis → PDF → validate → copy → LLM).

        Returns:
            List of stage results
        """
        logger.info(f"Executing full pipeline for project '{self.config.project_name}'")

        if self.config.resume:
            return self._resume_pipeline()

        stages: list[tuple] = []
        # Stage 0 (conceptually): clean output dirs unless resuming or disabled
        stages.append(("Clean Output Directories", self._run_clean_outputs, (not self.config.clean) or self.config.resume))
        stages.append(("Environment Setup", self._run_setup_environment))
        stages.append(("Infrastructure Tests", self._run_infrastructure_tests, self.config.skip_infra))
        stages.append(("Project Tests", self._run_project_tests))
        stages.append(("Project Analysis", self._run_analysis))
        stages.append(("PDF Rendering", self._run_pdf_rendering))
        stages.append(("Output Validation", self._run_validation))
        stages.append(("LLM Scientific Review", self._run_llm_review, self.config.skip_llm))
        stages.append(("LLM Translations", self._run_llm_translations, self.config.skip_llm))
        stages.append(("Copy Outputs", self._run_copy_outputs))
        return self._execute_pipeline(stages)

    def execute_core_pipeline(self) -> list[PipelineStageResult]:
        """Execute core pipeline (tests → analysis → PDF → validate → copy).

        Returns:
            List of stage results
        """
        logger.info(f"Executing core pipeline for project '{self.config.project_name}'")

        if self.config.resume:
            return self._resume_pipeline()

        stages: list[tuple] = []
        stages.append(("Clean Output Directories", self._run_clean_outputs, (not self.config.clean) or self.config.resume))
        stages.append(("Environment Setup", self._run_setup_environment))
        stages.append(("Infrastructure Tests", self._run_infrastructure_tests, self.config.skip_infra))
        stages.append(("Project Tests", self._run_project_tests))
        stages.append(("Project Analysis", self._run_analysis))
        stages.append(("PDF Rendering", self._run_pdf_rendering))
        stages.append(("Output Validation", self._run_validation))
        stages.append(("Copy Outputs", self._run_copy_outputs))
        return self._execute_pipeline(stages)

    def _execute_pipeline(self, stages: list) -> list[PipelineStageResult]:
        """Execute pipeline stages.

        Args:
            stages: List of (stage_name, function, skip_condition) tuples

        Returns:
            List of stage results
        """
        results: list[PipelineStageResult] = []
        pipeline_start = time.time()

        executed_stage_num = 0  # sequential over executed (non-skipped) stages only
        for stage_spec in stages:
            stage_name = stage_spec[0]
            stage_func = stage_spec[1]
            skip_condition = stage_spec[2] if len(stage_spec) > 2 else False

            if skip_condition:
                logger.info(f"Skipping stage: {stage_name}")
                continue

            executed_stage_num += 1
            result = self._execute_stage(executed_stage_num, stage_name, stage_func, pipeline_start)
            results.append(result)

            if not result.success:
                logger.error(f"Pipeline failed at stage {executed_stage_num}: {stage_name}")
                break

            # Save checkpoint after successful executed stage
            self._save_checkpoint(pipeline_start, executed_stage_num, results)

        return results

    def _execute_stage(
        self,
        stage_num: int,
        stage_name: str,
        stage_func: Callable[[], bool],
        pipeline_start: Optional[float] = None
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
            log_stage_with_eta(stage_num, self.config.total_stages, stage_name, pipeline_start, logger)
        else:
            logger.info(f"Stage {stage_num}: {stage_name}")

        try:
            with log_operation(f"Stage {stage_num}: {stage_name}"):
                success = stage_func()

            duration = time.time() - start_time

            if success:
                logger.info(f"✓ Stage {stage_num} completed successfully ({duration:.1f}s)")
                return PipelineStageResult(
                    stage_num=stage_num,
                    stage_name=stage_name,
                    success=True,
                    duration=duration
                )
            else:
                logger.error(f"✗ Stage {stage_num} failed")
                return PipelineStageResult(
                    stage_num=stage_num,
                    stage_name=stage_name,
                    success=False,
                    duration=duration,
                    exit_code=1
                )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"✗ Stage {stage_num} failed with exception: {e}")
            return PipelineStageResult(
                stage_num=stage_num,
                stage_name=stage_name,
                success=False,
                duration=duration,
                exit_code=1,
                error_message=str(e)
            )

    def _resume_pipeline(self) -> list[PipelineStageResult]:
        """Resume pipeline from checkpoint.

        Returns:
            List of stage results from resumed execution
        """
        logger.info("Resuming pipeline from checkpoint")

        is_valid, error_message = self.checkpoint_manager.validate_checkpoint()
        if not is_valid:
            logger.warning(f"Checkpoint invalid, starting fresh: {error_message}")
            # Fall back to fresh run (but force resume off to avoid recursion)
            original_resume = self.config.resume
            self.config.resume = False
            try:
                return self.execute_full_pipeline() if not self.config.skip_llm else self.execute_core_pipeline()
            finally:
                self.config.resume = original_resume

        checkpoint = self.checkpoint_manager.load_checkpoint()
        if checkpoint is None:
            logger.warning("No checkpoint found, starting fresh")
            original_resume = self.config.resume
            self.config.resume = False
            try:
                return self.execute_full_pipeline() if not self.config.skip_llm else self.execute_core_pipeline()
            finally:
                self.config.resume = original_resume

        # Rebuild stage list based on configured pipeline type
        stages: list[tuple] = []
        stages.append(("Clean Output Directories", self._run_clean_outputs, True))  # never re-run on resume
        stages.append(("Environment Setup", self._run_setup_environment))
        stages.append(("Infrastructure Tests", self._run_infrastructure_tests, self.config.skip_infra))
        stages.append(("Project Tests", self._run_project_tests))
        stages.append(("Project Analysis", self._run_analysis))
        stages.append(("PDF Rendering", self._run_pdf_rendering))
        stages.append(("Output Validation", self._run_validation))
        if not self.config.skip_llm:
            stages.append(("LLM Scientific Review", self._run_llm_review))
            stages.append(("LLM Translations", self._run_llm_translations))
        stages.append(("Copy Outputs", self._run_copy_outputs))

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

        # Identify remaining stages by matching stage names against checkpoint stage_results in-order
        completed_names = [sr.name for sr in checkpoint.stage_results]
        completed_idx = 0
        remaining: list[tuple] = []
        for stage_spec in stages:
            stage_name = stage_spec[0]
            skip_condition = stage_spec[2] if len(stage_spec) > 2 else False
            if skip_condition:
                continue

            if completed_idx < len(completed_names) and stage_name == completed_names[completed_idx]:
                completed_idx += 1
                continue

            remaining.append(stage_spec)

        if completed_idx != len(completed_names):
            logger.warning(
                "Checkpoint stages did not match configured pipeline stages; starting fresh to avoid inconsistency"
            )
            original_resume = self.config.resume
            self.config.resume = False
            try:
                return self.execute_full_pipeline() if not self.config.skip_llm else self.execute_core_pipeline()
            finally:
                self.config.resume = original_resume

        logger.info(f"Resuming from stage {len(resumed_results) + 1} ({len(remaining)} stage(s) remaining)")

        # Execute remaining stages, continuing checkpoint numbering from prior completed count
        pipeline_start = checkpoint.pipeline_start_time
        executed_stage_num = len(resumed_results)
        for stage_spec in remaining:
            stage_name = stage_spec[0]
            stage_func = stage_spec[1]
            skip_condition = stage_spec[2] if len(stage_spec) > 2 else False
            if skip_condition:
                continue

            executed_stage_num += 1
            result = self._execute_stage(executed_stage_num, stage_name, stage_func, pipeline_start)
            # Handle exit code 2 (skip) as success for LLM stages
            if hasattr(result, 'exit_code') and result.exit_code == 2:
                # Exit code 2 means "skipped successfully" (e.g., no LLM languages configured)
                result = PipelineStageResult(
                    stage_num=result.stage_num,
                    stage_name=result.stage_name,
                    success=True,  # Treat skip as success
                    duration=result.duration,
                    exit_code=2  # Preserve original exit code for reporting
                )
            resumed_results.append(result)
            if not result.success:
                logger.error(f"Pipeline failed at stage {executed_stage_num}: {stage_name}")
                break
            self._save_checkpoint(pipeline_start, executed_stage_num, resumed_results)

        return resumed_results

    def _save_checkpoint(
        self,
        pipeline_start: float,
        last_stage: int,
        results: list[PipelineStageResult]
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
                completed=r.success
            )
            for r in results
        ]

        self.checkpoint_manager.save_checkpoint(
            pipeline_start_time=pipeline_start,
            last_stage_completed=last_stage,
            stage_results=checkpoint_results,
            total_stages=self.config.total_stages
        )

    # Stage execution methods - these will call the actual scripts/commands
    # For now, these are placeholders that will be implemented to call
    # the existing bash functions or Python equivalents

    def _run_clean_outputs(self) -> bool:
        """Clean output directories for a fresh run."""
        from infrastructure.core.file_operations import clean_output_directories

        logger.info("Cleaning output directories...")
        clean_output_directories(self.config.repo_root, self.config.project_name)
        return True

    def _run_setup_environment(self) -> bool:
        """Run environment setup."""
        logger.info("Running environment setup...")
        return self._run_script("00_setup_environment.py", "--project", self.config.project_name)

    def _run_infrastructure_tests(self) -> bool:
        """Run infrastructure tests."""
        logger.info("Running infrastructure tests...")
        # Provide a project name for report output location; infra tests themselves should not depend on project src.
        return self._run_script("01_run_tests.py", "--infra-only", "--project", self.config.project_name)

    def _run_project_tests(self) -> bool:
        """Run project tests."""
        logger.info("Running project tests...")
        return self._run_script("01_run_tests.py", "--project-only", "--project", self.config.project_name)

    def _run_analysis(self) -> bool:
        """Run project analysis."""
        logger.info("Running project analysis...")
        return self._run_script("02_run_analysis.py", "--project", self.config.project_name)

    def _run_pdf_rendering(self) -> bool:
        """Run PDF rendering."""
        logger.info("Running PDF rendering...")
        return self._run_script("03_render_pdf.py", "--project", self.config.project_name)

    def _run_validation(self) -> bool:
        """Run output validation."""
        logger.info("Running output validation...")
        return self._run_script("04_validate_output.py", "--project", self.config.project_name)

    def _run_llm_review(self) -> bool:
        """Run LLM scientific review."""
        logger.info("Running LLM scientific review...")
        return self._run_script("06_llm_review.py", "--reviews-only", "--project", self.config.project_name)

    def _run_llm_translations(self) -> bool:
        """Run LLM translations."""
        logger.info("Running LLM translations...")
        return self._run_script("06_llm_review.py", "--translations-only", "--project", self.config.project_name)

    def _run_copy_outputs(self) -> bool:
        """Run output copying."""
        logger.info("Running output copying...")
        return self._run_script("05_copy_outputs.py", "--project", self.config.project_name)

    def _run_script(self, script_name: str, *args: str) -> bool:
        """Run a script with given arguments.

        Args:
            script_name: Name of script in scripts/ directory
            *args: Arguments to pass to script

        Returns:
            True if script succeeded, False otherwise
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
        project_src = self.config.repo_root / "projects" / self.config.project_name / "src"
        pythonpath_parts = [str(self.config.repo_root), str(self.config.repo_root / "infrastructure")]
        if project_src.exists():
            pythonpath_parts.append(str(project_src))
        existing = env.get("PYTHONPATH")
        if existing:
            pythonpath_parts.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

        try:
            # Stream subprocess output to console for long-running stages; still capture exit code.
            result = subprocess.run(cmd, cwd=self.config.repo_root, env=env, check=False)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to run script {script_name}: {e}")
            return False