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
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging.utils import get_logger, log_header, log_live_resource_usage, log_substep
from infrastructure.reporting.pipeline_test_runner import execute_test_pipeline

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
        help="Show individual test names (deprecated/default)",
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
        "--infra-only",
        action="store_true",
        help="Run only infrastructure tests (skip project tests)",
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
    args = parser.parse_args()

    # Validate mutually exclusive flags
    if args.infra_only and args.project_only:
        parser.error("--infra-only and --project-only cannot be used together")

    quiet = args.quiet

    # Determine execution mode based on flags
    run_infra = not args.project_only  # Run infra unless --project-only specified
    run_project = not args.infra_only  # Run project unless --infra-only specified

    log_header(f"STAGE 01: Run Tests (Project: {args.project})", logger)

    # Log resource usage at start
    log_live_resource_usage("Test stage start", logger)

    repo_root = Path(__file__).parent.parent
    strict = not args.non_strict

    # If the default placeholder project is selected but isn't a runnable project,
    # pick the first discovered runnable project (has src/ and tests/).
    project_root = repo_root / "projects" / args.project
    if args.project == "project" and (
        not (project_root / "src").exists() or not (project_root / "tests").exists()
    ):
        try:
            from infrastructure.project.discovery import discover_projects

            discovered = discover_projects(repo_root)
            runnable = [p for p in discovered if (p.path / "src").exists() and (p.path / "tests").exists()]
            if runnable:
                args.project = runnable[0].name
                log_substep(f"Default project placeholder is not runnable; using '{args.project}' instead.", logger)
        except Exception as e:
            logger.warning("Project discovery failed; continuing with project=%s (%s)", args.project, e)

    exit_code = execute_test_pipeline(
        project_name=args.project,
        repo_root=repo_root,
        run_infra=run_infra,
        run_project=run_project,
        quiet=quiet,
        include_slow=args.include_slow,
        include_ollama_tests=args.include_ollama_tests,
        strict=strict,
    )

    # Log resource usage at end
    log_live_resource_usage("Test stage end", logger)

    return exit_code

if __name__ == "__main__":
    sys.exit(main())
