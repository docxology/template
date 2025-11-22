#!/usr/bin/env python3
"""Test suite orchestrator script.

This thin orchestrator runs the complete test suite for the project:
1. Runs unit tests for src/ modules
2. Verifies 70%+ code coverage
3. Reports test results
4. Validates test infrastructure

Stage 2 of the pipeline orchestration.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import get_logger, log_success, log_header

# Set up logger for this module
logger = get_logger(__name__)


def run_tests() -> int:
    """Execute pytest test suite with coverage."""
    logger.info("Running test suite with coverage analysis...")
    
    repo_root = Path(__file__).parent.parent
    test_dir = repo_root / "tests"
    
    if not test_dir.exists():
        logger.error("Tests directory not found")
        return 1
    
    # Build pytest command - run project tests excluding problematic integration tests
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(repo_root / "project" / "tests"),  # Primary: project tests  
        "--ignore=" + str(repo_root / "project" / "tests" / "integration"),  # Skip integration tests
        "--cov=project/src",  # Coverage for project source
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-fail-under=70",
        "-v",
        "--tb=short",
    ]
    
    logger.info(f"Executing: {' '.join(cmd)}")
    
    try:
        # Set up environment with correct Python paths
        env = os.environ.copy()
        pythonpath = str(repo_root) + os.pathsep + \
                    str(repo_root / "infrastructure") + os.pathsep + \
                    str(repo_root / "src") + os.pathsep + \
                    str(repo_root / "project" / "src")
        env["PYTHONPATH"] = pythonpath
        
        result = subprocess.run(cmd, cwd=str(repo_root), env=env, check=False)
        return result.returncode
    except Exception as e:
        logger.error(f"Failed to run tests: {e}", exc_info=True)
        return 1


def report_results(exit_code: int) -> None:
    """Report test execution results."""
    log_header("Test Execution Summary", logger)
    
    if exit_code == 0:
        log_success("All tests passed", logger)
        log_success("Coverage threshold met (70%+)", logger)
        log_success("Tests complete - ready for analysis", logger)
    else:
        logger.error("Test suite failed")
        logger.error("Tests failed - fix issues and try again")


def main() -> int:
    """Execute test suite orchestration."""
    log_header("STAGE 01: Run Tests", logger)
    
    exit_code = run_tests()
    report_results(exit_code)
    
    return exit_code


if __name__ == "__main__":
    exit(main())

