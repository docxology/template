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


def log_stage(message: str) -> None:
    """Log a stage message."""
    print(f"\n[STAGE-01] {message}")


def log_success(message: str) -> None:
    """Log a success message."""
    print(f"  ✅ {message}")


def log_error(message: str) -> None:
    """Log an error message."""
    print(f"  ❌ {message}")


def run_tests() -> int:
    """Execute pytest test suite with coverage."""
    log_stage("Running test suite with coverage analysis...")
    
    repo_root = Path(__file__).parent.parent
    test_dir = repo_root / "tests"
    
    if not test_dir.exists():
        log_error("Tests directory not found")
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
    
    print(f"\nExecuting: {' '.join(cmd)}\n")
    
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
        log_error(f"Failed to run tests: {e}")
        return 1


def report_results(exit_code: int) -> None:
    """Report test execution results."""
    print("\n" + "="*60)
    print("Test Execution Summary")
    print("="*60)
    
    if exit_code == 0:
        log_success("All tests passed")
        log_success("Coverage threshold met (70%+)")
        print("\n✅ Tests complete - ready for analysis")
    else:
        log_error("Test suite failed")
        print("\n❌ Tests failed - fix issues and try again")


def main() -> int:
    """Execute test suite orchestration."""
    print("\n" + "="*60)
    print("STAGE 01: Run Tests")
    print("="*60)
    
    exit_code = run_tests()
    report_results(exit_code)
    
    return exit_code


if __name__ == "__main__":
    exit(main())

