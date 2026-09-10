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
    1: Infrastructure or project tests failed
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header, log_live_resource_usage
from infrastructure.orchestration.stage_policy import (
    build_stage_01_parser,
    execute_test_stage,
    resolve_test_stage_options,
)

# Set up logger for this module
logger = get_logger(__name__)


def main() -> int:
    """Execute test suite orchestration.

    Runs both infrastructure and project tests in sequence.
    Infrastructure and project test failures are reported and fail the pipeline.

    Returns:
        Exit code (0=all requested phases passed, 1=an infrastructure or project
        phase failed)
    """
    parser = build_stage_01_parser()
    args = parser.parse_args()

    try:
        options = resolve_test_stage_options(
            profile=args.profile,
            include_slow=args.include_slow,
            include_long_running=args.include_long_running,
            include_ollama_tests=args.include_ollama_tests,
            include_bench=args.include_bench,
            infra_only=args.infra_only,
            project_only=args.project_only,
            all_projects=args.all_projects,
            public_projects=args.public_projects,
            infra_scope=args.infra_scope,
            quiet=args.quiet,
            strict=not args.non_strict,
            project_workers=args.project_workers,
            parallel=args.parallel,
            receipt_path=args.receipt,
        )
    except ValueError as exc:
        parser.error(str(exc))

    log_header(f"STAGE 01: Run Tests (Project: {args.project})", logger)

    # Log resource usage at start
    log_live_resource_usage("Test stage start", logger)

    # NOTE: ``scripts/`` is *not* the repo root — this script lives at
    # ``scripts/pipeline/stage_01_test.py`` (two levels deep).  Use the same
    # ``parents[2]`` resolution as the sys.path bootstrap above so the policy
    # layer gets the real repo root, not ``scripts/``.
    repo_root = Path(__file__).resolve().parents[2]
    exit_code = execute_test_stage(options, args.project, repo_root)

    # Log resource usage at end
    log_live_resource_usage("Test stage end", logger)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
