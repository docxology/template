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
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_success, log_header
from infrastructure.core.runtime.environment import (
    check_python_version,
    set_environment_variables,
    setup_directories,
    verify_source_structure,
)
from infrastructure.core.runtime.env_deps import check_build_tools
from infrastructure.core.runtime.setup_checks import (
    run_optional_setup_hook,
    sync_workspace_dependencies,
    validate_project_discovery,
)
from infrastructure.core.files.coverage_cleanup import clean_coverage_files

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

    repo_root = Path(__file__).parent.parent

    # Clean coverage files to ensure clean state for subsequent test runs
    clean_coverage_files(repo_root)

    checks = [
        ("Python version", lambda: check_python_version()),
        ("Dependencies", lambda: sync_workspace_dependencies(repo_root)),
        ("Build tools", lambda: check_build_tools()),
        ("Directory structure", lambda: setup_directories(repo_root, args.project)),
        ("Source structure", lambda: verify_source_structure(repo_root, args.project)),
        ("Project discovery", lambda: validate_project_discovery(repo_root, args.project)),
        ("Environment variables", lambda: set_environment_variables(repo_root)),
        ("Project setup_hook (optional)", lambda: run_optional_setup_hook(repo_root, args.project)),
    ]

    results = []
    for check_name, check_fn in checks:
        try:
            result = check_fn()
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"Error during {check_name}: {e}")
            results.append((check_name, False))

    # Summary
    log_header("Setup Summary")

    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {check_name}")
        if not result:
            all_passed = False

    if all_passed:
        log_success("\n✅ Environment setup complete - ready to proceed")
        return 0
    else:
        logger.error("\n❌ Environment setup failed - fix issues and try again")
        return 1


if __name__ == "__main__":
    exit(main())
