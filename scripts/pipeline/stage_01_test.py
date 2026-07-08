#!/usr/bin/env python3
"""Test suite orchestrator script.

This thin orchestrator runs the complete test suite for the project:
1. Runs infrastructure tests with 60%+ coverage
2. Runs project tests with 90%+ coverage
3. Reports test results
4. Validates test infrastructure

Stage 01 of the pipeline orchestration.

Note: For separate infrastructure/project test runs, use ./run.sh which
provides an interactive menu with options 1 (infrastructure) and 2 (project).

Exit codes:
    0: All required tests passed
    1: Project tests failed (infrastructure failures are logged but non-fatal)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header, log_live_resource_usage, log_substep
from infrastructure.core.pytest_marker_exprs import build_pytest_marker_expression
from infrastructure.core.test_runner import run_per_project_pytest
from infrastructure.reporting.pipeline_test_runner import INFRASTRUCTURE_TEST_SCOPES, execute_test_pipeline

# Set up logger for this module
logger = get_logger(__name__)


def main() -> int:
    """Execute test suite orchestration.

    Runs both infrastructure and project tests in sequence.
    Infrastructure test failures are reported but don't fail the pipeline.

    Returns:
        Exit code (0=project tests passed, 1=project tests failed)
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run test suite")
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress individual test names (default: verbose mode)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show individual test names (default; use --quiet to suppress)",
    )
    parser.add_argument(
        "--project",
        default="project",
        help="Project name in projects/ directory (default: project)",
    )
    parser.add_argument(
        "--non-strict",
        action="store_true",
        help="Allow configured test-failure tolerances (not recommended for CI)",
    )
    parser.add_argument(
        "--include-slow",
        action="store_true",
        help="Include slow tests (normally skipped for faster execution)",
    )
    parser.add_argument(
        "--include-long-running",
        action="store_true",
        help=(
            "Include long-running end-to-end/deep gate tests. These are heavier "
            "than ordinary slow tests and are skipped by default."
        ),
    )
    parser.add_argument(
        "--infra-only",
        action="store_true",
        help="Run only infrastructure tests (skip project tests)",
    )
    parser.add_argument(
        "--infra-scope",
        choices=INFRASTRUCTURE_TEST_SCOPES,
        default="full",
        help=(
            "Infrastructure test scope. 'full' runs the coverage-bearing repo "
            "suite; 'pipeline-smoke' runs the focused real contract used by "
            "project pipelines."
        ),
    )
    parser.add_argument(
        "--project-only",
        action="store_true",
        help="Run only project tests (skip infrastructure tests)",
    )
    parser.add_argument(
        "--include-ollama-tests",
        action="store_true",
        help="Include Ollama-dependent tests (requires Ollama server running)",
    )
    parser.add_argument(
        "--all-projects",
        action="store_true",
        help=(
            "When combined with --project-only, run every discovered "
            "projects/<name>/tests/ via infrastructure.core.test_runner "
            "(one pytest process per project; combined coverage gate at end). "
            "This mirrors the open-coded loop in .github/workflows/ci.yml."
        ),
    )
    parser.add_argument(
        "--public-projects",
        action="store_true",
        help=(
            "When combined with --project-only --all-projects, restrict the "
            "per-project loop to infrastructure.project.public_scope. Use this "
            "for public-repo release validation in checkouts that also symlink "
            "private or rotating local projects."
        ),
    )
    parser.add_argument(
        "--parallel",
        "-n",
        metavar="WORKERS",
        default=None,
        help=(
            "Opt into pytest-xdist parallelism: 'auto' (one worker per core) or "
            "a positive integer. Default is serial. Also honours the "
            "PYTEST_XDIST_WORKERS env var. On loaded dev machines prefer a fixed "
            "count (e.g. -n 6) over 'auto' to avoid wall-clock timeout flakiness."
        ),
    )
    args = parser.parse_args()

    # Validate mutually exclusive flags
    if args.infra_only and args.project_only:
        parser.error("--infra-only and --project-only cannot be used together")
    if args.public_projects and not (args.project_only and args.all_projects):
        parser.error("--public-projects requires --project-only --all-projects")

    quiet = args.quiet

    # Determine execution mode based on flags
    run_infra = not args.project_only  # Run infra unless --project-only specified
    run_project = not args.infra_only  # Run project unless --infra-only specified

    log_header(f"STAGE 01: Run Tests (Project: {args.project})", logger)

    # Log resource usage at start
    log_live_resource_usage("Test stage start", logger)

    # NOTE: ``scripts/`` is *not* the repo root — this script lives at
    # ``scripts/pipeline/stage_01_test.py`` (two levels deep).  Use the same
    # ``parents[2]`` resolution as the sys.path bootstrap on line 27 so
    # ``resolve_project_root`` gets the real repo root, not ``scripts/``.
    # The old ``Path(__file__).parent.parent`` resolved to ``scripts/``,
    # which made ``resolve_project_root`` prepend ``scripts/`` to every
    # project path (e.g. ``scripts/projects/templates/<name>/tests``),
    # causing 0 tests discovered for all templates.
    repo_root = Path(__file__).resolve().parents[2]
    strict = not args.non_strict

    # If the default placeholder project is selected but isn't a runnable project,
    # pick the first discovered runnable project (has src/ and tests/).
    from infrastructure.project.discovery import resolve_project_root

    project_root = resolve_project_root(repo_root, args.project)
    if args.project == "project" and (not (project_root / "src").exists() or not (project_root / "tests").exists()):
        try:
            from infrastructure.project.discovery import discover_projects

            discovered = discover_projects(repo_root)
            runnable = [p for p in discovered if (p.path / "src").exists() and (p.path / "tests").exists()]
            if runnable:
                args.project = runnable[0].name
                log_substep(f"Default project placeholder is not runnable; using '{args.project}' instead.", logger)
        except Exception as e:
            logger.warning("Project discovery failed; continuing with project=%s (%s)", args.project, e)

    # --project-only --all-projects dispatches to the per-project runner
    # (one pytest process per project, combined coverage gate at end).
    # This is the local mirror of the bash loop in .github/workflows/ci.yml.
    if args.project_only and args.all_projects:
        marker_expr = build_pytest_marker_expression(
            skip_requires_ollama=not args.include_ollama_tests,
            skip_slow=not args.include_slow,
            skip_bench=True,
            skip_long_running=not args.include_long_running,
        )
        projects = None
        if args.public_projects:
            from infrastructure.project.public_scope import public_project_names

            projects = public_project_names(repo_root)
            log_substep(
                "Restricting all-projects test run to public scope: " + ", ".join(projects),
                logger,
            )
        exit_code = run_per_project_pytest(
            repo_root,
            projects=projects,
            marker_expr=marker_expr,
            parallel=args.parallel,
        )
        log_live_resource_usage("Test stage end", logger)
        return exit_code

    exit_code = execute_test_pipeline(
        project_name=args.project,
        repo_root=repo_root,
        run_infra=run_infra,
        run_project=run_project,
        quiet=quiet,
        include_slow=args.include_slow,
        include_long_running=args.include_long_running,
        include_ollama_tests=args.include_ollama_tests,
        strict=strict,
        infra_scope=args.infra_scope,
        parallel=args.parallel,
    )

    # Log resource usage at end
    log_live_resource_usage("Test stage end", logger)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
