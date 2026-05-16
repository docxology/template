"""Multi-project orchestration system.

This module provides orchestration for running pipelines across multiple projects,
extracted from the bash run.sh script into testable Python code.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from infrastructure.core.logging.utils import get_logger, log_operation
from infrastructure.core.errors import PROJECT_EXCEPTION, PROJECT_FAILED
from infrastructure.core.pipeline.executor import PipelineConfig, PipelineExecutor, PipelineStageResult

if TYPE_CHECKING:
    from infrastructure.project.project_info import ProjectInfo

logger = get_logger(__name__)


def _projects_dir_for_project(repo_root: Path, project_path: Path) -> str:
    """Return the repository-relative projects root for a discovered project."""
    try:
        relative_parts = project_path.resolve().relative_to(repo_root.resolve()).parts
    except ValueError:
        return "projects"
    return relative_parts[0] if relative_parts else "projects"


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

    project_results: dict[str, list[PipelineStageResult]]
    infra_test_duration: float = 0.0
    total_duration: float = 0.0
    successful_projects: int = 0
    failed_projects: int = 0


def format_multi_project_outcome_lines(
    ordered_projects: Sequence[ProjectInfo],
    result: MultiProjectResult,
    *,
    hint_max_chars: int = 160,
) -> list[str]:
    """Human-readable lines naming succeeded vs failed projects (serial multi-project UX).

    ``ordered_projects`` must match discovery order and use ``qualified_name`` keys
    consistent with :class:`MultiProjectOrchestrator`.

    Args:
        ordered_projects: Projects in run order (same list passed to orchestrator config).
        result: Aggregate result from ``execute_all_projects_*``.
        hint_max_chars: Truncate first failing stage ``error_message`` to this length.
    """
    lines: list[str] = []
    n = len(ordered_projects)
    if n == 0:
        return lines

    pr = result.project_results
    infra_aborted = len(pr) == 0 and result.successful_projects == 0 and result.failed_projects == n
    if infra_aborted:
        lines.append(
            "Infrastructure tests failed — no project pipelines were run.",
        )
        return lines

    succeeded: list[str] = []
    failed: list[str] = []

    for proj in ordered_projects:
        qn = proj.qualified_name
        stages = pr.get(qn)
        if stages is None:
            failed.append(f"{qn}: no pipeline results recorded")
            continue
        if not stages:
            failed.append(f"{qn}: pipeline failed before stage results were recorded")
            continue
        if all(stage.success for stage in stages):
            succeeded.append(qn)
        else:
            first_bad = next((s for s in stages if not s.success), None)
            if first_bad is None:
                failed.append(f"{qn}: unknown stage failure")
                continue
            msg = (first_bad.error_message or "").strip()
            if len(msg) > hint_max_chars:
                msg = msg[: hint_max_chars - 1] + "…"
            if msg:
                failed.append(f"{qn}: {first_bad.stage_name} — {msg}")
            else:
                failed.append(f"{qn}: {first_bad.stage_name}")

    if succeeded:
        lines.append("Succeeded:")
        lines.extend(f"  - {name}" for name in succeeded)
    if failed:
        lines.append("Failed:")
        lines.extend(f"  - {entry}" for entry in failed)
    return lines


def _dir_size_mb(path: Path) -> float:
    """Best-effort total size of files under ``path`` in megabytes (0.0 on error)."""
    if not path.exists():
        return 0.0
    total = 0
    try:
        for p in path.rglob("*"):
            if p.is_file():
                try:
                    total += p.stat().st_size
                except OSError:
                    continue
    except OSError:
        return 0.0
    return total / (1024 * 1024)


def _fmt_duration(seconds: float) -> str:
    """Format seconds as ``9.4s`` or ``2m 6s``."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(round(seconds)), 60)
    return f"{m}m {s:02d}s"


def format_multi_project_detailed_report(
    ordered_projects: Sequence[ProjectInfo],
    result: MultiProjectResult,
    *,
    repo_root: Path | None = None,
    width: int = 80,
) -> list[str]:
    """Render a rich end-of-run summary for multi-project execution.

    Designed for option ``d`` (all-projects core/fast) end-of-run UX. Returns
    a list of plain ASCII lines (no ANSI). Sections:

    1. Header banner with aggregate counts and wall time.
    2. Per-project status table (status icon, name, stage progress, duration,
       output size, first failing stage).
    3. Stage timing breakdown (avg/total/ok-count across projects).
    4. Failure details with pointers to logs and reports.
    5. Output locations + recommended next steps.

    Tests can assert on substrings of returned lines without parsing layout.
    """
    n = len(ordered_projects)
    succ = result.successful_projects
    failed = n - succ
    rate = (succ / n * 100.0) if n else 0.0
    total = float(result.total_duration or 0.0)
    avg = (total / n) if n else 0.0

    bar = "=" * width
    sep = "-" * width
    out: list[str] = []

    # Header banner
    out.append(bar)
    out.append("MULTI-PROJECT EXECUTION SUMMARY".center(width))
    out.append(f"{n} projects  ·  {succ} succeeded  ·  {failed} failed  ·  {rate:.1f}% success".center(width))
    out.append(f"wall time {_fmt_duration(total)}  ·  avg/project {_fmt_duration(avg)}".center(width))
    if result.infra_test_duration and result.infra_test_duration > 0:
        out.append(f"infrastructure tests: {_fmt_duration(result.infra_test_duration)}".center(width))
    out.append(bar)

    # Per-project status table
    pr = result.project_results
    rows: list[tuple[str, str, str, str, str, str]] = []
    project_durations: list[tuple[str, float]] = []
    for proj in ordered_projects:
        qn = proj.qualified_name
        stages = pr.get(qn) or []
        total_stages = len(stages)
        ok_stages = sum(1 for s in stages if getattr(s, "success", False))
        dur = sum(float(getattr(s, "duration", 0.0)) for s in stages)
        project_durations.append((qn, dur))
        if total_stages == 0:
            icon = "❌"
            fail_at = "no stages ran"
        elif ok_stages == total_stages:
            icon = "✅"
            fail_at = ""
        else:
            icon = "❌"
            first_bad = next(
                (s for s in stages if not getattr(s, "success", False)),
                None,
            )
            fail_at = getattr(first_bad, "stage_name", "unknown") if first_bad else "unknown"

        out_dir = (repo_root / "projects" / qn / "output") if repo_root is not None else Path()
        size_mb = _dir_size_mb(out_dir) if repo_root is not None else 0.0
        rows.append(
            (
                icon,
                qn,
                f"{ok_stages}/{total_stages} stages" if total_stages else "0 stages",
                _fmt_duration(dur),
                f"{size_mb:.2f} MB" if size_mb else "—",
                fail_at,
            )
        )

    out.append("")
    out.append("PROJECT STATUS")
    out.append(sep)
    name_w = max((len(r[1]) for r in rows), default=12)
    stages_w = max((len(r[2]) for r in rows), default=8)
    for icon, name, stages_str, dur, size, fail_at in rows:
        suffix = f"   failed at: {fail_at}" if fail_at else ""
        out.append(f" {icon}  {name:<{name_w}}  {stages_str:<{stages_w}}  {dur:>7}  out: {size:>9}{suffix}")

    # Stage timing breakdown across all projects
    out.append("")
    out.append("STAGE TIMING BREAKDOWN")
    out.append(sep)
    stage_stats: dict[str, dict[str, float]] = {}
    for proj in ordered_projects:
        for s in pr.get(proj.qualified_name, []) or []:
            name = getattr(s, "stage_name", "?")
            entry = stage_stats.setdefault(name, {"total": 0.0, "n": 0.0, "ok": 0.0})
            entry["total"] += float(getattr(s, "duration", 0.0))
            entry["n"] += 1.0
            entry["ok"] += 1.0 if getattr(s, "success", False) else 0.0

    if stage_stats:
        out.append(f" {'Stage':<28}  {'Avg':>7}  {'Total':>8}  {'Status':>14}")
        for stage_name in sorted(stage_stats.keys(), key=lambda k: stage_stats[k]["total"], reverse=True):
            e = stage_stats[stage_name]
            avg_s = e["total"] / e["n"] if e["n"] else 0.0
            status = f"{int(e['ok'])}/{int(e['n'])} ok"
            out.append(
                f" {stage_name[:28]:<28}  {_fmt_duration(avg_s):>7}  {_fmt_duration(e['total']):>8}  {status:>14}"
            )
    else:
        out.append("  (no stage data recorded)")

    # Performance highlights
    if project_durations:
        ranked = sorted(project_durations, key=lambda kv: kv[1])
        fastest_name, fastest_dur = ranked[0]
        slowest_name, slowest_dur = ranked[-1]
        out.append("")
        out.append("PERFORMANCE HIGHLIGHTS")
        out.append(sep)
        out.append(f"  Fastest project: {fastest_name}  ({_fmt_duration(fastest_dur)})")
        out.append(f"  Slowest project: {slowest_name}  ({_fmt_duration(slowest_dur)})")

    # Failure details
    failure_rows: list[tuple[str, str, str]] = []
    for proj in ordered_projects:
        qn = proj.qualified_name
        stages = pr.get(qn) or []
        if not stages:
            failure_rows.append((qn, "pipeline aborted before any stage ran", ""))
            continue
        if all(getattr(s, "success", False) for s in stages):
            continue
        first_bad = next((s for s in stages if not getattr(s, "success", False)), None)
        if first_bad is None:
            continue
        err = (getattr(first_bad, "error_message", "") or "").strip()
        if len(err) > 160:
            err = err[:159] + "…"
        failure_rows.append((qn, getattr(first_bad, "stage_name", "?"), err))

    if failure_rows:
        out.append("")
        out.append("FAILURE DETAILS")
        out.append(sep)
        for qn, stage_name, err in failure_rows:
            out.append(f"  ❌ {qn}")
            out.append(f"     Stage : {stage_name}")
            if err:
                out.append(f"     Error : {err}")
            if repo_root is not None:
                log_path = repo_root / "projects" / qn / "output" / "logs" / "pipeline.log"
                if log_path.exists():
                    try:
                        rel = log_path.relative_to(repo_root)
                    except ValueError:
                        rel = log_path
                    out.append(f"     Log   : {rel}")
                report_path = repo_root / "projects" / qn / "output" / "reports" / "test_results.md"
                if report_path.exists():
                    try:
                        rel = report_path.relative_to(repo_root)
                    except ValueError:
                        rel = report_path
                    out.append(f"     Report: {rel}")
            out.append("")

    # Output locations + next steps
    if repo_root is not None:
        out.append("OUTPUT LOCATIONS")
        out.append(sep)
        summary_md = repo_root / "output" / "multi_project_summary" / "multi_project_summary.md"
        if summary_md.exists():
            try:
                rel = summary_md.relative_to(repo_root)
            except ValueError:
                rel = summary_md
            out.append(f"  Summary report : {rel}")
        for proj in ordered_projects:
            qn = proj.qualified_name
            stages = pr.get(qn) or []
            if not (stages and all(getattr(s, "success", False) for s in stages)):
                continue
            pdf_dir = repo_root / "output" / qn
            if pdf_dir.exists():
                pdfs = sorted(pdf_dir.glob("*.pdf"))
                for pdf in pdfs[:2]:
                    try:
                        rel = pdf.relative_to(repo_root)
                    except ValueError:
                        rel = pdf
                    out.append(f"  Output PDF     : {rel}")

        out.append("")
        out.append("NEXT STEPS")
        out.append(sep)
        if failure_rows:
            sample = failure_rows[0][0].split("/")[-1]
            out.append(f"  • Re-run a failed project: ./run.sh --project {sample} --pipeline --core-only --skip-infra")
            out.append("  • Inspect a failure log : cat projects/<name>/output/logs/pipeline.log")
        else:
            out.append("  • All projects passed. Inspect outputs under output/<project>/")

    # Final status banner
    out.append("")
    if failed == 0 and n > 0:
        out.append(bar)
        out.append(f"🎉 ALL {n} PROJECTS PASSED  ·  {_fmt_duration(total)}".center(width))
        out.append(bar)
    else:
        out.append(bar)
        out.append(f"⚠️  {succ}/{n} succeeded  ·  {failed} failed  ·  {_fmt_duration(total)}".center(width))
        out.append(bar)

    return out


class MultiProjectOrchestrator:
    """Orchestrate pipeline execution across multiple projects."""

    def __init__(
        self,
        config: MultiProjectConfig,
        on_project_complete: Callable[[str, list[PipelineStageResult], Path], None] | None = None,
    ):
        """Initialize multi-project orchestrator.

        Args:
            config: Multi-project configuration
            on_project_complete: Optional callback invoked after each project finishes.
                Receives (project_name, stage_results, output_dir). Use this at the
                call-site to generate reports without importing reporting modules here.
        """
        self.config = config
        self.on_project_complete = on_project_complete

    def execute_all_projects_full(self) -> MultiProjectResult:
        """Execute full pipeline for all projects (with infrastructure tests, with LLM).

        Returns:
            Multi-project execution result
        """
        logger.info(f"Executing full pipeline for {len(self.config.projects)} projects")

        return self._execute_multi_project_pipeline(run_infra_tests=True, run_llm=True)

    def execute_all_projects_core(self) -> MultiProjectResult:
        """Execute core pipeline for all projects (with infrastructure tests, no LLM).

        Returns:
            Multi-project execution result
        """
        logger.info(f"Executing core pipeline for {len(self.config.projects)} projects")

        return self._execute_multi_project_pipeline(run_infra_tests=True, run_llm=False)

    def execute_all_projects_full_no_infra(self) -> MultiProjectResult:
        """Execute full pipeline for all projects (no infrastructure tests, with LLM).

        Returns:
            Multi-project execution result
        """
        logger.info(f"Executing full pipeline (no infra) for {len(self.config.projects)} projects")

        return self._execute_multi_project_pipeline(run_infra_tests=False, run_llm=True)

    def execute_all_projects_core_no_infra(self) -> MultiProjectResult:
        """Execute core pipeline for all projects (no infrastructure tests, no LLM).

        Returns:
            Multi-project execution result
        """
        logger.info(f"Executing core pipeline (no infra) for {len(self.config.projects)} projects")

        return self._execute_multi_project_pipeline(run_infra_tests=False, run_llm=False)

    def _execute_multi_project_pipeline(self, run_infra_tests: bool, run_llm: bool) -> MultiProjectResult:
        """Execute pipeline across multiple projects.

        Args:
            run_infra_tests: Whether to run infrastructure tests once at start
            run_llm: Whether to include LLM stages

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
                    failed_projects=len(self.config.projects),
                )
            infra_duration = time.time() - start_time
            logger.info(f"✅ Infrastructure tests completed in {infra_duration:.1f}s")
        else:
            logger.info("Skipping infrastructure tests (already run or disabled)")

        # Execute pipeline for each project
        successful_projects = 0
        failed_projects = 0

        for i, project in enumerate(self.config.projects, 1):
            # Use qualified_name to include program directory for nested projects
            # e.g., 'cognitive_integrity/cogsec_multiagent_1_theory' instead of 'cogsec_multiagent_1_theory'  # noqa: E501
            project_name = project.qualified_name
            logger.info(f"Project {i}/{len(self.config.projects)}: {project_name}")

            try:
                with log_operation(f"Pipeline execution for {project_name}"):
                    # Preserve qualified names for nested projects.  The
                    # projects_dir remains the top-level pool (projects or
                    # projects_in_progress); project_name carries any program
                    # subpath, e.g. cognitive_integrity/cogsec_multiagent_1_theory.
                    pipeline_config = PipelineConfig(
                        project_name=project_name,
                        repo_root=self.config.repo_root,
                        projects_dir=_projects_dir_for_project(self.config.repo_root, project.path),
                        skip_infra=True,  # Always skip infra tests for individual projects in multi-project mode  # noqa: E501
                        skip_llm=not run_llm,
                        total_stages=10 if run_llm else 8,
                    )

                    # Execute pipeline
                    executor = PipelineExecutor(pipeline_config)
                    method = executor.execute_full_pipeline if run_llm else executor.execute_core_pipeline
                    results = method()

                    project_results[project_name] = results

                    # Notify call-site that this project finished (e.g. for report generation).
                    # Reporting logic lives at the call-site to avoid a downward dependency
                    # from core/ into the higher-level reporting/ layer.
                    if self.on_project_complete is not None:
                        output_dir = pipeline_config.project_dir / "output"
                        try:
                            self.on_project_complete(project_name, results, output_dir)
                        except Exception as e:  # noqa: BLE001 - callback can raise anything
                            logger.warning(
                                f"Project completion callback failed for {project_name}: {e}",
                                exc_info=True,
                            )

                    # Check if all stages succeeded
                    all_success = all(r.success for r in results)
                    if all_success:
                        successful_projects += 1
                        logger.info(f"✅ Project '{project_name}' completed successfully")
                    else:
                        failed_projects += 1
                        logger.error(PROJECT_FAILED.format(project_name=project_name))
                        # Continue with other projects even if one fails

            except Exception as e:  # noqa: BLE001 - pipeline execution can raise varied exceptions
                failed_projects += 1
                logger.error(PROJECT_EXCEPTION.format(project_name=project_name, error=e))
                project_results[project_name] = []

        # Executive reporting is handled by the dedicated pipeline stage
        # (07_generate_executive_report.py), which runs as part of the stage executor.

        total_duration = time.time() - start_time

        logger.info(
            f"Multi-project execution completed: {successful_projects} successful, {failed_projects} failed"  # noqa: E501
        )

        return MultiProjectResult(
            project_results=project_results,
            infra_test_duration=infra_duration,
            total_duration=total_duration,
            successful_projects=successful_projects,
            failed_projects=failed_projects,
        )

    def _run_infrastructure_tests_once(self) -> bool:
        """Run infrastructure tests once before all projects.

        Returns:
            True if infrastructure tests passed, False otherwise
        """
        logger.info("Running infrastructure tests once for all projects...")

        try:
            # Use an existing project name so reports can be written under projects/{name}/output/reports/  # noqa: E501
            # (the infrastructure test suite itself does not depend on project code).
            # Use qualified_name for proper nested project path resolution.
            fallback_project = self.config.projects[0].qualified_name if self.config.projects else "project"

            # Create a config just to run infra tests
            dummy_config = PipelineConfig(
                project_name=fallback_project,
                repo_root=self.config.repo_root,
                skip_infra=False,
                skip_llm=True,
            )

            executor = PipelineExecutor(dummy_config)

            # Run only the infrastructure tests stage
            success = executor.run_infrastructure_tests()

            if success:
                logger.info("✅ Infrastructure tests passed for all projects")
                return True
            else:
                logger.error("❌ Infrastructure tests failed")
                return False

        except Exception as e:  # noqa: BLE001 - infra tests can raise varied exceptions
            logger.error(f"❌ Infrastructure tests failed with exception: {e}")
            return False
