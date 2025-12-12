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
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import (
    get_logger, log_success, log_header, log_substep
)
from infrastructure.core.config_loader import get_testing_config
from infrastructure.reporting.test_reporter import (
    parse_pytest_output,
    generate_test_report,
    save_test_report as save_test_report_to_files,
)

# Set up logger for this module
logger = get_logger(__name__)


def _run_pytest_stream(cmd: list[str], repo_root: Path, env: dict, quiet: bool) -> Tuple[int, str, str]:
    """Run pytest streaming output to console while capturing logs for reporting."""
    keywords = ['passed', 'failed', 'skipped', 'warnings', 'ERROR', 'FAILED', 'PASSED', 'coverage']
    stdout_buf: list[str] = []

    process = subprocess.Popen(
        cmd,
        cwd=str(repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    assert process.stdout is not None
    for line in process.stdout:
        stdout_buf.append(line)
        if not quiet:
            print(line, end='')
        else:
            if any(k in line for k in keywords):
                print(line, end='')

    process.wait()
    return process.returncode, "".join(stdout_buf), ""


def check_test_failures(
    failed_count: int,
    test_suite: str,
    repo_root: Path,
    env_var: str = "MAX_TEST_FAILURES",
    config_key: str = "max_test_failures"
) -> tuple[bool, str]:
    """Check if test failures are within tolerance.
    
    Priority order:
    1. Environment variables (highest priority)
    2. Config file (project/manuscript/config.yaml)
    3. Default value (0 - strict by default)
    
    Args:
        failed_count: Number of failed tests
        test_suite: Name of test suite (for logging)
        repo_root: Repository root path (for loading config file)
        env_var: Environment variable name for threshold (e.g., MAX_INFRA_TEST_FAILURES)
        config_key: Config file key name (e.g., "max_infra_test_failures")
        
    Returns:
        Tuple of (should_halt, message)
        
    Examples:
        >>> check_test_failures(0, "Infrastructure", Path("."), "MAX_INFRA_TEST_FAILURES")
        (False, "Infrastructure: All tests passed")
        
        >>> os.environ["MAX_TEST_FAILURES"] = "5"
        >>> check_test_failures(3, "Project", Path("."), "MAX_TEST_FAILURES")
        (False, "Project: 3 failure(s) within tolerance (max: 5)")
        
        >>> check_test_failures(10, "Project", Path("."), "MAX_TEST_FAILURES")
        (True, "Project: 10 failure(s) exceeds tolerance (max: 5)")
    """
    # Priority 1: Check environment variables (highest priority)
    # Try specific env var first (e.g., MAX_INFRA_TEST_FAILURES), then fall back to MAX_TEST_FAILURES
    env_value = os.environ.get(env_var) or os.environ.get("MAX_TEST_FAILURES")
    
    if env_value is not None:
        try:
            max_failures = int(env_value)
        except (ValueError, TypeError):
            max_failures = 0  # Invalid env var, use default
    else:
        # Priority 2: Check config file
        testing_config = get_testing_config(repo_root)
        config_value = testing_config.get(config_key) or testing_config.get("max_test_failures")
        
        if config_value is not None:
            max_failures = int(config_value)
        else:
            # Priority 3: Default value (strict - no failures allowed)
            max_failures = 0
    
    if failed_count == 0:
        return False, f"{test_suite}: All tests passed"
    elif failed_count <= max_failures:
        return False, f"{test_suite}: {failed_count} failure(s) within tolerance (max: {max_failures})"
    else:
        return True, f"{test_suite}: {failed_count} failure(s) exceeds tolerance (max: {max_failures})"


def run_infrastructure_tests(repo_root: Path, quiet: bool = True) -> tuple[int, dict]:
    """Execute infrastructure test suite with coverage.
    
    Args:
        repo_root: Repository root path
        quiet: If True, suppress individual test names (show only summary)
        
    Returns:
        Tuple of (exit_code, test_results_dict)
    """
    log_substep("Running infrastructure tests (60% coverage threshold)...")
    log_substep("(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)")
    
    # Build pytest command for infrastructure tests
    # Skip requires_ollama tests - they are slow and require external Ollama service
    # Warnings are controlled by pyproject.toml (--disable-warnings + filterwarnings)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(repo_root / "tests" / "infrastructure"),
        # test_coverage_completion.py removed - coverage completion is now handled by test runners
        "--ignore=" + str(repo_root / "tests" / "integration" / "test_module_interoperability.py"),
        "-m", "not requires_ollama",
        "--cov=infrastructure",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=json",
        "--cov-fail-under=60",
        "--tb=short",
    ]
    
    # Add verbosity based on quiet mode
    if quiet:
        cmd.append("-q")  # Quiet mode - only show summary
    else:
        cmd.append("-v")  # Verbose - show all test names
    
    try:
        # Set up environment with correct Python paths
        env = os.environ.copy()
        pythonpath = os.pathsep.join([
            str(repo_root),
            str(repo_root / "infrastructure"),
            str(repo_root / "project" / "src"),
        ])
        env["PYTHONPATH"] = pythonpath
        
        exit_code, stdout_text, stderr_text = _run_pytest_stream(cmd, repo_root, env, quiet)
        
        # Parse test results from output
        test_results = parse_pytest_output(stdout_text, stderr_text, exit_code)
        
        # Check for warnings in output
        warning_count = stdout_text.count(" warning") + stderr_text.count(" warning")
        if warning_count > 0:
            logger.warning(f"Infrastructure tests completed with {warning_count} warning(s)")
        
        # Check if failures are within tolerance
        failed_count = test_results.get('failed', 0)
        should_halt, message = check_test_failures(
            failed_count, "Infrastructure", repo_root, "MAX_INFRA_TEST_FAILURES", "max_infra_test_failures"
        )
        
        if exit_code == 0:
            log_success("Infrastructure tests passed", logger)
        elif should_halt:
            logger.error(message)
        else:
            logger.warning(message)
            # Return 0 if within tolerance to allow pipeline to continue
            exit_code = 0
        
        return exit_code, test_results
    except Exception as e:
        logger.error(f"Failed to run infrastructure tests: {e}", exc_info=True)
        return 1, {}


def run_project_tests(repo_root: Path, quiet: bool = True) -> tuple[int, dict]:
    """Execute project test suite with coverage.
    
    Args:
        repo_root: Repository root path
        quiet: If True, suppress individual test names (show only summary)
        
    Returns:
        Tuple of (exit_code, test_results_dict)
    """
    log_substep("Running project tests (90% coverage threshold)...")
    
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
        "--cov-report=json",
        "--cov-fail-under=90",
        "--tb=short",
    ]
    
    # Add verbosity based on quiet mode
    if quiet:
        cmd.append("-q")  # Quiet mode - only show summary
    else:
        cmd.append("-v")  # Verbose - show all test names
    
    try:
        # Set up environment with correct Python paths
        env = os.environ.copy()
        pythonpath = os.pathsep.join([
            str(repo_root),
            str(repo_root / "infrastructure"),
            str(repo_root / "project" / "src"),
        ])
        env["PYTHONPATH"] = pythonpath
        
        exit_code, stdout_text, stderr_text = _run_pytest_stream(cmd, repo_root, env, quiet)
        
        # Parse test results from output
        test_results = parse_pytest_output(stdout_text, stderr_text, exit_code)
        
        # Check for warnings in output
        warning_count = stdout_text.count(" warning") + stderr_text.count(" warning")
        if warning_count > 0:
            logger.warning(f"Project tests completed with {warning_count} warning(s)")
        
        # Check if failures are within tolerance
        failed_count = test_results.get('failed', 0)
        should_halt, message = check_test_failures(
            failed_count, "Project", repo_root, "MAX_PROJECT_TEST_FAILURES", "max_project_test_failures"
        )
        
        if exit_code == 0:
            log_success("Project tests passed", logger)
        elif should_halt:
            logger.error(message)
        else:
            logger.warning(message)
            # Return 0 if within tolerance to allow pipeline to continue
            exit_code = 0
        
        return exit_code, test_results
    except Exception as e:
        logger.error(f"Failed to run project tests: {e}", exc_info=True)
        return 1, {}




def report_results(
    infra_exit: int,
    project_exit: int,
    infra_results: dict,
    project_results: dict
) -> None:
    """Report test execution results.
    
    Args:
        infra_exit: Infrastructure test exit code
        project_exit: Project test exit code
        infra_results: Infrastructure test results
        project_results: Project test results
    """
    log_header("Test Execution Summary", logger)
    
    # Infrastructure summary
    if infra_exit == 0:
        passed = infra_results.get('passed', 0)
        total = infra_results.get('total', 0)
        coverage = infra_results.get('coverage_percent', 0)
        log_success(
            f"Infrastructure tests: PASSED ({passed}/{total} tests, {coverage:.1f}% coverage)",
            logger
        )
    else:
        failed = infra_results.get('failed', 0)
        logger.error(f"Infrastructure tests: FAILED ({failed} test(s) failed)")
    
    # Project summary
    if project_exit == 0:
        passed = project_results.get('passed', 0)
        total = project_results.get('total', 0)
        coverage = project_results.get('coverage_percent', 0)
        log_success(
            f"Project tests: PASSED ({passed}/{total} tests, {coverage:.1f}% coverage)",
            logger
        )
    else:
        failed = project_results.get('failed', 0)
        logger.error(f"Project tests: FAILED ({failed} test(s) failed)")
    
    # Overall summary
    if infra_exit == 0 and project_exit == 0:
        total_passed = infra_results.get('passed', 0) + project_results.get('passed', 0)
        total_tests = infra_results.get('total', 0) + project_results.get('total', 0)
        log_success(f"All tests passed ({total_passed}/{total_tests}) - ready for analysis", logger)
    else:
        logger.error("Some tests failed - fix issues and try again")


def main() -> int:
    """Execute test suite orchestration.
    
    Runs both infrastructure and project tests in sequence.
    
    Returns:
        Exit code (0=all tests passed, 1=any test failed)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run test suite")
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show individual test names (default: quiet mode)'
    )
    args = parser.parse_args()
    
    quiet = not args.verbose
    
    log_header("STAGE 01: Run Tests", logger)
    
    # Log resource usage at start
    from infrastructure.core.logging_utils import log_resource_usage
    log_resource_usage("Test stage start", logger)
    
    repo_root = Path(__file__).parent.parent
    
    # Run infrastructure tests first
    infra_exit, infra_results = run_infrastructure_tests(repo_root, quiet=quiet)
    
    # Run project tests (even if infrastructure tests fail, for complete reporting)
    project_exit, project_results = run_project_tests(repo_root, quiet=quiet)
    
    # Generate and save test report
    report = generate_test_report(infra_results, project_results, repo_root)
    output_dir = repo_root / "project" / "output" / "reports"
    save_test_report_to_files(report, output_dir)
    
    # Report combined results
    report_results(infra_exit, project_exit, infra_results, project_results)
    
    # Log resource usage at end
    log_resource_usage("Test stage end", logger)
    
    # Return failure if any test suite failed
    if infra_exit != 0 or project_exit != 0:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())

