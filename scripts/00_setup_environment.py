#!/usr/bin/env python3
"""Environment setup orchestrator script.

This thin orchestrator prepares the environment for the complete project pipeline:
1. Verifies Python version and dependencies
2. Sets up directory structure
3. Configures environment variables
4. Validates build tools availability

Stage 1 of the pipeline orchestration.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_success, log_header
from infrastructure.core.environment import (
    check_python_version,
    check_dependencies,
    install_missing_packages,
    check_build_tools,
    setup_directories,
    verify_source_structure,
    set_environment_variables,
)

# Set up logger for this module
logger = get_logger(__name__)


def main() -> int:
    """Execute environment setup orchestration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup environment")
    parser.add_argument(
        '--project',
        default='project',
        help='Project name in projects/ directory (default: project)'
    )
    args = parser.parse_args()
    
    log_header(f"STAGE 00: Environment Setup (Project: {args.project})", logger)
    
    repo_root = Path(__file__).parent.parent
    
    def check_and_install_dependencies() -> bool:
        """Check dependencies and install missing ones if needed."""
        all_present, missing = check_dependencies()
        if not all_present and missing:
            return install_missing_packages(missing)
        return all_present
    
    checks = [
        ("Python version", lambda: check_python_version()),
        ("Dependencies", check_and_install_dependencies),
        ("Build tools", lambda: check_build_tools()),
        ("Directory structure", lambda: setup_directories(repo_root, args.project)),
        ("Source structure", lambda: verify_source_structure(repo_root, args.project)),
        ("Environment variables", lambda: set_environment_variables(repo_root)),
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

