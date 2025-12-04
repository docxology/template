#!/usr/bin/env python3
"""Test suite orchestrator script.

This thin orchestrator runs the complete test suite for the project:
1. Runs infrastructure tests with 49%+ coverage
2. Runs project tests with 70%+ coverage
3. Reports test results
4. Validates test infrastructure

Stage 01 of the pipeline orchestration.

Note: For separate infrastructure/project test runs, use ./run.sh which
provides an interactive menu with options 1 (infrastructure) and 2 (project).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import (
    get_logger, log_success, log_header, log_substep
)

# Set up logger for this module
logger = get_logger(__name__)


def run_infrastructure_tests(repo_root: Path) -> int:
    """Execute infrastructure test suite with coverage.
    
    Args:
        repo_root: Repository root path
        
    Returns:
        Exit code (0=success, non-zero=failure)
    """
    log_substep("Running infrastructure tests (49% coverage threshold)...")
    log_substep("(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)")
    
    # Build pytest command for infrastructure tests
    # Skip requires_ollama tests - they are slow and require external Ollama service
    # Warnings are controlled by pyproject.toml (--disable-warnings + filterwarnings)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(repo_root / "tests" / "infrastructure"),
        str(repo_root / "tests" / "test_coverage_completion.py"),
        "--ignore=" + str(repo_root / "tests" / "integration" / "test_module_interoperability.py"),
        "-m", "not requires_ollama",
        "--cov=infrastructure",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-fail-under=49",
        "-v",
        "--tb=short",
    ]
    
    try:
        # Set up environment with correct Python paths
        env = os.environ.copy()
        pythonpath = os.pathsep.join([
            str(repo_root),
            str(repo_root / "infrastructure"),
            str(repo_root / "project" / "src"),
        ])
        env["PYTHONPATH"] = pythonpath
        
        # Capture output to extract warning count
        result = subprocess.run(
            cmd, 
            cwd=str(repo_root), 
            env=env, 
            check=False,
            capture_output=True,
            text=True
        )
        
        # Print stdout and stderr
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Check for warnings in output
        warning_count = result.stdout.count(" warning") + result.stderr.count(" warning")
        if warning_count > 0:
            logger.warning(f"Infrastructure tests completed with {warning_count} warning(s)")
        
        if result.returncode == 0:
            log_success("Infrastructure tests passed", logger)
        else:
            logger.error("Infrastructure tests failed")
        
        return result.returncode
    except Exception as e:
        logger.error(f"Failed to run infrastructure tests: {e}", exc_info=True)
        return 1


def run_project_tests(repo_root: Path) -> int:
    """Execute project test suite with coverage.
    
    Args:
        repo_root: Repository root path
        
    Returns:
        Exit code (0=success, non-zero=failure)
    """
    log_substep("Running project tests (70% coverage threshold)...")
    
    # Build pytest command for project tests
    # Warnings are controlled by pyproject.toml (--disable-warnings + filterwarnings)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(repo_root / "project" / "tests"),
        "--ignore=" + str(repo_root / "project" / "tests" / "integration"),
        "--cov=project/src",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-fail-under=70",
        "-v",
        "--tb=short",
    ]
    
    try:
        # Set up environment with correct Python paths
        env = os.environ.copy()
        pythonpath = os.pathsep.join([
            str(repo_root),
            str(repo_root / "infrastructure"),
            str(repo_root / "project" / "src"),
        ])
        env["PYTHONPATH"] = pythonpath
        
        # Capture output to extract warning count
        result = subprocess.run(
            cmd, 
            cwd=str(repo_root), 
            env=env, 
            check=False,
            capture_output=True,
            text=True
        )
        
        # Print stdout and stderr
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # Check for warnings in output
        warning_count = result.stdout.count(" warning") + result.stderr.count(" warning")
        if warning_count > 0:
            logger.warning(f"Project tests completed with {warning_count} warning(s)")
        
        if result.returncode == 0:
            log_success("Project tests passed", logger)
        else:
            logger.error("Project tests failed")
        
        return result.returncode
    except Exception as e:
        logger.error(f"Failed to run project tests: {e}", exc_info=True)
        return 1


def report_results(infra_exit: int, project_exit: int) -> None:
    """Report test execution results.
    
    Args:
        infra_exit: Infrastructure test exit code
        project_exit: Project test exit code
    """
    log_header("Test Execution Summary", logger)
    
    if infra_exit == 0:
        log_success("Infrastructure tests: PASSED (49%+ coverage)", logger)
    else:
        logger.error("Infrastructure tests: FAILED")
    
    if project_exit == 0:
        log_success("Project tests: PASSED (70%+ coverage)", logger)
    else:
        logger.error("Project tests: FAILED")
    
    if infra_exit == 0 and project_exit == 0:
        log_success("All tests passed - ready for analysis", logger)
    else:
        logger.error("Some tests failed - fix issues and try again")


def main() -> int:
    """Execute test suite orchestration.
    
    Runs both infrastructure and project tests in sequence.
    
    Returns:
        Exit code (0=all tests passed, 1=any test failed)
    """
    log_header("STAGE 01: Run Tests", logger)
    
    repo_root = Path(__file__).parent.parent
    
    # Run infrastructure tests first
    infra_exit = run_infrastructure_tests(repo_root)
    
    # Run project tests (even if infrastructure tests fail, for complete reporting)
    project_exit = run_project_tests(repo_root)
    
    # Report combined results
    report_results(infra_exit, project_exit)
    
    # Return failure if any test suite failed
    if infra_exit != 0 or project_exit != 0:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())

