"""Thin facade over :class:`infrastructure.core.pipeline.PipelineExecutor`.

This module adds the human-facing banners and CLI plumbing that
``run.sh`` used to provide, **without** duplicating any pipeline logic.
All stage definitions, dependencies, and execution semantics still live
in :mod:`infrastructure.core.pipeline`.

The runner delegates to the existing pipeline executor and to the
existing :mod:`infrastructure.core.pipeline.multi_project` orchestrator
for ``--all-projects`` runs.
"""

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, TextIO

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.executor import PipelineExecutor
from infrastructure.core.pipeline.multi_project import MultiProjectConfig, MultiProjectOrchestrator
from infrastructure.core.pipeline.types import PipelineConfig
from infrastructure.core.pipeline.plan import compile_execution_plan
from infrastructure.core.pipeline.multi_project_runtime import freeze_project_plans, freeze_shared_plan
from infrastructure.core.pipeline.incremental import IncrementalConfig
from infrastructure.core.pipeline.multi_project import format_multi_project_outcome_lines
from infrastructure.orchestration.stage_logger import (
    setup_multiproject_log,
    setup_stage_log,
    stage_log_path,
)
from infrastructure.project.discovery import discover_projects
from infrastructure.orchestration.discovery import validate_project_slug
from infrastructure.reporting.multi_project_report import format_multi_project_detailed_report

logger = get_logger(__name__)


@dataclass
class PipelineInvocation:
    """User-facing options for a single-project pipeline run."""

    project: str
    skip_infra: bool = False
    resume: bool = False
    mode: str = "core"
    incremental: bool = False
    log_layout: str = "per_project"


@dataclass
class MultiProjectInvocation:
    """User-facing options for an all-projects pipeline run."""

    skip_infra: bool = False
    mode: str = "core"


@dataclass
class PipelineRunner:
    """Thin facade over :class:`PipelineExecutor`.

    ``stream`` is the destination for the human-facing banners. Tests pass
    ``io.StringIO()``; the CLI passes ``sys.stdout``.
    """

    repo_root: Path
    stream: TextIO = field(default_factory=lambda: sys.stdout)
    executor_factory: Callable[[PipelineConfig], Any] = PipelineExecutor
    orchestrator_factory: Callable[[MultiProjectConfig], Any] = MultiProjectOrchestrator

    def _emit(self, line: str) -> None:
        self.stream.write(line + "\n")
        self.stream.flush()

    def _banner(self, idx: int, total: int, label: str, project: str) -> None:
        self._emit("")
        self._emit(f"[{idx}/{total}] {label}  (project: {project})")
        self._emit("-" * 60)

    def run(self, invocation: PipelineInvocation) -> int:
        """Execute a single-project pipeline.

        Returns:
            Process exit code (0 on success).
        """
        try:
            project = validate_project_slug(invocation.project, self.repo_root)
        except ValueError as exc:
            self._emit(f"Invalid pipeline invocation: {exc}")
            return 2
        try:
            config = PipelineConfig(
                project_name=project,
                repo_root=self.repo_root,
                skip_infra=invocation.skip_infra,
                mode=invocation.mode,
                resume=invocation.resume,
                incremental=IncrementalConfig(enabled=invocation.incremental),
            )
            deadline = time.monotonic() + config.run_timeout_seconds
            stage_log_path(self.repo_root, project, layout=invocation.log_layout)
            plan = compile_execution_plan(config)
            stage_names = tuple(stage.name for stage in plan.stages)
            which = f"{invocation.mode} pipeline"
        except ValueError as exc:
            self._emit(f"Invalid pipeline invocation: {exc}")
            return 2
        if not stage_names:
            self._emit(f"FAILED: {which} has no executable stages")
            return 1
        if time.monotonic() >= deadline:
            self._emit("Pipeline deadline expired during plan preflight")
            return 124
        executor: Any = None
        try:
            # Logging starts only after the exact selected contract is valid.
            setup_stage_log(self.repo_root, project, "Pipeline", layout=invocation.log_layout)
            executor = self.executor_factory(config)
            self._emit(f"=== {which.upper()} === project={project}")
            for idx, name in enumerate(stage_names, start=1):
                self._banner(idx, len(stage_names), name, project)
            results = executor.execute_plan(plan, deadline_monotonic=deadline)
        except TimeoutError as exc:
            self._emit(f"Pipeline deadline expired: {exc}")
            return 124
        except KeyboardInterrupt:
            return 130
        except Exception as exc:  # noqa: BLE001 — bubble up as failure code
            logger.error("Pipeline execution failed: %s", exc, exc_info=True)
            self._emit(f"FAILED: {exc}")
            return 1
        finally:
            # Release only our actual executor; custom factories own their resources.
            if isinstance(executor, PipelineExecutor):
                executor.close()

        outcome = executor.run_result(results)
        success = outcome.complete
        self._emit("")
        self._emit("=== PIPELINE COMPLETE ===" if success else "=== PIPELINE FAILED ===")
        return int(outcome.exit_code)

    def run_multi(self, invocation: MultiProjectInvocation) -> int:
        """Execute the all-projects orchestration."""
        projects = discover_projects(self.repo_root)
        if not projects:
            self._emit("No projects discovered under projects/")
            return 1

        config = MultiProjectConfig(
            repo_root=self.repo_root,
            projects=projects,
            run_infra_tests=not invocation.skip_infra,
            mode=invocation.mode,
        )
        try:
            config.deadline_monotonic = time.monotonic() + config.run_timeout_seconds
            specs = freeze_project_plans(
                projects,
                self.repo_root,
                mode=config.mode,
                resume=config.resume,
                timeout=config.run_timeout_seconds,
            )
            shared = freeze_shared_plan(specs) if config.run_infra_tests else None
            if time.monotonic() >= config.deadline_monotonic:
                raise TimeoutError("Multi-project deadline expired during plan preflight")
            setup_multiproject_log(self.repo_root)
            orchestrator = self.orchestrator_factory(config)
            result = orchestrator.execute_prepared_projects(specs, shared)
        except ValueError as exc:
            self._emit(f"Invalid multi-project invocation: {exc}")
            return 2
        except TimeoutError as exc:
            self._emit(f"Multi-project deadline expired: {exc}")
            return 124
        except KeyboardInterrupt:
            return 130
        except Exception as exc:
            self._emit(f"Multi-project execution failed: {exc}")
            return 1

        success = result.exit_code == 0
        self._emit(
            f"=== MULTI-PROJECT {'COMPLETE' if success else 'FAILED'} === "
            f"{getattr(result, 'successful_projects', 0)}/{len(projects)} succeeded"
        )
        outcome_lines = format_multi_project_outcome_lines(projects, result)
        if outcome_lines:
            self._emit("")
            for line in outcome_lines:
                self._emit(line)

        detailed_lines = format_multi_project_detailed_report(projects, result, repo_root=self.repo_root)
        if detailed_lines:
            self._emit("")
            for line in detailed_lines:
                self._emit(line)
        return int(result.exit_code)
