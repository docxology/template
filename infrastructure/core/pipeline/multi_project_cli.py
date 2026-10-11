"""Multi-project pipeline CLI helpers."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.core.project_paths import find_repo_root
from infrastructure.core.pipeline.multi_project import (
    MultiProjectConfig,
    MultiProjectOrchestrator,
    MultiProjectResult,
)
from infrastructure.core.pipeline.multi_project_support import validated_run_for_rows
from infrastructure.core.pipeline.multi_project_parallel import (
    ParallelRunResult,
    run_projects_in_parallel,
)
from infrastructure.project.discovery import discover_projects
from infrastructure.project.project_info import ProjectInfo
from infrastructure.core.pipeline.multi_project_runtime import validate_budget

logger = get_logger(__name__)


def execute_multi_project_parallel(
    repo_root: Path,
    *,
    mode: str = "core",
    max_workers: int | None = None,
    resume: bool = False,
    run_infra_tests: bool = True,
    run_timeout_seconds: float = 14400.0,
) -> int:
    """Execute multi-project orchestration with bounded parallelism."""
    try:
        validate_budget(run_timeout_seconds)
        deadline = time.monotonic() + run_timeout_seconds
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
            mode=mode,
            run_infra_tests=run_infra_tests,
            resume=resume,
            run_timeout_seconds=run_timeout_seconds,
            deadline_monotonic=deadline,
        )

        log_header("MULTI-PROJECT EXECUTION RESULTS (PARALLEL)", logger)
        logger.info("Total Projects: %d", len(projects))
        logger.info("Successful: %d", len(result.succeeded))
        logger.info("Failed: %d", len(result.failed))
        logger.info("Total Duration: %.1fs", result.elapsed_seconds)

        aggregate = MultiProjectResult(
            result.project_results,
            result.infra_test_duration,
            result.elapsed_seconds,
            len(result.succeeded),
            len(result.failed),
            result.expected_projects,
            result.run_results,
            result.shared_infrastructure_exit_code,
            result.shared_infrastructure_result,
        )
        report_exit = _write_summary_reports(aggregate, projects, repo_root, deadline=deadline)
        exit_code = _combined_exit(result.exit_code, report_exit)
        if exit_code != 0:
            logger.error("Failed projects:")
            for name in result.failed:
                logger.error("  - %s", name)
            return exit_code

        log_success("🎉 All projects completed successfully!", logger)
        return 0

    except KeyboardInterrupt:
        return 130
    except TimeoutError as e:
        logger.error("Parallel multi-project deadline expired: %s", e)
        return 124
    except ValueError as e:
        logger.error("Invalid parallel invocation: %s", e)
        return 2
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
            contracts = getattr(result, "run_results", {})
            run = validated_run_for_rows(proj_result, contracts.get(proj_name))
            all_success = run is not None and run.complete
            duration = sum(float(getattr(stage, "duration", 0.0)) for stage in proj_result)
            status = "✅" if all_success else "❌"
            logger.info(f"  {status} {proj_name}: {len(proj_result)} stages, {duration:.1f}s")
        else:
            logger.info(f"  ❓ {proj_name}: Unknown status")


def _combined_exit(*codes: int) -> int:
    return next((code for code in (130, 124, 1, 75) if code in codes), 0)


def _write_summary_reports(
    result: MultiProjectResult, projects: list[ProjectInfo], repo_root: Path, *, deadline: float
) -> int:
    from infrastructure.core.pipeline.multi_project_summary import write_summary_reports

    try:
        return write_summary_reports(result, projects, repo_root, deadline=deadline)
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, TypeError, KeyError) as exc:
        logger.error("Aggregate reporting failed: %s", exc)
        return 1


def _failed_project_names(result: object) -> list[str]:
    project_results = getattr(result, "project_results", None)
    contracts = getattr(result, "run_results", {})
    fallback = tuple(project_results) if isinstance(project_results, dict) else ()
    expected = getattr(result, "expected_projects", fallback)
    failures = []
    for name in expected:
        rows = project_results.get(name) if isinstance(project_results, dict) else None
        run = validated_run_for_rows(rows, contracts.get(name))
        if run is None or not run.complete:
            failures.append(name)
    return failures


def execute_multi_project(
    repo_root: Path,
    run_infra_tests: bool = True,
    mode: str = "core",
    skip_infra: bool = False,
    resume: bool = False,
    run_timeout_seconds: float = 14400.0,
) -> int:
    """Execute multi-project orchestration serially."""
    try:
        validate_budget(run_timeout_seconds)
        deadline = time.monotonic() + run_timeout_seconds
        projects = discover_projects(repo_root)
        if not projects:
            logger.error("No valid projects found")
            return 1

        logger.info(f"Found {len(projects)} projects: {', '.join([p.name for p in projects])}")

        config = MultiProjectConfig(
            repo_root=repo_root,
            projects=projects,
            run_infra_tests=run_infra_tests and not skip_infra,
            mode=mode,
            resume=resume,
            run_timeout_seconds=run_timeout_seconds,
            deadline_monotonic=deadline,
        )
        orchestrator = MultiProjectOrchestrator(config)

        result = orchestrator.execute_all_projects()
        operation_desc = f"multi-project {mode} execution"

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
            infra_percentage = (
                result.infra_test_duration / result.total_duration * 100 if result.total_duration else 0.0
            )
            logger.info(f"Infrastructure Tests: {result.infra_test_duration:.1f}s ({infra_percentage:.1f}%)")

        _log_project_status(result)
        report_exit = _write_summary_reports(result, projects, repo_root, deadline=deadline)
        exit_code = _combined_exit(result.exit_code, report_exit)

        if exit_code == 0:
            log_success("🎉 All projects completed successfully!", logger)
            return 0

        logger.error("❌ Some projects failed")
        for proj_name in _failed_project_names(result):
            logger.error(f"     - {proj_name}")
        return exit_code

    except KeyboardInterrupt:
        return 130
    except TimeoutError as e:
        logger.error("Multi-project deadline expired: %s", e)
        return 124
    except ValueError as e:
        logger.error("Invalid multi-project invocation: %s", e)
        return 2
    except Exception as e:
        logger.error(f"Multi-project execution failed: {e}")
        return 1


def build_arg_parser() -> argparse.ArgumentParser:
    """Build arg parser."""
    parser = argparse.ArgumentParser(description="Execute multi-project orchestration")
    parser.add_argument("--no-infra-tests", action="store_true", help="Skip infrastructure tests")
    parser.add_argument("--mode", choices=("core", "live"), default="core")
    parser.add_argument("--skip-infra", action="store_true", help="Skip infra tests for individual projects")
    parser.add_argument(
        "--parallel",
        action="store_true",
        help=(
            "Run each project's pipeline in a separate worker process via "
            "a finite subprocess scheduler. Default runs serially. "
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
    parser.add_argument(
        "--run-timeout",
        type=float,
        default=14400.0,
        help="Whole-run seconds for shared verification, queue, workers and reporting.",
    )
    return parser


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    """CLI entry point."""
    args = build_arg_parser().parse_args(argv)
    root = repo_root or find_repo_root()

    if args.parallel:
        return execute_multi_project_parallel(
            root,
            mode=args.mode,
            run_infra_tests=not (args.no_infra_tests or args.skip_infra),
            max_workers=args.max_workers,
            resume=args.resume,
            run_timeout_seconds=args.run_timeout,
        )

    return execute_multi_project(
        root,
        run_infra_tests=not args.no_infra_tests,
        mode=args.mode,
        resume=args.resume,
        skip_infra=args.skip_infra,
        run_timeout_seconds=args.run_timeout,
    )


if __name__ == "__main__":
    sys.exit(main())
