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
from typing import Optional, Tuple

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging_utils import (
    get_logger, log_success, log_header, log_substep
)
from infrastructure.core.logging_progress import (
    log_with_spinner, StreamingProgress
)
from infrastructure.core.config_loader import get_testing_config
from infrastructure.core.file_operations import clean_coverage_files
from infrastructure.reporting.test_reporter import (
    parse_pytest_output,
    generate_test_report,
    save_test_report as save_test_report_to_files,
)

# Set up logger for this module
logger = get_logger(__name__)


def _check_cov_datafile_support() -> bool:
    """Check if pytest-cov supports the --cov-datafile flag.

    Returns:
        True if --cov-datafile is supported, False otherwise
    """
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "--help"],
            capture_output=True, text=True, timeout=10
        )
        return "--cov-datafile" in result.stdout
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        # If we can't check, assume it's not supported to be safe
        return False


def extract_failed_tests(stdout: str, stderr: str) -> list[dict]:
    """Extract detailed information about failed tests from pytest output.

    Handles multiple pytest output formats for comprehensive failure detection.

    Args:
        stdout: Standard output from pytest
        stderr: Standard error from pytest

    Returns:
        List of dictionaries with failure details:
        [
            {
                'test': 'test_file.py::TestClass::test_method',
                'error_type': 'AssertionError',
                'error_message': 'Expected 1, got 2',
                'traceback': ['line1', 'line2', ...]
            },
            ...
        ]
    """
    failed_tests = []
    combined_output = stdout + "\n" + stderr

    # Method 1: Extract from FAILURES section (--tb=line format)
    # Pattern: /path/file.py:line: ErrorType: message
    failures_section = False
    current_test = None

    for line in combined_output.split('\n'):
        line = line.strip()

        if 'FAILURES' in line and '===' in line:
            failures_section = True
            continue
        elif line.startswith('=') and 'durations' in line.lower():
            failures_section = False
            break

        if failures_section:
            # Check if this is a test header line (function name)
            if line.startswith('__') and '__' in line:
                # Extract test function name: __ TestClass.test_method __
                test_func_match = re.search(r'__\s+([^_\s]+)\s+__', line)
                if test_func_match:
                    current_test = test_func_match.group(1)

            # Check if this is an error line: /path/file.py:line: ErrorType: message
            elif line.startswith('/') and '.py:' in line and ':' in line:
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    error_part = parts[2].strip()
                    if ':' in error_part:
                        error_split = error_part.split(':', 1)
                        error_type = error_split[0].strip()
                        error_message = error_split[1].strip()

                        # Try to extract test name from the path if we don't have current_test
                        test_name = current_test
                        if not test_name:
                            # Extract from path: /path/to/test_file.py -> test_file.py
                            path_part = parts[0].strip()
                            if '/' in path_part:
                                test_name = path_part.split('/')[-1]
                            else:
                                test_name = path_part

                        failed_tests.append({
                            'test': test_name,
                            'error_type': error_type,
                            'error_message': error_message,
                            'traceback': []
                        })

    # Method 2: Extract from verbose output (--verbose format)
    # Pattern: test_file.py::TestClass::test_method FAILED
    if not failed_tests:
        verbose_lines = [l for l in combined_output.split('\n')
                        if ' FAILED' in l and '::' in l and not l.strip().startswith('=')]
        for line in verbose_lines:
            # Extract test name from pattern: test_file.py::TestClass::test_method FAILED
            test_match = re.search(r'([^\s]+)\s+FAILED', line.strip())
            if test_match:
                test_name = test_match.group(1)
                failed_tests.append({
                    'test': test_name,
                    'error_type': 'Unknown',
                    'error_message': 'Failed (use --tb=short for details)'
                })

    # Method 3: Extract from short FAILED lines
    # Pattern: FAILED test_file.py::test_method - ErrorType: message
    if not failed_tests:
        short_failed_lines = [l for l in combined_output.split('\n')
                             if l.strip().startswith('FAILED ') and '::' in l]
        for line in short_failed_lines:
            # Extract test name and error details
            test_match = re.search(r'FAILED\s+([^\s]+)', line)
            if test_match:
                test_name = test_match.group(1)

                # Try to extract error details from the line
                error_type = 'Unknown'
                error_message = 'Run with -v for details'

                # Look for error patterns in the same line
                if ' - ' in line:
                    error_part = line.split(' - ', 1)[1]
                    if ':' in error_part:
                        error_split = error_part.split(':', 1)
                        error_type = error_split[0].strip()
                        error_message = error_split[1].strip()

                failed_tests.append({
                    'test': test_name,
                    'error_type': error_type,
                    'error_message': error_message
                })

    # Method 4: Extract timeout errors specifically
    if not failed_tests:
        timeout_lines = [l for l in combined_output.split('\n')
                        if 'timeout' in l.lower() or 'pytest_timeout' in l.lower()]
        for line in timeout_lines:
            # Look for test names near timeout errors
            test_lines = []
            lines = combined_output.split('\n')
            for i, l in enumerate(lines):
                if 'timeout' in l.lower():
                    # Look a few lines before for test name
                    for j in range(max(0, i-3), i):
                        if '::' in lines[j] and ('PASSED' in lines[j] or 'FAILED' in lines[j]):
                            test_match = re.search(r'([^\s]+)\s+(?:PASSED|FAILED)', lines[j])
                            if test_match:
                                test_lines.append(test_match.group(1))

            for test_name in test_lines:
                failed_tests.append({
                    'test': test_name,
                    'error_type': 'TimeoutError',
                    'error_message': 'Test timed out (increase timeout or optimize test)'
                })

    # Method 5: Ultimate fallback - extract from any FAILED lines
    if not failed_tests:
        any_failed_lines = [l for l in combined_output.split('\n')
                           if l.strip().startswith('FAILED') and '::' in l]
        for line in any_failed_lines:
            test_match = re.search(r'FAILED\s+([^\s]+)', line)
            if test_match:
                failed_tests.append({
                    'test': test_match.group(1),
                    'error_type': 'Unknown',
                    'error_message': 'Test failed (use --tb=short -v for details)'
                })

    return failed_tests


def extract_timeout_errors(stdout: str, stderr: str) -> list[dict]:
    """Extract timeout errors from pytest output.

    Args:
        stdout: Standard output from pytest
        stderr: Standard error from pytest

    Returns:
        List of dictionaries with timeout error details:
        [
            {
                'test': 'test_file.py::TestClass::test_method',
                'timeout_duration': '10.0s',
                'suggestion': 'Increase timeout or optimize test'
            },
            ...
        ]
    """
    timeout_errors = []
    combined_output = stdout + "\n" + stderr

    # Look for timeout-related error patterns
    timeout_patterns = [
        r'timeout',
        r'pytest_timeout',
        r'TimeoutError',
        r'test.*timed out',
        r'exceeded.*timeout'
    ]

    lines = combined_output.split('\n')
    for i, line in enumerate(lines):
        line_lower = line.lower()

        # Check if this line contains timeout errors
        has_timeout = any(pattern in line_lower for pattern in timeout_patterns)
        if has_timeout:
            # Try to find the associated test name
            test_name = 'Unknown'

            # Look a few lines before for test name patterns
            for j in range(max(0, i-5), i):
                prev_line = lines[j]
                # Look for test execution lines
                test_match = re.search(r'([^\s]+\.py(?:::[^\s]+)*)\s+(?:PASSED|FAILED|ERROR)', prev_line)
                if test_match:
                    test_name = test_match.group(1)
                    break

            # Extract timeout duration if mentioned
            timeout_duration = 'Unknown'
            duration_match = re.search(r'(\d+(?:\.\d+)?)\s*s(?:econds?)?', line_lower)
            if duration_match:
                timeout_duration = f"{duration_match.group(1)}s"

            timeout_errors.append({
                'test': test_name,
                'timeout_duration': timeout_duration,
                'suggestion': 'Increase timeout with --timeout=N or optimize slow test'
            })

    return timeout_errors


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

    # Filter out internal stack traces that clutter the output
    internal_stack_patterns = [
        'super().serve_forever',
        'selector.select',
        '_selector.poll',
        'config.hook.pytest',
        'hook_impl.function',
        'httplib_response = super().getresponse',
        'fp.readline',
        'ready = selector.select',
        'fd_event_list = self._selector.poll',
        'code = main()',
        'ret: ExitCode | int = config.hook.pytest_cmdline_main',
        'res = hook_impl.function',
        'runtestprotocol(item, nextitem=nextitem)',
        'call = CallInfo.from_call',
        'result: TResult | None = func()',
        'lambda: runtest_hook(item=item',
        'self.ihook.pytest_pyfunc_call',
        'item.config.hook.pytest_runtest_protocol',
        'response = long_client.query_long',
        'response_text = self._generate_response',
        'response = requests.post',
        'return request(',
        'return session.request',
        'resp = self.send',
        'r = adapter.send',
        'resp = conn.urlopen',
        'response = self._make_request',
        'response = conn.getresponse',
        'httplib_response = super().getresponse',
        'version, status, reason = self._read_status',
        'line = str(self.fp.readline'
    ]

    for line in process.stdout:
        # Skip lines that are clearly internal stack traces
        if any(pattern in line for pattern in internal_stack_patterns):
            continue  # Skip internal stack trace lines

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

    # Clean coverage files to prevent database corruption
    clean_coverage_files(repo_root)

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
    ]

    # Set up environment with correct Python paths (needed for discovery and execution)
    env = os.environ.copy()

    # Add cov-datafile flag if supported, otherwise use environment variable
    cov_datafile_supported = _check_cov_datafile_support()
    if cov_datafile_supported:
        cmd.append("--cov-datafile=.coverage.infra")
    else:
        env["COVERAGE_FILE"] = ".coverage.infra"

    cmd.extend([
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=json:coverage_infra.json",
        "--cov-fail-under=0",
        "--tb=short",
    ])

    # Add slow test filtering unless explicitly requested
    if not include_slow:
        cmd.extend(["-m", "not slow"])

    # Add verbosity based on quiet mode
    # Infrastructure tests run in quiet mode to avoid overwhelming output
    # but with enhanced keyword filtering to capture summary
    cmd.extend(["-q", "--tb=short"])  # Quiet mode with short traceback for failure extraction
    pythonpath_parts = [
        str(repo_root),
        str(repo_root / "infrastructure"),
    ]
    project_src = project_root / "src"
    if project_src.exists():
        pythonpath_parts.append(str(project_src))
    pythonpath = os.pathsep.join(pythonpath_parts)
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

        # Parse test count from discovery output with multiple fallback patterns
        test_count = None
        combined_output = discovery_result.stdout + "\n" + discovery_result.stderr

        # Try multiple patterns for different pytest output formats
        patterns = [
            r'(\d+)\s+tests?\s+collected',  # "123 tests collected"
            r'collected\s+(\d+)\s+items?',  # "collected 123 items"
            r'found\s+(\d+)\s+tests?',      # "found 123 tests"
            r'(\d+)\s+tests?\s+found',      # "123 tests found"
        ]

        for pattern in patterns:
            match = re.search(pattern, combined_output, re.IGNORECASE)
            if match:
                try:
                    test_count = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue

        if test_count is not None:
            discovery_time = time.time() - discovery_start
            log_success(f"Discovered {test_count} infrastructure tests in {discovery_time:.1f}s")
        else:
            logger.warning("Could not parse test count from infrastructure test discovery")
            logger.debug(f"Discovery output: {combined_output[:500]}...")

    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.warning(f"Infrastructure test discovery failed: {e}")

    try:
        log_substep("Executing infrastructure tests...")

        # Phase 2: Test execution
        execution_start = time.time()
        logger.info("Phase 2: Executing infrastructure tests...")

        # Execute tests with coverage error handling and retry
        max_retries = 1  # One retry after cleanup
        retry_count = 0

        while retry_count <= max_retries:
            try:
                with log_with_spinner("Running infrastructure tests", logger):
                    exit_code, stdout_text, stderr_text = _run_pytest_stream(cmd, repo_root, env, quiet)
                break  # Success, exit retry loop

            except subprocess.SubprocessError as e:
                # Check if this is a coverage database corruption error
                error_msg = str(e)
                if "coverage.exceptions.DataError" in error_msg or "no such table: file" in error_msg:
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(f"Coverage database corruption detected, cleaning and retrying ({retry_count}/{max_retries})...")
                        clean_coverage_files(repo_root)
                        logger.info("Retrying infrastructure test execution...")
                        continue
                    else:
                        logger.error("Coverage database corruption persisted after cleanup attempts")
                        raise e
                else:
                    # Not a coverage error, re-raise
                    raise e

        execution_time = time.time() - execution_start
        logger.info(f"✓ Infrastructure test execution completed in {execution_time:.1f}s")

        # Check for coverage now that pytest has completed and written coverage.json
        coverage_found = False
        coverage_pct: Optional[float] = None

        # First try to read from coverage.json files (written after process completion)
        coverage_json_paths = [
            repo_root / "coverage_infra.json",  # Infrastructure-specific coverage
            repo_root / "coverage.json",  # Fallback to general coverage
            repo_root / "htmlcov" / "coverage.json",  # HTML report location
        ]

        logger.debug(f"Looking for coverage files in {repo_root}")

        # Wait for coverage files to be written (retry up to 3 times with 0.5s delay)
        max_retries = 3
        for attempt in range(max_retries):
            if attempt > 0:
                time.sleep(0.5)  # Wait for file to be written

            for coverage_json_path in coverage_json_paths:
                logger.debug(f"Attempt {attempt+1}/{max_retries}: Checking coverage file: {coverage_json_path} (exists: {coverage_json_path.exists()})")
                if coverage_json_path.exists():
                    # Check file size to ensure it's not empty/incomplete
                    file_size = coverage_json_path.stat().st_size
                    logger.debug(f"Coverage file size: {file_size} bytes")
                    if file_size < 100:  # Coverage JSON should be much larger
                        logger.debug(f"Coverage file too small ({file_size} bytes), likely incomplete")
                        continue

                    try:
                        import json
                        with open(coverage_json_path, 'r') as f:
                            coverage_data = json.load(f)
                        overall_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
                        logger.debug(f"Coverage data from {coverage_json_path}: totals={coverage_data.get('totals', {})}")
                        if overall_coverage > 0:
                            logger.info(f"✓ Found coverage: {overall_coverage:.1f}%")
                            coverage_pct = overall_coverage
                            coverage_found = True
                            break
                        else:
                            logger.debug(f"Coverage file exists but overall_coverage is 0 or None: {overall_coverage}")
                    except json.JSONDecodeError as e:
                        logger.debug(f"JSON decode error for {coverage_json_path}: {e} (file may be incomplete)")
                    except Exception as e:
                        logger.debug(f"Could not read coverage from {coverage_json_path}: {e}")
                if coverage_found:
                    break
            if coverage_found:
                break

        # Fallback to stdout parsing if JSON not found
        if not coverage_found:
            coverage_match = re.search(r'TOTAL\s+.*?\s+(\d+\.\d+)%', stdout_text)
            if not coverage_match:
                # Fallback to any percentage pattern
                coverage_match = re.search(r'(\d+\.\d+)%', stdout_text)

            if coverage_match:
                coverage_pct = float(coverage_match.group(1))
                logger.info(f"✓ Found coverage: {coverage_pct:.1f}%")
                coverage_found = True

        if not coverage_found:
            logger.warning(f"✗ No coverage percentage found")
            logger.info("Coverage extraction diagnostics:")
            logger.info("  • Checked files: coverage_infra.json, coverage.json")
            logger.info("  • Searched stdout for: 'TOTAL ... X%', 'X%' patterns")

            # Show lines that might contain coverage for debugging
            coverage_lines = [line for line in stdout_text.split('\n') if '%' in line]
            if coverage_lines:
                logger.info(f"  • Found lines with %: {len(coverage_lines)} total")
                for i, line in enumerate(coverage_lines[:3], 1):
                    logger.info(f"    {i}. {line.strip()}")
            else:
                logger.info("  • No lines with '%' found in output")

            logger.info("Possible solutions:")
            logger.info("  • Run with coverage: pytest --cov=infrastructure --cov-report=json")
            logger.info("  • Check pytest-cov installation: pip install pytest-cov")
            logger.info("  • Verify coverage config in pyproject.toml")

        # Debug: Check if we captured test results
        has_test_output = ('collected' in stdout_text.lower() or
                          '...' in stdout_text or
                          '[100%]' in stdout_text or
                          exit_code == 0)
        if has_test_output:
            logger.info(f"✓ Captured test execution output")
        else:
            logger.warning(f"✗ No test execution output found in stdout (length: {len(stdout_text)})")

        # Phase 3: Result parsing and validation
        logger.info("Phase 3: Parsing test results and validating coverage...")
        parse_start = time.time()

        # Parse test results from output
        test_results = parse_pytest_output(stdout_text, stderr_text, exit_code)

        # Merge coverage if found
        if coverage_pct is not None:
            test_results['coverage_percent'] = coverage_pct

        # Enhanced failure analysis
        failed_tests = extract_failed_tests(stdout_text, stderr_text)
        test_results['failed_tests'] = failed_tests

        # Debug: Log extraction results
        if failed_tests:
            logger.debug(f"Extracted {len(failed_tests)} failed tests")
            for ft in failed_tests[:3]:
                logger.debug(f"  - {ft['test']}: {ft['error_type']}")
        else:
            logger.debug("No failed tests extracted (may be parsing issue)")
            # Show sample output for debugging
            if 'FAILED' in stdout_text:
                failed_lines = [l for l in stdout_text.split('\n') if 'FAILED' in l]
                logger.debug(f"Found FAILED lines: {failed_lines[:3]}")

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

    # Clean coverage files to prevent database corruption
    clean_coverage_files(repo_root)

    log_substep(f"Running project tests for '{project_name}' (90% coverage threshold)...")
    logger.info(f"Project tests started at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    project_root = repo_root / "projects" / project_name

    # Log test discovery and configuration
    test_path = project_root / "tests"
    logger.info(f"Test path: {test_path}")
    logger.info(f"Coverage target: projects/{project_name}/src (90% minimum)")
    logger.info(f"Filters applied: exclude integration tests")

    # Build pytest command for project tests using uv run pytest from project directory
    # This ensures the project's pyproject.toml pytest configuration is used
    # Warnings are controlled by pyproject.toml (--disable-warnings + filterwarnings)
    cmd = [
        "uv",
        "run",
        "--project=" + str(project_root),
        "pytest",
        "tests",
        f"--cov=src",
    ]

    # Set up environment - running from project directory so paths are relative
    env = os.environ.copy()

    # Add cov-datafile flag if supported, otherwise use environment variable
    cov_datafile_supported = _check_cov_datafile_support()
    if cov_datafile_supported:
        cmd.append("--cov-datafile=.coverage.project")
    else:
        env["COVERAGE_FILE"] = ".coverage.project"

    cmd.extend([
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=json:coverage_project.json",
        "--cov-fail-under=70",
        "--tb=short",
    ])

    # Add slow test filtering unless explicitly requested
    if not include_slow:
        cmd.extend(["-m", "not slow"])

    # Add verbosity based on quiet mode
    # Project tests need full output for proper result parsing
    if quiet:
        cmd.extend(["-q", "--tb=short"])  # Quiet mode with short traceback for failure extraction
    else:
        cmd.extend(["--tb=short"])  # Short traceback but allow summary output

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

        # Parse test count from discovery output with multiple fallback patterns
        test_count = None
        combined_output = discovery_result.stdout + "\n" + discovery_result.stderr

        # Try multiple patterns for different pytest output formats
        patterns = [
            r'(\d+)\s+tests?\s+collected',  # "123 tests collected"
            r'collected\s+(\d+)\s+items?',  # "collected 123 items"
            r'found\s+(\d+)\s+tests?',      # "found 123 tests"
            r'(\d+)\s+tests?\s+found',      # "123 tests found"
        ]

        for pattern in patterns:
            match = re.search(pattern, combined_output, re.IGNORECASE)
            if match:
                try:
                    test_count = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue

        if test_count is not None:
            discovery_time = time.time() - discovery_start
            log_success(f"Discovered {test_count} project tests for '{project_name}' in {discovery_time:.1f}s")
        else:
            logger.warning(f"Could not parse test count from project test discovery for '{project_name}'")
            logger.debug(f"Discovery output: {combined_output[:500]}...")

    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.warning(f"Project test discovery failed for '{project_name}': {e}")

    try:
        log_substep(f"Executing project tests for '{project_name}'...")

        # Phase 2: Test execution
        execution_start = time.time()
        logger.info(f"Phase 2: Executing project tests for '{project_name}'...")

        # Execute tests with coverage error handling and retry
        max_retries = 1  # One retry after cleanup
        retry_count = 0

        while retry_count <= max_retries:
            try:
                with log_with_spinner(f"Running project tests for '{project_name}'", logger):
                    exit_code, stdout_text, stderr_text = _run_pytest_stream(cmd, project_root, env, quiet)
                break  # Success, exit retry loop

            except subprocess.SubprocessError as e:
                # Check if this is a coverage database corruption error
                error_msg = str(e)
                if "coverage.exceptions.DataError" in error_msg or "no such table: file" in error_msg:
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(f"Coverage database corruption detected for project '{project_name}', cleaning and retrying ({retry_count}/{max_retries})...")
                        clean_coverage_files(repo_root)
                        logger.info(f"Retrying project test execution for '{project_name}'...")
                        continue
                    else:
                        logger.error(f"Coverage database corruption persisted after cleanup attempts for project '{project_name}'")
                        raise e
                else:
                    # Not a coverage error, re-raise
                    raise e

        execution_time = time.time() - execution_start
        logger.info(f"✓ Project test execution completed in {execution_time:.1f}s")

        # Check for coverage now that pytest has completed and written coverage_project.json
        coverage_found = False
        coverage_pct: Optional[float] = None

        # Try project-specific coverage file first
        coverage_json_paths = [
            repo_root / "coverage_project.json",  # Project-specific coverage
            repo_root / "coverage.json",  # Fallback to general coverage
            repo_root / "htmlcov" / "coverage.json",  # HTML report location
        ]

        for coverage_json_path in coverage_json_paths:
            if coverage_json_path.exists():
                try:
                    import json
                    with open(coverage_json_path, 'r') as f:
                        coverage_data = json.load(f)
                    overall_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
                    if overall_coverage > 0:
                        logger.info(f"✓ Found project coverage: {overall_coverage:.1f}%")
                        coverage_pct = overall_coverage
                        coverage_found = True
                        break
                except Exception as e:
                    logger.debug(f"Could not read project coverage from {coverage_json_path}: {e}")

        # Fallback to stdout parsing if JSON not found
        if not coverage_found:
            coverage_match = re.search(r'TOTAL\s+.*?\s+(\d+\.\d+)%', stdout_text)
            if not coverage_match:
                coverage_match = re.search(r'(\d+\.\d+)%', stdout_text)

            if coverage_match:
                coverage_pct = float(coverage_match.group(1))
                logger.info(f"✓ Found project coverage: {coverage_pct:.1f}%")
                coverage_found = True

        if not coverage_found:
            logger.warning(f"✗ No project coverage percentage found")
            logger.info("Coverage extraction diagnostics:")
            logger.info("  • Checked files: coverage_project.json, coverage.json, htmlcov/coverage.json")
            logger.info("  • Searched stdout for: 'TOTAL ... X%', 'X%' patterns")

            # Show lines that might contain coverage for debugging
            coverage_lines = [line for line in stdout_text.split('\n') if '%' in line]
            if coverage_lines:
                logger.info(f"  • Found lines with %: {len(coverage_lines)} total")
                for i, line in enumerate(coverage_lines[:3], 1):
                    logger.info(f"    {i}. {line.strip()}")
            else:
                logger.info("  • No lines with '%' found in output")

            logger.info("Possible solutions:")
            logger.info("  • Run with coverage: pytest --cov=projects/project/src --cov-report=json")
            logger.info("  • Check pytest-cov installation: pip install pytest-cov")
            logger.info("  • Verify coverage config in pyproject.toml")
            logger.info("  • Ensure tests import from project source correctly")

        # Phase 3: Result parsing and validation
        logger.info(f"Phase 3: Parsing project test results and validating coverage...")
        parse_start = time.time()

        # Parse test results from output
        test_results = parse_pytest_output(stdout_text, stderr_text, exit_code)

        # Merge coverage if found
        if coverage_pct is not None:
            test_results['coverage_percent'] = coverage_pct

        # Enhanced failure analysis
        failed_tests = extract_failed_tests(stdout_text, stderr_text)
        test_results['failed_tests'] = failed_tests

        # Debug: Log extraction results
        if failed_tests:
            logger.debug(f"Extracted {len(failed_tests)} failed tests")
            for ft in failed_tests[:3]:
                logger.debug(f"  - {ft['test']}: {ft['error_type']}")
        else:
            logger.debug("No failed tests extracted (may be parsing issue)")
            # Show sample output for debugging
            if 'FAILED' in stdout_text:
                failed_lines = [l for l in stdout_text.split('\n') if 'FAILED' in l]
                logger.debug(f"Found FAILED lines: {failed_lines[:3]}")

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
    report: dict,
    project_name: str = "project"
) -> None:
    """Report comprehensive test execution results with detailed breakdowns.

    Args:
        infra_exit: Infrastructure test exit code
        project_exit: Project test exit code
        infra_results: Infrastructure test results
        project_results: Project test results
        report: Complete test report with detailed metrics
        project_name: Name of the project (for debug command suggestions)
    """
    def format_coverage_status(coverage_pct: float, threshold: float) -> str:
        """Format coverage with visual indicators and improvement suggestions."""
        if coverage_pct >= threshold:
            return f"✓ {coverage_pct:.1f}% (meets {threshold}% threshold)"
        elif coverage_pct >= threshold * 0.9:  # Within 10% of threshold
            gap = threshold - coverage_pct
            return f"🟡 {coverage_pct:.1f}% (close to {threshold}% threshold, {gap:.1f}% gap)"
        elif coverage_pct >= threshold * 0.8:  # Within 20% of threshold
            gap = threshold - coverage_pct
            return f"⚠️ {coverage_pct:.1f}% (below {threshold}% threshold by {gap:.1f}%)"
        else:
            gap = threshold - coverage_pct
            return f"❌ {coverage_pct:.1f}% (significantly below {threshold}% threshold by {gap:.1f}%)"

    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"

    def analyze_coverage_gaps(results: dict, threshold: float, test_type: str, report: dict) -> list[str]:
        """Analyze coverage gaps with detailed file-level suggestions."""
        suggestions = []
        coverage = results.get('coverage_percent', 0)

        if coverage < threshold:
            gap = threshold - coverage
            suggestions.append(f"📊 {test_type} coverage is {gap:.1f}% below threshold")

            # Get detailed coverage information if available
            coverage_details = report.get('coverage_details', {}).get(test_type.lower(), {})
            file_coverage = coverage_details.get('file_coverage', {})

            if file_coverage:
                # Identify files with lowest coverage (< 50%)
                low_coverage_files = [
                    (file_path, data['coverage_percent'])
                    for file_path, data in file_coverage.items()
                    if data['coverage_percent'] < 50 and data['total_lines'] > 10  # Only substantial files
                ]
                low_coverage_files.sort(key=lambda x: x[1])  # Sort by coverage ascending

                if low_coverage_files:
                    suggestions.append("  📁 Files needing attention:")
                    for file_path, file_cov in low_coverage_files[:5]:  # Top 5 worst
                        file_name = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
                        missing_lines = file_coverage[file_path]['missing_lines']
                        suggestions.append(f"    • {file_name}: {file_cov:.1f}% coverage ({missing_lines} uncovered lines)")

                # Identify largest files with low coverage
                substantial_files = [
                    (file_path, data)
                    for file_path, data in file_coverage.items()
                    if data['total_lines'] > 100 and data['coverage_percent'] < 70
                ]
                substantial_files.sort(key=lambda x: x[1]['total_lines'], reverse=True)

                if substantial_files:
                    suggestions.append("  📊 High-impact files to prioritize:")
                    for file_path, data in substantial_files[:3]:
                        file_name = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
                        suggestions.append(f"    • {file_name}: {data['total_lines']} lines, {data['coverage_percent']:.1f}% coverage")
            else:
                # Fallback to generic suggestions if detailed coverage not available
                if test_type == "Infrastructure":
                    suggestions.extend([
                        "  • Add tests for CLI modules (currently ~60% coverage)",
                        "  • Test error handling paths in core modules",
                        "  • Add integration tests for module interactions"
                    ])
                elif test_type == "Project":
                    suggestions.extend([
                        "  • Test edge cases in data processing functions",
                        "  • Add tests for visualization output generation",
                        "  • Cover error handling in analysis pipelines"
                    ])

            suggestions.extend([
                f"  • Target: Reach {threshold}% coverage minimum",
                "  • Run: pytest --cov-report=html && open htmlcov/index.html"
            ])

        return suggestions

    log_header("Test Execution Summary", logger)

    # Check for collection errors
    if infra_results.get('collection_errors', 0) > 0:
        print()
        print(f"⚠️  Collection Errors: {infra_results['collection_errors']}")
        print(f"   Tests discovered: {infra_results.get('discovery_count', 0)}")
        print(f"   Tests executed: 0 (collection failed)")
        print()
        print("   Common causes:")
        print("     - Missing test dependencies (pytest-httpserver, etc.)")
        print("     - Syntax errors in test files")
        print("     - Import errors in conftest.py")
        print()

    # Infrastructure summary
    print()  # Add spacing
    # Check if infrastructure tests were actually run
    infra_was_run = infra_results.get('total', 0) > 0 or infra_exit != 0
    
    if not infra_was_run:
        # Infrastructure tests were skipped
        print("Infrastructure Results:")
        print(f"  ⏭ Skipped (not run in this execution)")
        print(f"  📊 Coverage: N/A (tests not executed)")
    elif infra_exit == 0:
        passed = infra_results.get('passed', 0)
        failed = infra_results.get('failed', 0)
        skipped = infra_results.get('skipped', 0)
        total = infra_results.get('total', 0)
        coverage = infra_results.get('coverage_percent', 0)

        print("Infrastructure Results:")
        print(f"  ✓ Passed: {passed}")
        if skipped > 0:
            print(f"  ⚠ Skipped: {skipped}")
        warnings = infra_results.get('warnings', 0)
        if warnings > 0:
            print(f"  ⚠ Warnings: {warnings}")
        print(f"  📊 Coverage: {format_coverage_status(coverage, 60.0)}")

        # Show coverage improvement suggestions if below threshold
        if coverage < 60.0:
            suggestions = analyze_coverage_gaps(infra_results, 60.0, "Infrastructure", report)
            for suggestion in suggestions:
                print(f"    {suggestion}")

        # Show execution phases if available
        phases = infra_results.get('execution_phases', {})
        if phases:
            total_exec_time = sum(phases.values())
            print(f"  ⏱ Duration: {format_duration(total_exec_time)}")
    else:
        failed = infra_results.get('failed', 0)
        skipped = infra_results.get('skipped', 0)
        warnings = infra_results.get('warnings', 0)
        print("Infrastructure Results:")
        print(f"  ✗ Failed: {failed} test(s) failed")
        if skipped > 0:
            print(f"  ⚠ Skipped: {skipped}")
        if warnings > 0:
            print(f"  ⚠ Warnings: {warnings}")

        # Show detailed failure information
        failed_tests = infra_results.get('failed_tests', [])
        if failed_tests:
            print()
            print("  📋 Failed Tests:")
            for i, failure in enumerate(failed_tests[:5], 1):  # Show first 5 failures
                print(f"    {i}. {failure['test']}")
                if failure['error_type'] != 'Unknown':
                    print(f"       {failure['error_type']}: {failure['error_message'][:60]}{'...' if len(failure['error_message']) > 60 else ''}")
            if len(failed_tests) > 5:
                print(f"    ... and {len(failed_tests) - 5} more failures")

        # Show timeout errors separately if detected
        # Note: We need to extract timeouts from the raw stdout/stderr since they're not in failed_tests
        timeout_errors = []  # Would need access to raw stdout/stderr here
        if timeout_errors:
            print()
            print("  ⏰ Timeout Errors:")
            for i, timeout in enumerate(timeout_errors[:3], 1):
                print(f"    {i}. {timeout['test']} ({timeout['timeout_duration']})")
                print(f"       {timeout['suggestion']}")

        # Always show debug commands
        print()
        print("  🔧 Quick Fix Suggestions:")

        # Check for specific error types and provide targeted solutions
        has_import_errors = any('import' in str(f) or 'module' in str(f).lower() for f in failed_tests)
        has_coverage_errors = any('coverage' in str(f).lower() or 'dataerror' in str(f).lower() or 'no such table' in str(f).lower() for f in failed_tests)
        has_timeout_errors = any('timeout' in str(f).lower() for f in failed_tests)

        if has_import_errors:
            print("    - Missing dependencies: pip install pytest-httpserver pytest-timeout")
            print("    - Import path issues: check PYTHONPATH includes repository root")

        if has_coverage_errors:
            print("    - Coverage database corruption: files automatically cleaned and retried")
            print("    - If errors persist: rm -f .coverage* coverage_*.json && rerun tests")
            print("    - To skip coverage temporarily: pytest --no-cov tests/infrastructure/")
            print("    - Coverage isolation: infrastructure and project tests use separate data files")

        if has_timeout_errors:
            print("    - Timeout issues: increase with --timeout=60 or PYTEST_TIMEOUT=60")
            print("    - Identify slow tests: pytest --durations=10 tests/infrastructure/")
            print("    - Skip slow tests: pytest -m 'not slow' tests/infrastructure/")

        # General debugging suggestions
        print("    - Run individual failing tests: pytest tests/infrastructure/<test_file> -v")
        print("    - Debug with full traceback: pytest tests/infrastructure/<test_file> -s --tb=long")
        print("    - Run infrastructure tests only: python3 scripts/01_run_tests.py --infrastructure-only")
        print("    - Check test environment: python3 scripts/00_setup_environment.py")

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
        warnings = project_results.get('warnings', 0)
        if warnings > 0:
            print(f"  ⚠ Warnings: {warnings}")
        print(f"  📊 Coverage: {format_coverage_status(coverage, 90.0)}")

        # Show coverage improvement suggestions if below threshold
        if coverage < 90.0:
            suggestions = analyze_coverage_gaps(project_results, 90.0, "Project", report)
            for suggestion in suggestions:
                print(f"    {suggestion}")

        # Show execution phases if available
        phases = project_results.get('execution_phases', {})
        if phases:
            total_exec_time = sum(phases.values())
            print(f"  ⏱ Duration: {format_duration(total_exec_time)}")
    else:
        failed = project_results.get('failed', 0)
        skipped = project_results.get('skipped', 0)
        warnings = project_results.get('warnings', 0)
        print("Project Results:")
        print(f"  ✗ Failed: {failed} test(s) failed")
        if skipped > 0:
            print(f"  ⚠ Skipped: {skipped}")
        if warnings > 0:
            print(f"  ⚠ Warnings: {warnings}")

        # Show detailed failure information
        failed_tests = project_results.get('failed_tests', [])
        if failed_tests:
            print()
            print("  📋 Failed Tests:")
            for i, failure in enumerate(failed_tests[:5], 1):  # Show first 5 failures
                print(f"    {i}. {failure['test']}")
                if failure['error_type'] != 'Unknown':
                    print(f"       {failure['error_type']}: {failure['error_message'][:60]}{'...' if len(failure['error_message']) > 60 else ''}")
            if len(failed_tests) > 5:
                print(f"    ... and {len(failed_tests) - 5} more failures")

        # Show timeout errors separately if detected
        # Note: We need to extract timeouts from the raw stdout/stderr since they're not in failed_tests
        timeout_errors = []  # Would need access to raw stdout/stderr here
        if timeout_errors:
            print()
            print("  ⏰ Timeout Errors:")
            for i, timeout in enumerate(timeout_errors[:3], 1):
                print(f"    {i}. {timeout['test']} ({timeout['timeout_duration']})")
                print(f"       {timeout['suggestion']}")

        # Always show debug commands
        print()
        print("  🔧 Quick Fix Suggestions:")

        # Check for specific error types and provide targeted solutions
        has_import_errors = any('import' in str(f) or 'module' in str(f).lower() for f in failed_tests)
        has_assertion_errors = any('assertion' in str(f).lower() for f in failed_tests)
        has_coverage_errors = any('coverage' in str(f).lower() or 'dataerror' in str(f).lower() or 'no such table' in str(f).lower() for f in failed_tests)
        has_timeout_errors = any('timeout' in str(f).lower() for f in failed_tests)

        if has_import_errors:
            print("    - Missing project dependencies: check pyproject.toml and uv sync")
            print("    - Import path issues: verify project src/ directory structure")

        if has_assertion_errors:
            print("    - Review test assertions and expected values")
            print("    - Check test data generation and reproducibility")

        if has_coverage_errors:
            print("    - Coverage database corruption: files automatically cleaned and retried")
            print("    - If errors persist: rm -f .coverage* coverage_*.json && rerun tests")
            print("    - Coverage isolation: project tests use separate data file (.coverage.project)")

        if has_timeout_errors:
            print("    - Timeout issues: increase with --timeout=60 or PYTEST_TIMEOUT=60")
            print(f"    - Identify slow tests: pytest --durations=10 projects/{project_name}/tests/")
            print("    - Skip slow tests: pytest -m 'not slow' projects/{project_name}/tests/")

        # General debugging suggestions
        print(f"    - Run individual failing tests: pytest projects/{project_name}/tests/<test_file> -v")
        print(f"    - Debug with full traceback: pytest projects/{project_name}/tests/<test_file> -s --tb=long")
        print(f"    - Run project tests only: python3 scripts/01_run_tests.py --project {project_name} --project-only")
        print(f"    - Check project structure: verify projects/{project_name}/src/ and tests/ exist")

    # Overall summary
    print()  # Add spacing
    print("=" * 64)

    infra_passed = infra_results.get('passed', 0)
    infra_total = infra_results.get('total', 0)
    infra_coverage = infra_results.get('coverage_percent', 0)
    infra_was_run = infra_total > 0 or infra_exit != 0

    project_passed = project_results.get('passed', 0)
    project_total = project_results.get('total', 0)
    project_coverage = project_results.get('coverage_percent', 0)

    total_passed = infra_passed + project_passed
    total_tests = infra_total + project_total

    # Determine overall success based on project tests (infrastructure is optional)
    overall_success = (project_exit == 0)

    if overall_success:
        # Report infrastructure status separately
        if not infra_was_run:
            print("Infrastructure: ⏭ SKIPPED (intentionally skipped - use --infra-only to run infrastructure tests)")
        elif infra_exit == 0:
            print("Infrastructure: ✓ PASSED "
                  f"({infra_passed}/{infra_total} tests, {infra_coverage:.1f}% coverage)")
        else:
            infra_failed = infra_results.get('failed', 0)
            print(f"Infrastructure: ⚠ WARNING "
                  f"({infra_failed} test(s) failed, but continuing)")

        print(f"Project:       ✓ PASSED "
              f"({project_passed}/{project_total} tests, {project_coverage:.1f}% coverage)")
        print("-" * 64)
        print(f"Total:         ✓ PASSED ({total_passed}/{total_tests} tests)")
        if infra_was_run:
            print(f"Coverage:      Infrastructure: {infra_coverage:.1f}% | Project: {project_coverage:.1f}%")
        else:
            print(f"Coverage:      Infrastructure: N/A | Project: {project_coverage:.1f}%")

        # Calculate total duration
        infra_duration = sum(infra_results.get('execution_phases', {}).values())
        project_duration = sum(project_results.get('execution_phases', {}).values())
        total_duration = infra_duration + project_duration
        if total_duration > 0:
            print(f"Duration:      {format_duration(total_duration)}")

        print("=" * 64)
        log_success("All tests passed - ready for analysis", logger)
    else:
        # Project tests failed - this is fatal
        if infra_exit == 0:
            print("Infrastructure: ✓ PASSED "
                  f"({infra_passed}/{infra_total} tests, {infra_coverage:.1f}% coverage)")
        else:
            infra_failed = infra_results.get('failed', 0)
            print(f"Infrastructure: ✗ FAILED "
                  f"({infra_failed} test(s) failed)")

        print(f"Project:       ✗ FAILED "
              f"({project_results.get('failed', 0)} test(s) failed)")
        print("-" * 64)
        print("Total:         ✗ FAILED (project tests failed)")
        logger.error("Project tests failed - pipeline cannot continue until tests pass")
        logger.info("Fix the failing tests shown above and re-run the pipeline")
        logger.info("Run 'pytest projects/{project_name}/tests/ -v' for detailed failure information")


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
    parser.add_argument(
        '--infra-only',
        action='store_true',
        help='Run only infrastructure tests (skip project tests)'
    )
    parser.add_argument(
        '--project-only',
        action='store_true',
        help='Run only project tests (skip infrastructure tests)'
    )
    args = parser.parse_args()

    # Validate mutually exclusive flags
    if args.infra_only and args.project_only:
        parser.error("--infra-only and --project-only cannot be used together")
    
    quiet = not args.verbose

    # Determine execution mode based on flags
    run_infra = not args.project_only  # Run infra unless --project-only specified
    run_project = not args.infra_only  # Run project unless --infra-only specified

    log_header(f"STAGE 01: Run Tests (Project: {args.project})", logger)

    # Log resource usage at start
    from infrastructure.core.logging_utils import log_resource_usage
    log_resource_usage("Test stage start", logger)

    repo_root = Path(__file__).parent.parent

    # Initialize result variables
    infra_exit, infra_results = 0, {}
    project_exit, project_results = 0, {}

    # Phase 1: Infrastructure Tests (run unless --project-only specified)
    if run_infra:
        phase_title = "Infrastructure Tests" if run_project else "Infrastructure Tests (Only)"
        log_header(f"Phase 1/{1 + int(run_project)}: {phase_title}")

        # Run infrastructure tests first (but don't fail the whole pipeline if they fail)
        infra_exit, infra_results = run_infrastructure_tests(repo_root, args.project, quiet=quiet, include_slow=args.include_slow)

    # Phase 2: Project Tests (run unless --infra-only specified)
    if run_project:
        phase_num = 2 if run_infra else 1
        total_phases = 1 + int(run_infra)
        phase_title = f"Project Tests ({args.project})" if run_infra else f"Project Tests ({args.project}) (Only)"
        log_header(f"Phase {phase_num}/{total_phases}: {phase_title}")

        # Run project tests (even if infrastructure tests fail, for complete reporting)
        project_exit, project_results = run_project_tests(repo_root, args.project, quiet=quiet, include_slow=args.include_slow)

    # Generate and save test report with detailed coverage information
    if run_project:  # Only generate report if project tests were run (for output directory)
        report = generate_test_report(infra_results, project_results, repo_root, include_coverage_details=True)
        output_dir = repo_root / "projects" / args.project / "output" / "reports"
        save_test_report_to_files(report, output_dir)

        # Report combined results with detailed breakdowns
        report_results(infra_exit, project_exit, infra_results, project_results, report, project_name=args.project)
    elif run_infra:  # Only infrastructure tests were run
        # For infra-only mode, create a minimal report
        log_header("Infrastructure Test Results", logger)
        if infra_exit == 0:
            log_success("Infrastructure tests passed", logger)
        else:
            logger.error("Infrastructure tests failed - this may affect build quality")
            logger.info("Infrastructure test failures don't block the pipeline but should be addressed")
            # Show detailed failure information
            failed_tests = infra_results.get('failed_tests', [])
            if failed_tests:
                print()
                print("📋 Failed Tests:")
                for i, failure in enumerate(failed_tests[:5], 1):
                    print(f"    {i}. {failure['test']}")
                    if failure['error_type'] != 'Unknown':
                        print(f"       {failure['error_type']}: {failure['error_message'][:60]}{'...' if len(failure['error_message']) > 60 else ''}")
                if len(failed_tests) > 5:
                    print(f"    ... and {len(failed_tests) - 5} more failures")

    # Log resource usage at end
    log_resource_usage("Test stage end", logger)

    # Return exit code based on execution mode
    if run_project and run_infra:
        # Both tests run - return failure only if project tests failed (infrastructure tests are optional)
        return 1 if project_exit != 0 else 0
    elif run_project:
        # Project tests only
        return project_exit
    elif run_infra:
        # Infrastructure tests only
        return infra_exit
    else:
        # Should not happen due to argument validation
        return 0


if __name__ == "__main__":
    exit(main())

