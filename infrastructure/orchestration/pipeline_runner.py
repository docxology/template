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
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline import (
    MultiProjectConfig,
    MultiProjectOrchestrator,
    PipelineConfig,
    PipelineExecutor,
)
from infrastructure.core.pipeline.incremental import IncrementalConfig
from infrastructure.core.pipeline.multi_project import format_multi_project_outcome_lines
from infrastructure.orchestration.menu import STAGE_NAMES
from infrastructure.orchestration.stage_logger import (
    setup_multiproject_log,
    setup_stage_log,
)
from infrastructure.project.discovery import discover_projects
from infrastructure.reporting.multi_project_report import format_multi_project_detailed_report

logger = get_logger(__name__)


@dataclass
class PipelineInvocation:
    """User-facing options for a single-project pipeline run."""

    project: str
    skip_infra: bool = False
    skip_llm: bool = False
    resume: bool = False
    core_only: bool = False
    incremental: bool = False
    log_layout: str = "per_project"


@dataclass
class MultiProjectInvocation:
    """User-facing options for an all-projects pipeline run."""

    skip_infra: bool = False
    skip_llm: bool = False
    run_executive_report: bool = True


@dataclass
class PipelineRunner:
    """Thin facade over :class:`PipelineExecutor`.

    ``stream`` is the destination for the human-facing banners. Tests pass
    ``io.StringIO()``; the CLI passes ``sys.stdout``.
    """

    repo_root: Path
    stream: TextIO = field(default_factory=lambda: sys.stdout)

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
        # Set up the per-stage log file (banner-only — the executor handles
        # the actual file logging via its own handlers).
        setup_stage_log(
            self.repo_root,
            invocation.project,
            "Pipeline",
            layout=invocation.log_layout,
        )

        total = len(STAGE_NAMES)
        which = "core pipeline" if invocation.core_only else "full pipeline"
        self._emit(f"=== {which.upper()} === project={invocation.project}")
        for idx, name in enumerate(STAGE_NAMES, start=1):
            if invocation.core_only and name.startswith("LLM "):
                continue
            if invocation.skip_infra and name == "Infrastructure Tests":
                continue
            self._banner(idx, total, name, invocation.project)

        config = PipelineConfig(
            project_name=invocation.project,
            repo_root=self.repo_root,
            skip_infra=invocation.skip_infra,
            skip_llm=invocation.skip_llm or invocation.core_only,
            resume=invocation.resume,
            incremental=IncrementalConfig(enabled=invocation.incremental),
        )
        executor = PipelineExecutor(config)

        try:
            if invocation.core_only:
                results = executor.execute_core_pipeline()
            else:
                results = executor.execute_full_pipeline()
        except Exception as exc:  # noqa: BLE001 — bubble up as failure code
            logger.error("Pipeline execution failed: %s", exc, exc_info=True)
            self._emit(f"FAILED: {exc}")
            return 1

        success = all(getattr(r, "success", False) for r in results)
        self._emit("")
        self._emit("=== PIPELINE COMPLETE ===" if success else "=== PIPELINE FAILED ===")
        return 0 if success else 1

    def run_multi(self, invocation: MultiProjectInvocation) -> int:
        """Execute the all-projects orchestration."""
        setup_multiproject_log(self.repo_root)
        projects = discover_projects(self.repo_root)
        if not projects:
            self._emit("No projects discovered under projects/")
            return 1

        config = MultiProjectConfig(
            repo_root=self.repo_root,
            projects=projects,
            run_infra_tests=not invocation.skip_infra,
            run_llm=not invocation.skip_llm,
            run_executive_report=invocation.run_executive_report,
        )
        orchestrator = MultiProjectOrchestrator(config)

        if invocation.skip_infra and invocation.skip_llm:
            result = orchestrator.execute_all_projects_core_no_infra()
        elif invocation.skip_infra:
            result = orchestrator.execute_all_projects_full_no_infra()
        elif invocation.skip_llm:
            result = orchestrator.execute_all_projects_core()
        else:
            result = orchestrator.execute_all_projects_full()

        success = getattr(result, "successful_projects", 0) == len(projects) and len(projects) > 0
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
        return 0 if success else 1
