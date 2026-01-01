"""Multi-project orchestration system.

This module provides orchestration for running pipelines across multiple projects,
extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from infrastructure.core.logging_utils import get_logger, log_operation
from infrastructure.core.pipeline import PipelineConfig, PipelineExecutor, PipelineStageResult
from infrastructure.project.discovery import ProjectInfo

logger = get_logger(__name__)


@dataclass
class MultiProjectConfig:
    """Configuration for multi-project execution."""
    repo_root: Path
    projects: list[ProjectInfo]
    run_infra_tests: bool = True
    run_llm: bool = True
    run_executive_report: bool = True


@dataclass
class MultiProjectResult:
    """Result of multi-project execution."""
    project_results: Dict[str, List[PipelineStageResult]]
    infra_test_duration: float = 0.0
    total_duration: float = 0.0
    successful_projects: int = 0
    failed_projects: int = 0


class MultiProjectOrchestrator:
    """Orchestrate pipeline execution across multiple projects."""

    def __init__(self, config: MultiProjectConfig):
        """Initialize multi-project orchestrator.

        Args:
            config: Multi-project configuration
        """
        self.config = config

    def execute_all_projects_full(self) -> MultiProjectResult:
        """Execute full pipeline for all projects (with infrastructure tests, with LLM).

        Returns:
            Multi-project execution result
        """
        logger.info(f"Executing full pipeline for {len(self.config.projects)} projects")

        return self._execute_multi_project_pipeline(
            run_infra_tests=True,
            run_llm=True,
            pipeline_method="execute_full_pipeline"
        )

    def execute_all_projects_core(self) -> MultiProjectResult:
        """Execute core pipeline for all projects (with infrastructure tests, no LLM).

        Returns:
            Multi-project execution result
        """
        logger.info(f"Executing core pipeline for {len(self.config.projects)} projects")

        return self._execute_multi_project_pipeline(
            run_infra_tests=True,
            run_llm=False,
            pipeline_method="execute_core_pipeline"
        )

    def execute_all_projects_full_no_infra(self) -> MultiProjectResult:
        """Execute full pipeline for all projects (no infrastructure tests, with LLM).

        Returns:
            Multi-project execution result
        """
        logger.info(f"Executing full pipeline (no infra) for {len(self.config.projects)} projects")

        return self._execute_multi_project_pipeline(
            run_infra_tests=False,
            run_llm=True,
            pipeline_method="execute_full_pipeline"
        )

    def execute_all_projects_core_no_infra(self) -> MultiProjectResult:
        """Execute core pipeline for all projects (no infrastructure tests, no LLM).

        Returns:
            Multi-project execution result
        """
        logger.info(f"Executing core pipeline (no infra) for {len(self.config.projects)} projects")

        return self._execute_multi_project_pipeline(
            run_infra_tests=False,
            run_llm=False,
            pipeline_method="execute_core_pipeline"
        )

    def _execute_multi_project_pipeline(
        self,
        run_infra_tests: bool,
        run_llm: bool,
        pipeline_method: str
    ) -> MultiProjectResult:
        """Execute pipeline across multiple projects.

        Args:
            run_infra_tests: Whether to run infrastructure tests once at start
            run_llm: Whether to include LLM stages
            pipeline_method: Method name to call on PipelineExecutor

        Returns:
            Multi-project execution result
        """
        start_time = time.time()
        project_results = {}

        # Run infrastructure tests once at the beginning (if requested)
        infra_duration = 0.0
        if run_infra_tests:
            if not self._run_infrastructure_tests_once():
                logger.error("Infrastructure tests failed - aborting multi-project execution")
                return MultiProjectResult(
                    project_results={},
                    infra_test_duration=infra_duration,
                    total_duration=time.time() - start_time,
                    successful_projects=0,
                    failed_projects=len(self.config.projects)
                )
            infra_duration = time.time() - start_time
            logger.info(f"✅ Infrastructure tests completed in {infra_duration:.1f}s")
        else:
            logger.info("Skipping infrastructure tests (already run or disabled)")

        # Execute pipeline for each project
        successful_projects = 0
        failed_projects = 0

        for i, project in enumerate(self.config.projects, 1):
            project_name = project.name
            logger.info(f"Project {i}/{len(self.config.projects)}: {project_name}")

            try:
                with log_operation(f"Pipeline execution for {project_name}"):
                    # Create pipeline config
                    pipeline_config = PipelineConfig(
                        project_name=project_name,
                        repo_root=self.config.repo_root,
                        skip_infra=True,  # Always skip infra tests for individual projects in multi-project mode
                        skip_llm=not run_llm,
                        total_stages=9 if run_llm else 7
                    )

                    # Execute pipeline
                    executor = PipelineExecutor(pipeline_config)
                    method = getattr(executor, pipeline_method)
                    results = method()

                    project_results[project_name] = results

                    # Check if all stages succeeded
                    all_success = all(r.success for r in results)
                    if all_success:
                        successful_projects += 1
                        logger.info(f"✅ Project '{project_name}' completed successfully")
                    else:
                        failed_projects += 1
                        logger.error(f"❌ Project '{project_name}' failed")
                        # Continue with other projects even if one fails

            except Exception as e:
                failed_projects += 1
                logger.error(f"❌ Project '{project_name}' failed with exception: {e}")
                project_results[project_name] = []

        # Generate executive report if enabled and we have multiple projects
        if self.config.run_executive_report and len(self.config.projects) > 1:
            self._run_executive_reporting(project_results)

        total_duration = time.time() - start_time

        logger.info(f"Multi-project execution completed: {successful_projects} successful, {failed_projects} failed")

        return MultiProjectResult(
            project_results=project_results,
            infra_test_duration=infra_duration,
            total_duration=total_duration,
            successful_projects=successful_projects,
            failed_projects=failed_projects
        )

    def _run_infrastructure_tests_once(self) -> bool:
        """Run infrastructure tests once before all projects.

        Returns:
            True if infrastructure tests passed, False otherwise
        """
        logger.info("Running infrastructure tests once for all projects...")

        try:
            # Use an existing project name so reports can be written under projects/{name}/output/reports/
            # (the infrastructure test suite itself does not depend on project code).
            fallback_project = self.config.projects[0].name if self.config.projects else "project"

            # Create a config just to run infra tests
            dummy_config = PipelineConfig(
                project_name=fallback_project,
                repo_root=self.config.repo_root,
                skip_infra=False,
                skip_llm=True
            )

            executor = PipelineExecutor(dummy_config)

            # Run only the infrastructure tests stage
            success = executor._run_infrastructure_tests()

            if success:
                logger.info("✅ Infrastructure tests passed for all projects")
                return True
            else:
                logger.error("❌ Infrastructure tests failed")
                return False

        except Exception as e:
            logger.error(f"❌ Infrastructure tests failed with exception: {e}")
            return False

    def _run_executive_reporting(self, results: Dict[str, List[PipelineStageResult]]) -> None:
        """Generate cross-project executive report.

        Args:
            results: Results from all projects
        """
        if len(results) < 2:
            logger.info("Skipping executive reporting (requires 2+ projects)")
            return

        logger.info("Generating executive report for cross-project analysis...")

        try:
            # Import executive report generator
            from infrastructure.reporting import generate_multi_project_report

            # Extract project names from results
            project_names = list(results.keys())
            
            # Generate comprehensive multi-project report
            output_dir = self.config.repo_root / "output" / "executive_summary"
            report_files = generate_multi_project_report(
                self.config.repo_root,
                project_names,
                output_dir
            )
            
            logger.info("✅ Executive report generated successfully")
            logger.info(f"  Generated {len(report_files)} report files:")
            for file_type, path in report_files.items():
                logger.info(f"    • {file_type.upper()}: {path.name}")
            logger.info(f"  Reports saved to: {output_dir}")

        except ImportError as e:
            logger.warning(f"Executive reporting not available: {e}")
            logger.debug("  infrastructure.reporting module may not be properly configured")
        except Exception as e:
            logger.error(f"Executive reporting failed: {e}", exc_info=True)
            logger.info("  Continuing without executive report (non-critical)")