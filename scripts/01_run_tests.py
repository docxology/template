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
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import (
    get_logger, log_success, log_header, log_substep
)
from infrastructure.core.logging_progress import (
    log_with_spinner, StreamingProgress
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
    keywords = ['passed', 'failed', 'skipped', 'warnings', 'ERROR', 'FAILED', 'PASSED', 'coverage', '=']
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
    recent_lines = []  # Keep track of recent lines for summary detection
    for line in process.stdout:
        stdout_buf.append(line)
        recent_lines.append(line)
        if len(recent_lines) > 10:  # Keep only last 10 lines
            recent_lines.pop(0)

        if not quiet:
            print(line, end='')
        else:
            # Always print summary lines (pytest final summary with ===) and lines with keywords
            if any(k in line for k in keywords) or line.count('=') >= 10:
                print(line, end='')

    # After process completes, ensure the final summary is captured
    # Check the last few lines for summary information
    for line in recent_lines[-3:]:  # Check last 3 lines
        if ('passed' in line or 'failed' in line or 'skipped' in line) and not any(k in line for k in keywords):
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


def run_infrastructure_tests(repo_root: Path, project_name: str = "project", quiet: bool = True, include_slow: bool = False) -> tuple[int, dict]:
    """Execute infrastructure test suite with coverage.

    Args:
        repo_root: Repository root path
        project_name: Name of project in projects/ directory (default: "project")
        quiet: If True, suppress individual test names (show only summary)

    Returns:
        Tuple of (exit_code, test_results_dict)
    """
    start_time = time.time()
    project_root = repo_root / "projects" / project_name
    log_substep("Running infrastructure tests (60% coverage threshold)...")
    log_substep("(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)")
    logger.info(f"Infrastructure tests started at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    # Log test discovery and configuration
    test_path = repo_root / "tests" / "infrastructure"
    logger.info(f"Test path: {test_path}")
    logger.info(f"Coverage target: infrastructure (60% minimum)")
    logger.info(f"Filters applied: -m 'not requires_ollama', exclude integration tests")

    # Build pytest command for infrastructure tests using uv run pytest
    # Skip requires_ollama tests - they are slow and require external Ollama service
    # Include infrastructure tests and integration tests (excluding network-dependent ones)
    # Warnings are controlled by pyproject.toml (--disable-warnings + filterwarnings)
    cmd = [
        "uv",
        "run",
        "pytest",
        str(repo_root / "tests" / "infrastructure"),
        str(repo_root / "tests" / "integration"),
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

    # Add slow test filtering unless explicitly requested
    if not include_slow:
        cmd.extend(["-m", "not slow"])

    # Add verbosity based on quiet mode
    # Infrastructure tests run in quiet mode to avoid overwhelming output
    # but with enhanced keyword filtering to capture summary
    cmd.append("-q")  # Quiet mode - only show summary

    # Set up environment with correct Python paths (needed for discovery and execution)
    env = os.environ.copy()
    pythonpath = os.pathsep.join([
        str(repo_root),
        str(repo_root / "infrastructure"),
        str(project_root / "src"),
    ])
    env["PYTHONPATH"] = pythonpath

    # Ensure uv is in PATH if available
    import shutil
    if shutil.which("uv"):
        uv_path = os.path.dirname(shutil.which("uv"))
        env["PATH"] = f"{uv_path}:{env.get('PATH', '')}"

    # Phase 1: Test discovery - collect test count before execution
    discovery_start = time.time()
    discovery_cmd = cmd.copy()
    discovery_cmd.insert(-1, "--collect-only")  # Insert before verbosity flag

    log_substep("Discovering infrastructure tests...")
    try:
        discovery_result = subprocess.run(
            discovery_cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout for discovery
        )

        # Parse test count from discovery output
        test_count_match = re.search(r'(\d+)\s+tests?\s+collected', discovery_result.stdout)
        if test_count_match:
            test_count = int(test_count_match.group(1))
            discovery_time = time.time() - discovery_start
            log_success(f"Discovered {test_count} infrastructure tests in {discovery_time:.1f}s")
        else:
            logger.warning("Could not parse test count from infrastructure test discovery")

    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.warning(f"Infrastructure test discovery failed: {e}")

    try:
        log_substep("Executing infrastructure tests...")

        # Phase 2: Test execution
        execution_start = time.time()
        logger.info("Phase 2: Executing infrastructure tests...")
        with log_with_spinner("Running infrastructure tests", logger):
            exit_code, stdout_text, stderr_text = _run_pytest_stream(cmd, repo_root, env, quiet)
        execution_time = time.time() - execution_start
        logger.info(f"✓ Infrastructure test execution completed in {execution_time:.1f}s")

        # Debug: Check if we captured the summary
        if 'passed' in stdout_text.lower():
            logger.info(f"✓ Captured test summary in stdout")
            # Check for coverage
            coverage_match = re.search(r'(\d+\.\d+)%', stdout_text)
            if coverage_match:
                logger.info(f"✓ Found coverage: {coverage_match.group(1)}%")
            else:
                logger.warning(f"✗ No coverage percentage found in stdout")
                # Show lines that might contain coverage
                coverage_lines = [line for line in stdout_text.split('\n') if '%' in line]
                if coverage_lines:
                    logger.info(f"Lines with %: {coverage_lines[:3]}")
        else:
            logger.warning(f"✗ No test summary found in stdout (length: {len(stdout_text)})")

        # Phase 3: Result parsing and validation
        logger.info("Phase 3: Parsing test results and validating coverage...")
        parse_start = time.time()

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

        parse_time = time.time() - parse_start
        logger.info(f"✓ Test result parsing completed in {parse_time:.1f}s")

        duration = time.time() - start_time
        logger.info(f"✓ Infrastructure test suite completed in {duration:.1f}s")

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
        duration = time.time() - start_time
        logger.error(f"Failed to run infrastructure tests after {duration:.1f}s: {e}", exc_info=True)
        return 1, {}


def run_project_tests(repo_root: Path, project_name: str = "project", quiet: bool = True, include_slow: bool = False) -> tuple[int, dict]:
    """Execute project test suite with coverage.

    Args:
        repo_root: Repository root path
        project_name: Name of project in projects/ directory (default: "project")
        quiet: If True, suppress individual test names (show only summary)

    Returns:
        Tuple of (exit_code, test_results_dict)
    """
    start_time = time.time()
    log_substep(f"Running project tests for '{project_name}' (90% coverage threshold)...")
    logger.info(f"Project tests started at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    project_root = repo_root / "projects" / project_name

    # Log test discovery and configuration
    test_path = project_root / "tests"
    logger.info(f"Test path: {test_path}")
    logger.info(f"Coverage target: projects/{project_name}/src (90% minimum)")
    logger.info(f"Filters applied: exclude integration tests")

    # Build pytest command for project tests using uv run pytest
    # Warnings are controlled by pyproject.toml (--disable-warnings + filterwarnings)
    cmd = [
        "uv",
        "run",
        "pytest",
        str(project_root / "tests"),
        f"--cov=projects/{project_name}/src",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=json",
        "--cov-fail-under=90",
        "--tb=short",
    ]

    # Add slow test filtering unless explicitly requested
    if not include_slow:
        cmd.extend(["-m", "not slow"])

    # Add verbosity based on quiet mode
    # Infrastructure tests run in quiet mode to avoid overwhelming output
    # but with enhanced keyword filtering to capture summary
    cmd.append("-q")  # Quiet mode - only show summary

    # Set up environment with correct Python paths (needed for discovery and execution)
    env = os.environ.copy()
    pythonpath = os.pathsep.join([
        str(repo_root),
        str(repo_root / "infrastructure"),
        str(project_root / "src"),
    ])
    env["PYTHONPATH"] = pythonpath

    # Ensure uv is in PATH if available
    import shutil
    if shutil.which("uv"):
        uv_path = os.path.dirname(shutil.which("uv"))
        env["PATH"] = f"{uv_path}:{env.get('PATH', '')}"

    # Phase 1: Test discovery - collect test count before execution
    discovery_start = time.time()
    discovery_cmd = cmd.copy()
    discovery_cmd.insert(-1, "--collect-only")  # Insert before verbosity flag

    log_substep(f"Discovering project tests for '{project_name}'...")
    try:
        discovery_result = subprocess.run(
            discovery_cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout for discovery
        )

        # Parse test count from discovery output
        test_count_match = re.search(r'(\d+)\s+tests?\s+collected', discovery_result.stdout)
        if test_count_match:
            test_count = int(test_count_match.group(1))
            discovery_time = time.time() - discovery_start
            log_success(f"Discovered {test_count} project tests for '{project_name}' in {discovery_time:.1f}s")
        else:
            logger.warning(f"Could not parse test count from project test discovery for '{project_name}'")

    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.warning(f"Project test discovery failed for '{project_name}': {e}")

    try:
        log_substep(f"Executing project tests for '{project_name}'...")

        # Phase 2: Test execution
        execution_start = time.time()
        logger.info(f"Phase 2: Executing project tests for '{project_name}'...")
        with log_with_spinner(f"Running project tests for '{project_name}'", logger):
            exit_code, stdout_text, stderr_text = _run_pytest_stream(cmd, repo_root, env, quiet)
        execution_time = time.time() - execution_start
        logger.info(f"✓ Project test execution completed in {execution_time:.1f}s")

        # Phase 3: Result parsing and validation
        logger.info(f"Phase 3: Parsing project test results and validating coverage...")
        parse_start = time.time()

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

        parse_time = time.time() - parse_start
        logger.info(f"✓ Project test result parsing completed in {parse_time:.1f}s")

        duration = time.time() - start_time
        logger.info(f"✓ Project test suite completed in {duration:.1f}s")

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
        duration = time.time() - start_time
        logger.error(f"Failed to run project tests after {duration:.1f}s: {e}", exc_info=True)
        return 1, {}




def report_results(
    infra_exit: int,
    project_exit: int,
    infra_results: dict,
    project_results: dict,
    report: dict
) -> None:
    """Report comprehensive test execution results with detailed breakdowns.

    Args:
        infra_exit: Infrastructure test exit code
        project_exit: Project test exit code
        infra_results: Infrastructure test results
        project_results: Project test results
        report: Complete test report with detailed metrics
    """
    def format_coverage_status(coverage_pct: float, threshold: float) -> str:
        """Format coverage with visual indicators."""
        if coverage_pct >= threshold:
            return f"✓ {coverage_pct:.1f}% (exceeds {threshold}% threshold)"
        elif coverage_pct >= threshold * 0.8:  # 80% of threshold
            return f"⚠ {coverage_pct:.1f}% (below {threshold}% threshold)"
        else:
            return f"✗ {coverage_pct:.1f}% (below {threshold}% threshold)"

    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"

    log_header("Test Execution Summary", logger)

    # Infrastructure summary
    print()  # Add spacing
    if infra_exit == 0:
        passed = infra_results.get('passed', 0)
        failed = infra_results.get('failed', 0)
        skipped = infra_results.get('skipped', 0)
        total = infra_results.get('total', 0)
        coverage = infra_results.get('coverage_percent', 0)

        print("Infrastructure Results:")
        print(f"  ✓ Passed: {passed}")
        if skipped > 0:
            print(f"  ⚠ Skipped: {skipped}")
        print(f"  📊 Coverage: {format_coverage_status(coverage, 60.0)}")

        # Show execution phases if available
        phases = infra_results.get('execution_phases', {})
        if phases:
            total_exec_time = sum(phases.values())
            print(f"  ⏱ Duration: {format_duration(total_exec_time)}")
    else:
        failed = infra_results.get('failed', 0)
        print("Infrastructure Results:")
        print(f"  ✗ Failed: {failed} test(s) failed")

    # Project summary
    print()  # Add spacing
    if project_exit == 0:
        passed = project_results.get('passed', 0)
        failed = project_results.get('failed', 0)
        skipped = project_results.get('skipped', 0)
        total = project_results.get('total', 0)
        coverage = project_results.get('coverage_percent', 0)

        print("Project Results:")
        print(f"  ✓ Passed: {passed}")
        if skipped > 0:
            print(f"  ⚠ Skipped: {skipped}")
        print(f"  📊 Coverage: {format_coverage_status(coverage, 90.0)}")

        # Show execution phases if available
        phases = project_results.get('execution_phases', {})
        if phases:
            total_exec_time = sum(phases.values())
            print(f"  ⏱ Duration: {format_duration(total_exec_time)}")
    else:
        failed = project_results.get('failed', 0)
        print("Project Results:")
        print(f"  ✗ Failed: {failed} test(s) failed")

    # Overall summary
    print()  # Add spacing
    print("=" * 64)

    infra_passed = infra_results.get('passed', 0)
    infra_total = infra_results.get('total', 0)
    infra_coverage = infra_results.get('coverage_percent', 0)

    project_passed = project_results.get('passed', 0)
    project_total = project_results.get('total', 0)
    project_coverage = project_results.get('coverage_percent', 0)

    total_passed = infra_passed + project_passed
    total_tests = infra_total + project_total

    if infra_exit == 0 and project_exit == 0:
        print("Infrastructure: ✓ PASSED "
              f"({infra_passed}/{infra_total} tests, {infra_coverage:.1f}% coverage)")
        print(f"Project:       ✓ PASSED "
              f"({project_passed}/{project_total} tests, {project_coverage:.1f}% coverage)")
        print("-" * 64)
        print(f"Total:         ✓ PASSED ({total_passed}/{total_tests} tests)")
        print(f"Coverage:      Infrastructure: {infra_coverage:.1f}% | Project: {project_coverage:.1f}%")

        # Calculate total duration
        infra_duration = sum(infra_results.get('execution_phases', {}).values())
        project_duration = sum(project_results.get('execution_phases', {}).values())
        total_duration = infra_duration + project_duration
        if total_duration > 0:
            print(f"Duration:      {format_duration(total_duration)}")

        print("=" * 64)
        log_success("All tests passed - ready for analysis", logger)
    else:
        print("Infrastructure: ✗ FAILED "
              f"({infra_results.get('failed', 0)} test(s) failed)")
        print(f"Project:       ✗ FAILED "
              f"({project_results.get('failed', 0)} test(s) failed)")
        print("-" * 64)
        print("Total:         ✗ FAILED (some tests failed)")
        logger.error("Some tests failed - fix issues and try again")
        logger.info("Check the detailed output above for specific failure information")


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
    parser.add_argument(
        '--project',
        default='project',
        help='Project name in projects/ directory (default: project)'
    )
    parser.add_argument(
        '--include-slow',
        action='store_true',
        help='Include slow tests (normally skipped for faster execution)'
    )
    args = parser.parse_args()
    
    quiet = not args.verbose
    
    log_header(f"STAGE 01: Run Tests (Project: {args.project})", logger)
    
    # Log resource usage at start
    from infrastructure.core.logging_utils import log_resource_usage
    log_resource_usage("Test stage start", logger)
    
    repo_root = Path(__file__).parent.parent
    
    # Phase 1: Infrastructure Tests
    log_header("Phase 1/2: Infrastructure Tests")

    # Run infrastructure tests first
    infra_exit, infra_results = run_infrastructure_tests(repo_root, args.project, quiet=quiet, include_slow=args.include_slow)

    # Phase 2: Project Tests
    log_header(f"Phase 2/2: Project Tests ({args.project})")

    # Run project tests (even if infrastructure tests fail, for complete reporting)
    project_exit, project_results = run_project_tests(repo_root, args.project, quiet=quiet, include_slow=args.include_slow)
    
    # Generate and save test report with detailed coverage information
    report = generate_test_report(infra_results, project_results, repo_root, include_coverage_details=True)
    output_dir = repo_root / "projects" / args.project / "output" / "reports"
    save_test_report_to_files(report, output_dir)
    
    # Report combined results with detailed breakdowns
    report_results(infra_exit, project_exit, infra_results, project_results, report)
    
    # Log resource usage at end
    log_resource_usage("Test stage end", logger)
    
    # Return failure if any test suite failed
    if infra_exit != 0 or project_exit != 0:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())

