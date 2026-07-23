#!/usr/bin/env python3
"""Environment setup orchestrator script.

This thin orchestrator prepares the environment for the complete project pipeline:
1. Verifies Python version and dependencies
2. Sets up directory structure
3. Configures environment variables
4. Validates build tools availability

Stage 00 of the pipeline orchestration.

Exit codes:
    0: Setup succeeded (environment ready for downstream stages)
    1: Setup failed (missing Python version, dependencies, or build tools)

These map to ``scripts.runner.exit_codes.ExitCode`` (SUCCESS=0 / FAILURE=1).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_success, log_header
from infrastructure.core.runtime.setup_checks import (
    aggregate_check_results,
    run_environment_setup_checks,
)

# Set up logger for this module
logger = get_logger(__name__)


def main() -> int:
    """Execute environment setup orchestration."""
    import argparse

    parser = argparse.ArgumentParser(description="Setup environment")
    parser.add_argument(
        "--project",
        default="project",
        help="Project name in projects/ directory (default: project)",
    )
    args = parser.parse_args()

    log_header(f"STAGE 00: Environment Setup (Project: {args.project})", logger)

    repo_root = Path(__file__).resolve().parents[2]

    results = run_environment_setup_checks(repo_root, args.project)

    # Summary
    log_header("Setup Summary", logger)

    all_passed, summary_lines = aggregate_check_results(results)
    for line in summary_lines:
        logger.info(line)

    if all_passed:
        log_success("\n✅ Environment setup complete - ready to proceed")
        return 0
    else:
        logger.error("\n❌ Environment setup failed - fix issues and try again")
        return 1


if __name__ == "__main__":
    exit(main())
