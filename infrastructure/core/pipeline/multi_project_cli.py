"""Multi-project pipeline CLI helpers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.core.project_paths import find_repo_root
from infrastructure.core.pipeline.multi_project import (
    MultiProjectConfig,
    MultiProjectOrchestrator,
    MultiProjectResult,
)
from infrastructure.core.pipeline.multi_project_parallel import (
    ParallelRunResult,
    run_projects_in_parallel,
)
from infrastructure.project.discovery import discover_projects
from infrastructure.project.project_info import ProjectInfo
from infrastructure.reporting.multi_project_report import (
    format_multi_project_detailed_report,
    write_last_run_summary,
)

logger = get_logger(__name__)


def execute_multi_project_parallel(
    repo_root: Path,
    *,
    run_llm: bool = True,
    max_workers: int | None = None,
    resume: bool = False,
) -> int:
    """Execute multi-project orchestration with bounded parallelism."""
    try:
        projects = discover_projects(repo_root)
        if not projects:
            logger.error("No valid projects found")
            return 1

        logger.info(
            "Found %d projects (parallel mode): %s",
            len(projects),
            ", ".join(p.qualified_name for p in projects),
        )

        result: ParallelRunResult = run_projects_in_parallel(
            projects,
            repo_root=repo_root,
            max_workers=max_workers,
            core_only=not run_llm,
            skip_llm=not run_llm,
            resume=resume,
        )

        log_header("MULTI-PROJECT EXECUTION RESULTS (PARALLEL)", logger)
        logger.info("Total Projects: %d", len(projects))
        logger.info("Successful: %d", len(result.succeeded))
        logger.info("Failed: %d", len(result.failed))
        logger.info("Total Duration: %.1fs", result.elapsed_seconds)

        if result.failed:
            logger.error("Failed projects:")
            for name in result.failed:
                logger.error("  - %s", name)
            return 1

        log_success("🎉 All projects completed successfully!", logger)
        return 0

    except Exception as e:  # noqa: BLE001 — top-level CLI boundary
        logger.error("Parallel multi-project execution failed: %s", e)
        return 1


def _log_project_status(result: object) -> None:
    project_results = getattr(result, "project_results", None)
    if not project_results:
        return
    logger.info("Project Status:")
    if not isinstance(project_results, dict):
        logger.warning("  ⚠ project_results format unexpected")
        return
    for raw_name, proj_result in sorted(project_results.items(), key=lambda item: str(item[0])):
        proj_name = str(raw_name)
        if isinstance(proj_result, list) and proj_result:
            all_success = all(bool(getattr(stage, "success", False)) for stage in proj_result)
            duration = sum(float(getattr(stage, "duration", 0.0)) for stage in proj_result)
            status = "✅" if all_success else "❌"
            logger.info(f"  {status} {proj_name}: {len(proj_result)} stages, {duration:.1f}s")
        else:
            logger.info(f"  ❓ {proj_name}: Unknown status")


def _write_summary_reports(
    result: MultiProjectResult,
    projects: list[ProjectInfo],
    repo_root: Path,
) -> None:
    try:
        from infrastructure.reporting.multi_project_reporter import generate_multi_project_summary_report

        summary_output_dir = repo_root / "output" / "multi_project_summary"
        summary_output_dir.mkdir(parents=True, exist_ok=True)
        summary_files = generate_multi_project_summary_report(
            result=result, projects=projects, output_dir=summary_output_dir
        )
        logger.info("Multi-project summary reports generated:")
        for fmt, path in summary_files.items():
            logger.info(f"  • {fmt.upper()}: {path}")
    except ImportError:
        logger.warning("Multi-project summary generation not available")
    except Exception as e:
        logger.warning(f"Failed to generate multi-project summary: {e}")

    try:
        summary_lines = format_multi_project_detailed_report(
            result=result,
            ordered_projects=projects,
            repo_root=repo_root,
        )
        artifact = write_last_run_summary(summary_lines, repo_root)
        if artifact is not None:
            logger.info(f"  • LAST-RUN: {artifact}")
    except Exception as e:
        logger.warning(f"Failed to write last-run-summary.md: {e}")


def _failed_project_names(result: object) -> list[str]:
    project_results = getattr(result, "project_results", None)
    if not project_results:
        return []
    failed: list[str] = []
    for name, results_list in project_results.items():
        project_name = str(name)
        if isinstance(results_list, list) and results_list:
            if not all(bool(getattr(stage, "success", False)) for stage in results_list):
                failed.append(project_name)
        elif not results_list:
            failed.append(project_name)
    return failed


def execute_multi_project(
    repo_root: Path,
    run_infra_tests: bool = True,
    run_llm: bool = True,
    run_executive_report: bool = True,
    skip_infra: bool = False,
) -> int:
    """Execute multi-project orchestration serially."""
    try:
        projects = discover_projects(repo_root)
        if not projects:
            logger.error("No valid projects found")
            return 1

        logger.info(f"Found {len(projects)} projects: {', '.join([p.name for p in projects])}")

        config = MultiProjectConfig(
            repo_root=repo_root,
            projects=projects,
            run_infra_tests=run_infra_tests,
            run_llm=run_llm,
            run_executive_report=run_executive_report,
        )
        orchestrator = MultiProjectOrchestrator(config)

        if skip_infra:
            result = orchestrator.execute_all_projects_full_no_infra()
            operation_desc = "multi-project execution (no infra)"
        elif run_llm and run_infra_tests:
            result = orchestrator.execute_all_projects_full()
            operation_desc = "multi-project full execution"
        elif not run_llm and run_infra_tests:
            result = orchestrator.execute_all_projects_core()
            operation_desc = "multi-project core execution"
        elif not run_llm and not run_infra_tests:
            result = orchestrator.execute_all_projects_core_no_infra()
            operation_desc = "multi-project core execution (no infra)"
        else:
            result = orchestrator.execute_all_projects_core()
            operation_desc = "multi-project core execution"

        total_projects = len(projects)
        success_rate = (result.successful_projects / total_projects * 100) if total_projects > 0 else 0

        log_header("MULTI-PROJECT EXECUTION RESULTS", logger)
        logger.info(f"Operation: {operation_desc}")
        logger.info(f"Total Projects: {total_projects}")
        logger.info(f"Successful: {result.successful_projects}")
        failed_projects = total_projects - result.successful_projects
        logger.info(f"Failed: {failed_projects}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info(f"Total Duration: {result.total_duration:.1f}s")
        if total_projects > 0:
            logger.info(f"Average per Project: {result.total_duration / total_projects:.1f}s")

        if run_infra_tests and result.infra_test_duration > 0:
            infra_percentage = result.infra_test_duration / result.total_duration * 100
            logger.info(f"Infrastructure Tests: {result.infra_test_duration:.1f}s ({infra_percentage:.1f}%)")

        _log_project_status(result)
        _write_summary_reports(result, projects, repo_root)

        if result.successful_projects == len(projects):
            log_success("🎉 All projects completed successfully!", logger)
            return 0

        logger.error("❌ Some projects failed")
        for proj_name in _failed_project_names(result):
            logger.error(f"     - {proj_name}")
        return 1

    except Exception as e:
        logger.error(f"Multi-project execution failed: {e}")
        return 1


def build_arg_parser() -> argparse.ArgumentParser:
    """Build arg parser."""
    parser = argparse.ArgumentParser(description="Execute multi-project orchestration")
    parser.add_argument("--no-infra-tests", action="store_true", help="Skip infrastructure tests")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM stages")
    parser.add_argument("--no-executive-report", action="store_true", help="Skip executive report")
    parser.add_argument("--skip-infra", action="store_true", help="Skip infra tests for individual projects")
    parser.add_argument(
        "--parallel",
        action="store_true",
        help=(
            "Run each project's pipeline in a separate worker process via "
            "ProcessPoolExecutor. Default (without this flag) runs serially. "
            "MULTI_PROJECT_MAX_WORKERS env var sets the default pool size."
        ),
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help=(
            "Override the parallel worker count (only meaningful with "
            "--parallel). Defaults to min(N_projects, os.cpu_count()) or the "
            "value of MULTI_PROJECT_MAX_WORKERS when set."
        ),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume each project from its last checkpoint.",
    )
    return parser


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    """CLI entry point."""
    args = build_arg_parser().parse_args(argv)
    root = repo_root or find_repo_root()

    if args.parallel:
        return execute_multi_project_parallel(
            root,
            run_llm=not args.no_llm,
            max_workers=args.max_workers,
            resume=args.resume,
        )

    return execute_multi_project(
        root,
        run_infra_tests=not args.no_infra_tests,
        run_llm=not args.no_llm,
        run_executive_report=not args.no_executive_report,
        skip_infra=args.skip_infra,
    )


if __name__ == "__main__":
    sys.exit(main())
