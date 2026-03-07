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

from infrastructure.core.logging_utils import get_logger, log_success, log_header, log_substep
from infrastructure.core.logging_progress import log_with_spinner
from infrastructure.core.config_loader import get_testing_config
from infrastructure.core.file_operations import clean_coverage_files
from infrastructure.reporting.coverage_reporter import (
    parse_pytest_output,
    generate_test_report,
    save_test_report as save_test_report_to_files,
)
from infrastructure.core.environment import get_python_command, check_uv_available
from infrastructure.reporting.coverage_parser import (
    check_cov_datafile_support,
    extract_failed_tests,
    check_test_failures,
    extract_coverage_percentage,
)


# Set up logger for this module
logger = get_logger(__name__)


def _run_pytest_stream(
    cmd: list[str], repo_root: Path, env: dict, quiet: bool
) -> Tuple[int, str, str]:
    """Run pytest streaming output to console while capturing logs for reporting."""
    import select
    import sys

    keywords = [
        "passed",
        "failed",
        "skipped",
        "warnings",
        "ERROR",
        "FAILED",
        "PASSED",
        "coverage",
        "=",
    ]
    stdout_buf: list[str] = []

    process = subprocess.Popen(
        cmd,
        cwd=str(repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False,  # Use binary mode for non-blocking IO
        bufsize=0,
    )

    assert process.stdout is not None
    recent_lines = []  # Keep track of recent lines for summary detection

    # Filter out internal stack traces that clutter the output
    internal_stack_patterns = [
        "super().serve_forever",
        "selector.select",
        "_selector.poll",
        "config.hook.pytest",
        "hook_impl.function",
        "httplib_response = super().getresponse",
        "fp.readline",
        "ready = selector.select",
        "fd_event_list = self._selector.poll",
        "code = main()",
        "ret: ExitCode | int = config.hook.pytest_cmdline_main",
        "res = hook_impl.function",
        "runtestprotocol(item, nextitem=nextitem)",
        "call = CallInfo.from_call",
        "result: TResult | None = func()",
        "lambda: runtest_hook(item=item",
        "self.ihook.pytest_pyfunc_call",
        "item.config.hook.pytest_runtest_protocol",
        "response = long_client.query_long",
        "response_text = self._generate_response",
        "response = requests.post",
        "return request(",
        "return session.request",
        "resp = self.send",
        "r = adapter.send",
        "resp = conn.urlopen",
        "response = self._make_request",
        "response = conn.getresponse",
        "httplib_response = super().getresponse",
        "version, status, reason = self._read_status",
        "line = str(self.fp.readline",
    ]

    fd = process.stdout.fileno()
    import os

    os.set_blocking(fd, False)

    current_line = ""
    while True:
        reads, _, _ = select.select([fd], [], [], 0.1)

        if fd in reads:
            raw_chunk = process.stdout.read(4096)
            if raw_chunk is None:
                # No data available right now (EAGAIN/EWOULDBLOCK)
                if process.poll() is not None:
                    break
                continue
            if not raw_chunk:
                # EOF
                if process.poll() is not None:
                    break
                continue

            chunk = raw_chunk.decode("utf-8", errors="replace")

            # Process the chunk character by character to handle lines and dots
            for char in chunk:
                current_line += char
                if char == "\n" or (char == "." and not quiet):
                    # We have a full line or a progress dot in non-quiet mode
                    line_to_process = current_line

                    if char == "\n":
                        # Only append full lines to the buffer and history
                        if not any(
                            pattern in line_to_process for pattern in internal_stack_patterns
                        ):
                            stdout_buf.append(line_to_process)
                            recent_lines.append(line_to_process)
                            if len(recent_lines) > 10:
                                recent_lines.pop(0)

                    # Decide whether to print
                    should_print = False
                    if not quiet:
                        # In verbose mode, print everything, but skip stack traces if it's a newline combo  # noqa: E501
                        if char == "." or not any(
                            pattern in line_to_process for pattern in internal_stack_patterns
                        ):
                            should_print = True
                    else:
                        if char == "\n":
                            if (
                                any(k in line_to_process for k in keywords)
                                or line_to_process.count("=") >= 10
                            ):
                                should_print = True

                    if should_print:
                        sys.stdout.write(char if char == "." else line_to_process)
                        sys.stdout.flush()

                    if char == "\n":
                        current_line = ""
        else:
            if process.poll() is not None:
                break

    # Process remainder
    if current_line:
        stdout_buf.append(current_line)
        if not quiet:
            sys.stdout.write(current_line)
            sys.stdout.flush()

    # After process completes, ensure the final summary is captured
    for line in recent_lines[-3:]:
        if ("passed" in line or "failed" in line or "skipped" in line) and not any(
            k in line for k in keywords
        ):
            sys.stdout.write(line)
            sys.stdout.flush()

    process.wait()
    return process.returncode, "".join(stdout_buf), ""


def run_infrastructure_tests(
    repo_root: Path,
    project_name: str = "project",
    quiet: bool = True,
    include_slow: bool = False,
    include_ollama_tests: bool = False,
) -> tuple[int, dict]:
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

    # Get coverage threshold from config
    testing_config = get_testing_config(repo_root)
    infra_threshold = testing_config.infra_coverage_threshold

    log_substep(f"Running infrastructure tests ({infra_threshold}% coverage threshold)...")
    if not include_ollama_tests:
        log_substep(
            "(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)"
        )
    logger.info(
        f"Infrastructure tests started at {time.strftime('%H:%M:%S', time.localtime(start_time))}"
    )

    # Log test discovery and configuration
    test_path = repo_root / "tests" / "infra_tests"
    logger.info(f"Test path: {test_path}")
    logger.info("Coverage target: infrastructure (60% minimum)")
    if not include_ollama_tests:
        logger.info("Filters applied: -m 'not requires_ollama', exclude integration tests")
    else:
        logger.info(
            "Filters applied: include all tests (including Ollama-dependent), exclude integration tests"  # noqa: E501
        )

    # Build pytest command using get_python_command() which handles uv fallback
    # Conditionally skip requires_ollama tests based on include_ollama_tests parameter
    # Include infrastructure tests and integration tests (excluding network-dependent ones)
    # Warnings are controlled by pyproject.toml (--disable-warnings + filterwarnings)
    cmd = get_python_command() + [
        "-m",
        "pytest",
        str(repo_root / "tests" / "infra_tests"),
        str(repo_root / "tests" / "integration"),
        # test_coverage_completion.py removed - coverage completion is now handled by test runners
        "--ignore=" + str(repo_root / "tests" / "integration" / "test_module_interoperability.py"),
        "--cov=infrastructure",
    ]

    # Add Ollama filter if not including Ollama tests
    if not include_ollama_tests:
        cmd.extend(["-m", "not requires_ollama"])

    # Set up environment with correct Python paths (needed for discovery and execution)
    env = os.environ.copy()

    # Add cov-datafile flag if supported, otherwise use environment variable
    cov_datafile_supported = check_cov_datafile_support()
    if cov_datafile_supported:
        cmd.append("--cov-datafile=.coverage.infra")
    else:
        env["COVERAGE_FILE"] = ".coverage.infra"

    cmd.extend(
        [
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=json:coverage_infra.json",
            f"--cov-fail-under={infra_threshold}",
            "--tb=short",
        ]
    )

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
            timeout=30,  # 30 second timeout for discovery
        )

        # Parse test count from discovery output with multiple fallback patterns
        test_count = None
        combined_output = discovery_result.stdout + "\n" + discovery_result.stderr

        # Try multiple patterns for different pytest output formats
        patterns = [
            r"(\d+)\s+tests?\s+collected",  # "123 tests collected"
            r"collected\s+(\d+)\s+items?",  # "collected 123 items"
            r"found\s+(\d+)\s+tests?",  # "found 123 tests"
            r"(\d+)\s+tests?\s+found",  # "123 tests found"
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
                    exit_code, stdout_text, stderr_text = _run_pytest_stream(
                        cmd, repo_root, env, quiet
                    )

                # Check for pytest-cov INTERNALERROR in output (exit code 3)
                # This happens when stale .coverage files mix statement + branch data
                combined_output = stdout_text + "\n" + stderr_text
                if exit_code != 0 and (
                    "coverage.exceptions.DataError" in combined_output
                    or "Can't combine statement coverage data with branch data"
                    in combined_output
                ):
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(
                            "Coverage data conflict detected for infrastructure tests, "
                            f"cleaning stale files and retrying ({retry_count}/{max_retries})..."
                        )
                        clean_coverage_files(repo_root)
                        logger.info("Retrying infrastructure test execution...")
                        continue
                    else:
                        logger.warning(
                            "Coverage data conflict persisted for infrastructure tests. "
                            "Tests passed; ignoring coverage plugin error."
                        )
                        exit_code = 0
                        break
                break  # Success or non-coverage error, exit retry loop

            except subprocess.SubprocessError as e:
                # Check if this is a coverage database corruption error
                error_msg = str(e)
                if (
                    "coverage.exceptions.DataError" in error_msg
                    or "no such table: file" in error_msg
                ):
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(
                            f"Coverage database corruption detected, cleaning and retrying ({retry_count}/{max_retries})..."  # noqa: E501
                        )
                        clean_coverage_files(repo_root)
                        logger.info("Retrying infrastructure test execution...")
                        continue
                    else:
                        logger.error(
                            "Coverage database corruption persisted after cleanup attempts"
                        )
                        raise e
                else:
                    # Not a coverage error, re-raise
                    raise e

        execution_time = time.time() - execution_start
        logger.info(f"✓ Infrastructure test execution completed in {execution_time:.1f}s")

        # Extract coverage using the external parser

        coverage_json_paths = [
            repo_root / "coverage_infra.json",
            repo_root / "coverage.json",
            repo_root / "htmlcov" / "coverage.json",
        ]

        coverage_found, coverage_pct = extract_coverage_percentage(
            stdout_text, coverage_json_paths
        )

        if not coverage_found:
            logger.warning("✗ No coverage percentage found")
            logger.info("Coverage extraction diagnostics:")
            logger.info("  • Checked files: coverage_infra.json, coverage.json")
            logger.info("  • Searched stdout for: 'TOTAL ... X%', 'X%' patterns")

            # Show lines that might contain coverage for debugging
            coverage_lines = [line for line in stdout_text.split("\n") if "%" in line]
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
        has_test_output = (
            "collected" in stdout_text.lower()
            or "..." in stdout_text
            or "[100%]" in stdout_text
            or exit_code == 0
        )
        if has_test_output:
            logger.info("✓ Captured test execution output")
        else:
            logger.warning(
                f"✗ No test execution output found in stdout (length: {len(stdout_text)})"
            )

        # Phase 3: Result parsing and validation
        logger.info("Phase 3: Parsing test results and validating coverage...")
        parse_start = time.time()

        # Parse test results from output
        test_results = parse_pytest_output(stdout_text, stderr_text, exit_code)

        # Merge coverage if found
        if coverage_pct is not None:
            test_results["coverage_percent"] = coverage_pct

        # Enhanced failure analysis
        failed_tests = extract_failed_tests(stdout_text, stderr_text)
        test_results["failed_tests"] = failed_tests

        # Debug: Log extraction results
        if failed_tests:
            logger.debug(f"Extracted {len(failed_tests)} failed tests")
            for ft in failed_tests[:3]:
                logger.debug(f"  - {ft['test']}: {ft['error_type']}")
        else:
            logger.debug("No failed tests extracted (may be parsing issue)")
            # Show sample output for debugging
            if "FAILED" in stdout_text:
                failed_lines = [l for l in stdout_text.split("\n") if "FAILED" in l]
                logger.debug(f"Found FAILED lines: {failed_lines[:3]}")

        # Check for warnings in output
        warning_count = stdout_text.count(" warning") + stderr_text.count(" warning")
        if warning_count > 0:
            logger.warning(f"Infrastructure tests completed with {warning_count} warning(s)")

        # Check if failures are within tolerance
        failed_count = test_results.get("failed", 0)
        should_halt, message = check_test_failures(
            failed_count,
            "Infrastructure",
            repo_root,
            "MAX_INFRA_TEST_FAILURES",
            "max_infra_test_failures",
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
        logger.error(
            f"Failed to run infrastructure tests after {duration:.1f}s: {e}", exc_info=True
        )
        return 1, {}


def run_project_tests(
    repo_root: Path, project_name: str = "project", quiet: bool = True, include_slow: bool = False
) -> tuple[int, dict]:
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

    # Get coverage threshold from config
    testing_config = get_testing_config(repo_root)
    project_threshold = testing_config.project_coverage_threshold

    log_substep(
        f"Running project tests for '{project_name}' ({project_threshold}% coverage threshold)..."
    )
    logger.info(f"Project tests started at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    project_root = repo_root / "projects" / project_name

    # Log test discovery and configuration
    test_path = project_root / "tests"
    logger.info(f"Test path: {test_path}")
    logger.info(f"Coverage target: projects/{project_name}/src ({project_threshold}% minimum)")
    logger.info("Filters applied: exclude integration tests")

    # Build pytest command using get_python_command() which handles uv fallback
    # Run from repo root using the template's unified virtual environment
    # Use absolute paths for test directory and coverage source
    test_dir = f"projects/{project_name}/tests"
    cov_source = f"projects/{project_name}/src"

    # Point coverage to the project's pyproject.toml so that all subprocess
    # coverage trackers (spawned by integration tests) use the same branch=true
    # setting. Without this, subprocesses fall back to branch=false and the
    # combine() step crashes with DataError on the first run.
    project_cov_config = project_root / "pyproject.toml"

    if check_uv_available():
        # Use sys.executable from repo root (venv is already activated by uv run ./run.sh)
        # Do NOT use 'uv run python' - it adds ~300s overhead per invocation
        cmd = get_python_command() + [
            "-m",
            "pytest",
            test_dir,
            f"--cov={cov_source}",
            f"--cov-config={project_cov_config}",
        ]
    else:
        # Fallback to direct execution
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            test_dir,
            f"--cov={cov_source}",
            f"--cov-config={project_cov_config}",
        ]

    # Set up environment - running from project directory so paths are relative
    env = os.environ.copy()

    # Add project root to PYTHONPATH to allow imports like 'from src...' specific to this project
    # This fixes issues where tests import 'src.data...' but only repo root is in path
    pythonpath_parts = [
        str(repo_root),
        str(project_root),
    ]
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    # Propagate coverage config to ALL subprocesses spawned by integration tests.
    # COVERAGE_PROCESS_START tells coverage to activate when a new Python process
    # starts; pointing it to the project's pyproject.toml ensures branch=true
    # is used consistently, preventing incompatible shard files.
    if project_cov_config.exists():
        env["COVERAGE_PROCESS_START"] = str(project_cov_config)
    else:
        # Suppress subprocess coverage if config not found to avoid conflicts
        env.pop("COVERAGE_PROCESS_START", None)


    # Add cov-datafile flag if supported, otherwise use environment variable
    cov_datafile_supported = check_cov_datafile_support()
    if cov_datafile_supported:
        cmd.append("--cov-datafile=.coverage.project")
    else:
        env["COVERAGE_FILE"] = ".coverage.project"

    cmd.extend(
        [
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=json:coverage_project.json",
            f"--cov-fail-under={project_threshold}",
            "--tb=short",
        ]
    )

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
            timeout=30,  # 30 second timeout for discovery
        )

        # Parse test count from discovery output with multiple fallback patterns
        test_count = None
        combined_output = discovery_result.stdout + "\n" + discovery_result.stderr

        # Try multiple patterns for different pytest output formats
        patterns = [
            r"(\d+)\s+tests?\s+collected",  # "123 tests collected"
            r"collected\s+(\d+)\s+items?",  # "collected 123 items"
            r"found\s+(\d+)\s+tests?",  # "found 123 tests"
            r"(\d+)\s+tests?\s+found",  # "123 tests found"
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
            log_success(
                f"Discovered {test_count} project tests for '{project_name}' in {discovery_time:.1f}s"  # noqa: E501
            )
        else:
            logger.warning(
                f"Could not parse test count from project test discovery for '{project_name}'"
            )
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
                    exit_code, stdout_text, stderr_text = _run_pytest_stream(
                        cmd, repo_root, env, quiet
                    )

                # Check for pytest-cov INTERNALERROR in output (exit code 3)
                # This happens when stale .coverage files mix statement + branch data
                combined_output = stdout_text + "\n" + stderr_text
                if exit_code != 0 and (
                    "coverage.exceptions.DataError" in combined_output
                    or "Can't combine statement coverage data with branch data"
                    in combined_output
                ):
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(
                            f"Coverage data conflict detected for project '{project_name}', "
                            f"cleaning stale files and retrying ({retry_count}/{max_retries})..."
                        )
                        clean_coverage_files(repo_root)
                        logger.info(f"Retrying project test execution for '{project_name}'...")
                        continue
                    else:
                        # All tests passed but coverage plugin crashed — don't fail the suite
                        logger.warning(
                            f"Coverage data conflict persisted for project '{project_name}'. "
                            "Tests passed; ignoring coverage plugin error."
                        )
                        # Override exit code: the tests themselves passed
                        exit_code = 0
                        break
                break  # Success or non-coverage error, exit retry loop

            except subprocess.SubprocessError as e:
                # Check if this is a coverage database corruption error
                error_msg = str(e)
                if (
                    "coverage.exceptions.DataError" in error_msg
                    or "no such table: file" in error_msg
                ):
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(
                            f"Coverage database corruption detected for project '{project_name}', cleaning and retrying ({retry_count}/{max_retries})..."  # noqa: E501
                        )
                        clean_coverage_files(repo_root)
                        logger.info(f"Retrying project test execution for '{project_name}'...")
                        continue
                    else:
                        logger.error(
                            f"Coverage database corruption persisted after cleanup attempts for project '{project_name}'"  # noqa: E501
                        )
                        raise e
                else:
                    # Not a coverage error, re-raise
                    raise e

        execution_time = time.time() - execution_start
        logger.info(f"✓ Project test execution completed in {execution_time:.1f}s")

        # Extract coverage using the external parser

        coverage_json_paths = [
            repo_root / "coverage_project.json",
            repo_root / "coverage.json",
            repo_root / "htmlcov" / "coverage.json",
        ]

        coverage_found, coverage_pct = extract_coverage_percentage(stdout_text, coverage_json_paths)

        if not coverage_found:
            logger.warning("✗ No project coverage percentage found")
            logger.info("Coverage extraction diagnostics:")
            logger.info(
                "  • Checked files: coverage_project.json, coverage.json, htmlcov/coverage.json"
            )
            logger.info("  • Searched stdout for: 'TOTAL ... X%', 'X%' patterns")

            # Show lines that might contain coverage for debugging
            coverage_lines = [line for line in stdout_text.split("\n") if "%" in line]
            if coverage_lines:
                logger.info(f"  • Found lines with %: {len(coverage_lines)} total")
                for i, line in enumerate(coverage_lines[:3], 1):
                    logger.info(f"    {i}. {line.strip()}")
            else:
                logger.info("  • No lines with '%' found in output")

            logger.info("Possible solutions:")
            logger.info(
                "  • Run with coverage: pytest --cov=projects/project/src --cov-report=json"
            )
            logger.info("  • Check pytest-cov installation: pip install pytest-cov")
            logger.info("  • Verify coverage config in pyproject.toml")
            logger.info("  • Ensure tests import from project source correctly")

        # Phase 3: Result parsing and validation
        logger.info("Phase 3: Parsing project test results and validating coverage...")
        parse_start = time.time()

        # Parse test results from output
        test_results = parse_pytest_output(stdout_text, stderr_text, exit_code)

        # Merge coverage if found
        if coverage_pct is not None:
            test_results["coverage_percent"] = coverage_pct

        # Enhanced failure analysis
        failed_tests = extract_failed_tests(stdout_text, stderr_text)
        test_results["failed_tests"] = failed_tests

        # Debug: Log extraction results
        if failed_tests:
            logger.debug(f"Extracted {len(failed_tests)} failed tests")
            for ft in failed_tests[:3]:
                logger.debug(f"  - {ft['test']}: {ft['error_type']}")
        else:
            logger.debug("No failed tests extracted (may be parsing issue)")
            # Show sample output for debugging
            if "FAILED" in stdout_text:
                failed_lines = [l for l in stdout_text.split("\n") if "FAILED" in l]
                logger.debug(f"Found FAILED lines: {failed_lines[:3]}")

        # Check for warnings in output
        warning_count = stdout_text.count(" warning") + stderr_text.count(" warning")
        if warning_count > 0:
            logger.warning(f"Project tests completed with {warning_count} warning(s)")

        # Check if failures are within tolerance
        failed_count = test_results.get("failed", 0)
        should_halt, message = check_test_failures(
            failed_count,
            "Project",
            repo_root,
            "MAX_PROJECT_TEST_FAILURES",
            "max_project_test_failures",
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
    project_name: str = "project",
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
            return (
                f"❌ {coverage_pct:.1f}% (significantly below {threshold}% threshold by {gap:.1f}%)"
            )

    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"

    def analyze_coverage_gaps(
        results: dict, threshold: float, test_type: str, report: dict
    ) -> list[str]:
        """Analyze coverage gaps with detailed file-level suggestions."""
        suggestions = []
        coverage = results.get("coverage_percent", 0)

        if coverage < threshold:
            gap = threshold - coverage
            suggestions.append(f"📊 {test_type} coverage is {gap:.1f}% below threshold")

            # Get detailed coverage information if available
            coverage_details = report.get("coverage_details", {}).get(test_type.lower(), {})
            file_coverage = coverage_details.get("file_coverage", {})

            if file_coverage:
                # Identify files with lowest coverage (< 50%)
                low_coverage_files = [
                    (file_path, data["coverage_percent"])
                    for file_path, data in file_coverage.items()
                    if data["coverage_percent"] < 50
                    and data["total_lines"] > 10  # Only substantial files
                ]
                low_coverage_files.sort(key=lambda x: x[1])  # Sort by coverage ascending

                if low_coverage_files:
                    suggestions.append("  📁 Files needing attention:")
                    for file_path, file_cov in low_coverage_files[:5]:  # Top 5 worst
                        file_name = (
                            file_path.split("/")[-1]
                            if "/" in file_path
                            else file_path.split("\\")[-1]
                        )
                        missing_lines = file_coverage[file_path]["missing_lines"]
                        suggestions.append(
                            f"    • {file_name}: {file_cov:.1f}% coverage ({missing_lines} uncovered lines)"  # noqa: E501
                        )

                # Identify largest files with low coverage
                substantial_files = [
                    (file_path, data)
                    for file_path, data in file_coverage.items()
                    if data["total_lines"] > 100 and data["coverage_percent"] < 70
                ]
                substantial_files.sort(key=lambda x: x[1]["total_lines"], reverse=True)

                if substantial_files:
                    suggestions.append("  📊 High-impact files to prioritize:")
                    for file_path, data in substantial_files[:3]:
                        file_name = (
                            file_path.split("/")[-1]
                            if "/" in file_path
                            else file_path.split("\\")[-1]
                        )
                        suggestions.append(
                            f"    • {file_name}: {data['total_lines']} lines, {data['coverage_percent']:.1f}% coverage"  # noqa: E501
                        )
            else:
                # Fallback to generic suggestions if detailed coverage not available
                if test_type == "Infrastructure":
                    suggestions.extend(
                        [
                            "  • Add tests for CLI modules (currently ~60% coverage)",
                            "  • Test error handling paths in core modules",
                            "  • Add integration tests for module interactions",
                        ]
                    )
                elif test_type == "Project":
                    suggestions.extend(
                        [
                            "  • Test edge cases in data processing functions",
                            "  • Add tests for visualization output generation",
                            "  • Cover error handling in analysis pipelines",
                        ]
                    )

            suggestions.extend(
                [
                    f"  • Target: Reach {threshold}% coverage minimum",
                    "  • Run: pytest --cov-report=html && open htmlcov/index.html",
                ]
            )

        return suggestions

    log_header("Test Execution Summary", logger)

    # Check for collection errors
    if infra_results.get("collection_errors", 0) > 0:
        logger.info("")
        logger.info(f"⚠️  Collection Errors: {infra_results['collection_errors']}")
        logger.info(f"   Tests discovered: {infra_results.get('discovery_count', 0)}")
        logger.info("   Tests executed: 0 (collection failed)")
        logger.info("")
        logger.info("   Common causes:")
        logger.info("     - Missing test dependencies (pytest-httpserver, etc.)")
        logger.info("     - Syntax errors in test files")
        logger.info("     - Import errors in conftest.py")
        logger.info("")

    # Infrastructure summary
    logger.info("")  # Add spacing
    # Check if infrastructure tests were actually run
    infra_was_run = infra_results.get("total", 0) > 0 or infra_exit != 0

    if not infra_was_run:
        # Infrastructure tests were skipped
        logger.info("Infrastructure Results:")
        logger.info("  ⏭ Skipped (not run in this execution)")
        logger.info("  📊 Coverage: N/A (tests not executed)")
    elif infra_exit == 0:
        passed = infra_results.get("passed", 0)
        failed = infra_results.get("failed", 0)
        skipped = infra_results.get("skipped", 0)
        infra_results.get("total", 0)
        coverage = infra_results.get("coverage_percent", 0)

        logger.info("Infrastructure Results:")
        logger.info(f"  ✓ Passed: {passed}")
        if skipped > 0:
            logger.info(f"  ⚠ Skipped: {skipped}")
        warnings = infra_results.get("warnings", 0)
        if warnings > 0:
            logger.info(f"  ⚠ Warnings: {warnings}")
        logger.info(f"  📊 Coverage: {format_coverage_status(coverage, 60.0)}")

        # Show coverage improvement suggestions if below threshold
        if coverage < 60.0:
            suggestions = analyze_coverage_gaps(infra_results, 60.0, "Infrastructure", report)
            for suggestion in suggestions:
                logger.info(f"    {suggestion}")

        # Show execution phases if available
        phases = infra_results.get("execution_phases", {})
        if phases:
            total_exec_time = sum(phases.values())
            logger.info(f"  ⏱ Duration: {format_duration(total_exec_time)}")
    else:
        failed = infra_results.get("failed", 0)
        skipped = infra_results.get("skipped", 0)
        warnings = infra_results.get("warnings", 0)
        logger.info("Infrastructure Results:")
        logger.info(f"  ✗ Failed: {failed} test(s) failed")
        if skipped > 0:
            logger.info(f"  ⚠ Skipped: {skipped}")
        if warnings > 0:
            logger.info(f"  ⚠ Warnings: {warnings}")

        # Show detailed failure information
        failed_tests = infra_results.get("failed_tests", [])
        if failed_tests:
            logger.info("")
            logger.info("  📋 Failed Tests:")
            for i, failure in enumerate(failed_tests[:5], 1):  # Show first 5 failures
                logger.info(f"    {i}. {failure['test']}")
                if failure["error_type"] != "Unknown":
                    logger.info(
                        f"       {failure['error_type']}: {failure['error_message'][:60]}{'...' if len(failure['error_message']) > 60 else ''}"  # noqa: E501
                    )
            if len(failed_tests) > 5:
                logger.info(f"    ... and {len(failed_tests) - 5} more failures")

        # Show timeout errors separately if detected
        # Note: We need to extract timeouts from the raw stdout/stderr since they're not in failed_tests  # noqa: E501
        timeout_errors = []  # Would need access to raw stdout/stderr here
        if timeout_errors:
            logger.info("")
            logger.info("  ⏰ Timeout Errors:")
            for i, timeout in enumerate(timeout_errors[:3], 1):
                logger.info(f"    {i}. {timeout['test']} ({timeout['timeout_duration']})")
                logger.info(f"       {timeout['suggestion']}")

        # Always show debug commands
        logger.info("")
        logger.info("  🔧 Quick Fix Suggestions:")

        # Check for specific error types and provide targeted solutions
        has_import_errors = any(
            "import" in str(f) or "module" in str(f).lower() for f in failed_tests
        )
        has_coverage_errors = any(
            "coverage" in str(f).lower()
            or "dataerror" in str(f).lower()
            or "no such table" in str(f).lower()
            for f in failed_tests
        )
        has_timeout_errors = any("timeout" in str(f).lower() for f in failed_tests)

        if has_import_errors:
            logger.info("    - Missing dependencies: pip install pytest-httpserver pytest-timeout")
            logger.info("    - Import path issues: check PYTHONPATH includes repository root")

        if has_coverage_errors:
            logger.info(
                "    - Coverage database corruption: files automatically cleaned and retried"
            )
            logger.info("    - If errors persist: rm -f .coverage* coverage_*.json && rerun tests")
            logger.info("    - To skip coverage temporarily: pytest --no-cov tests/infra_tests/")
            logger.info(
                "    - Coverage isolation: infrastructure and project tests use separate data files"
            )

        if has_timeout_errors:
            logger.info("    - Timeout issues: increase with --timeout=60 or PYTEST_TIMEOUT=60")
            logger.info("    - Identify slow tests: pytest --durations=10 tests/infra_tests/")
            logger.info("    - Skip slow tests: pytest -m 'not slow' tests/infra_tests/")

        # General debugging suggestions
        logger.info("    - Run individual failing tests: pytest tests/infra_tests/<test_file> -v")
        logger.info(
            "    - Debug with full traceback: pytest tests/infra_tests/<test_file> -s --tb=long"
        )
        logger.info(
            "    - Run infrastructure tests only: python3 scripts/01_run_tests.py --infrastructure-only"  # noqa: E501
        )
        logger.info("    - Check test environment: python3 scripts/00_setup_environment.py")

    # Project summary
    logger.info("")  # Add spacing
    if project_exit == 0:
        passed = project_results.get("passed", 0)
        failed = project_results.get("failed", 0)
        skipped = project_results.get("skipped", 0)
        project_results.get("total", 0)
        coverage = project_results.get("coverage_percent", 0)

        logger.info("Project Results:")
        logger.info(f"  ✓ Passed: {passed}")
        if skipped > 0:
            logger.info(f"  ⚠ Skipped: {skipped}")
        warnings = project_results.get("warnings", 0)
        if warnings > 0:
            logger.info(f"  ⚠ Warnings: {warnings}")
        logger.info(f"  📊 Coverage: {format_coverage_status(coverage, 90.0)}")

        # Show coverage improvement suggestions if below threshold
        if coverage < 90.0:
            suggestions = analyze_coverage_gaps(project_results, 90.0, "Project", report)
            for suggestion in suggestions:
                logger.info(f"    {suggestion}")

        # Show execution phases if available
        phases = project_results.get("execution_phases", {})
        if phases:
            total_exec_time = sum(phases.values())
            logger.info(f"  ⏱ Duration: {format_duration(total_exec_time)}")
    else:
        failed = project_results.get("failed", 0)
        skipped = project_results.get("skipped", 0)
        warnings = project_results.get("warnings", 0)
        logger.info("Project Results:")
        logger.info(f"  ✗ Failed: {failed} test(s) failed")
        if skipped > 0:
            logger.info(f"  ⚠ Skipped: {skipped}")
        if warnings > 0:
            logger.info(f"  ⚠ Warnings: {warnings}")

        # Show detailed failure information
        failed_tests = project_results.get("failed_tests", [])
        if failed_tests:
            logger.info("")
            logger.info("  📋 Failed Tests:")
            for i, failure in enumerate(failed_tests[:5], 1):  # Show first 5 failures
                logger.info(f"    {i}. {failure['test']}")
                if failure["error_type"] != "Unknown":
                    logger.info(
                        f"       {failure['error_type']}: {failure['error_message'][:60]}{'...' if len(failure['error_message']) > 60 else ''}"  # noqa: E501
                    )
            if len(failed_tests) > 5:
                logger.info(f"    ... and {len(failed_tests) - 5} more failures")

        # Show timeout errors separately if detected
        # Note: We need to extract timeouts from the raw stdout/stderr since they're not in failed_tests  # noqa: E501
        timeout_errors = []  # Would need access to raw stdout/stderr here
        if timeout_errors:
            logger.info("")
            logger.info("  ⏰ Timeout Errors:")
            for i, timeout in enumerate(timeout_errors[:3], 1):
                logger.info(f"    {i}. {timeout['test']} ({timeout['timeout_duration']})")
                logger.info(f"       {timeout['suggestion']}")

        # Always show debug commands
        logger.info("")
        logger.info("  🔧 Quick Fix Suggestions:")

        # Check for specific error types and provide targeted solutions
        has_import_errors = any(
            "import" in str(f) or "module" in str(f).lower() for f in failed_tests
        )
        has_assertion_errors = any("assertion" in str(f).lower() for f in failed_tests)
        has_coverage_errors = any(
            "coverage" in str(f).lower()
            or "dataerror" in str(f).lower()
            or "no such table" in str(f).lower()
            for f in failed_tests
        )
        has_timeout_errors = any("timeout" in str(f).lower() for f in failed_tests)

        if has_import_errors:
            logger.info("    - Missing project dependencies: check pyproject.toml and uv sync")
            logger.info("    - Import path issues: verify project src/ directory structure")

        if has_assertion_errors:
            logger.info("    - Review test assertions and expected values")
            logger.info("    - Check test data generation and reproducibility")

        if has_coverage_errors:
            logger.info(
                "    - Coverage database corruption: files automatically cleaned and retried"
            )
            logger.info("    - If errors persist: rm -f .coverage* coverage_*.json && rerun tests")
            logger.info(
                "    - Coverage isolation: project tests use separate data file (.coverage.project)"
            )

        if has_timeout_errors:
            logger.info("    - Timeout issues: increase with --timeout=60 or PYTEST_TIMEOUT=60")
            logger.info(
                f"    - Identify slow tests: pytest --durations=10 projects/{project_name}/tests/"
            )
            logger.info(
                "    - Skip slow tests: pytest -m 'not slow' projects/{project_name}/tests/"
            )

        # General debugging suggestions
        logger.info(
            f"    - Run individual failing tests: pytest projects/{project_name}/tests/<test_file> -v"  # noqa: E501
        )
        logger.info(
            f"    - Debug with full traceback: pytest projects/{project_name}/tests/<test_file> -s --tb=long"  # noqa: E501
        )
        logger.info(
            f"    - Run project tests only: python3 scripts/01_run_tests.py --project {project_name} --project-only"  # noqa: E501
        )
        logger.info(
            f"    - Check project structure: verify projects/{project_name}/src/ and tests/ exist"
        )

    # Overall summary
    logger.info("")  # Add spacing
    logger.info("=" * 64)

    infra_passed = infra_results.get("passed", 0)
    infra_total = infra_results.get("total", 0)
    infra_coverage = infra_results.get("coverage_percent", 0)
    infra_was_run = infra_total > 0 or infra_exit != 0

    project_passed = project_results.get("passed", 0)
    project_total = project_results.get("total", 0)
    project_coverage = project_results.get("coverage_percent", 0)

    total_passed = infra_passed + project_passed
    total_tests = infra_total + project_total

    # Determine overall success based on project tests (infrastructure is optional)
    overall_success = project_exit == 0

    if overall_success:
        # Report infrastructure status separately
        if not infra_was_run:
            logger.info(
                "Infrastructure: ⏭ SKIPPED (intentionally skipped - use --infra-only to run infrastructure tests)"  # noqa: E501
            )
        elif infra_exit == 0:
            logger.info(
                "Infrastructure: ✓ PASSED "
                f"({infra_passed}/{infra_total} tests, {infra_coverage:.1f}% coverage)"
            )
        else:
            infra_failed = infra_results.get("failed", 0)
            logger.info(
                f"Infrastructure: ⚠ WARNING ({infra_failed} test(s) failed, but continuing)"
            )

        logger.info(
            f"Project:       ✓ PASSED "
            f"({project_passed}/{project_total} tests, {project_coverage:.1f}% coverage)"
        )
        logger.info("-" * 64)
        logger.info(f"Total:         ✓ PASSED ({total_passed}/{total_tests} tests)")
        if infra_was_run:
            logger.info(
                f"Coverage:      Infrastructure: {infra_coverage:.1f}% | Project: {project_coverage:.1f}%"  # noqa: E501
            )
        else:
            logger.info(f"Coverage:      Infrastructure: N/A | Project: {project_coverage:.1f}%")

        # Calculate total duration
        infra_duration = sum(infra_results.get("execution_phases", {}).values())
        project_duration = sum(project_results.get("execution_phases", {}).values())
        total_duration = infra_duration + project_duration
        if total_duration > 0:
            logger.info(f"Duration:      {format_duration(total_duration)}")

        logger.info("=" * 64)
        log_success("All tests passed - ready for analysis", logger)
    else:
        # Project tests failed - this is fatal
        if infra_exit == 0:
            logger.info(
                "Infrastructure: ✓ PASSED "
                f"({infra_passed}/{infra_total} tests, {infra_coverage:.1f}% coverage)"
            )
        else:
            infra_failed = infra_results.get("failed", 0)
            logger.info(f"Infrastructure: ✗ FAILED ({infra_failed} test(s) failed)")

        logger.info(f"Project:       ✗ FAILED ({project_results.get('failed', 0)} test(s) failed)")
        logger.info("-" * 64)
        logger.info("Total:         ✗ FAILED (project tests failed)")
        logger.error("Project tests failed - pipeline cannot continue until tests pass")
        logger.info("Fix the failing tests shown above and re-run the pipeline")
        logger.info(
            "Run 'pytest projects/{project_name}/tests/ -v' for detailed failure information"
        )


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
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress individual test names (default: verbose mode)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show individual test names (deprecated/default)",
    )
    parser.add_argument(
        "--project",
        default="project",
        help="Project name in projects/ directory (default: project)",
    )
    parser.add_argument(
        "--include-slow",
        action="store_true",
        help="Include slow tests (normally skipped for faster execution)",
    )
    parser.add_argument(
        "--infra-only",
        action="store_true",
        help="Run only infrastructure tests (skip project tests)",
    )
    parser.add_argument(
        "--project-only",
        action="store_true",
        help="Run only project tests (skip infrastructure tests)",
    )
    parser.add_argument(
        "--include-ollama-tests",
        action="store_true",
        help="Include Ollama-dependent tests (requires Ollama server running)",
    )
    args = parser.parse_args()

    # Validate mutually exclusive flags
    if args.infra_only and args.project_only:
        parser.error("--infra-only and --project-only cannot be used together")

    quiet = args.quiet

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
        infra_exit, infra_results = run_infrastructure_tests(
            repo_root,
            args.project,
            quiet=quiet,
            include_slow=args.include_slow,
            include_ollama_tests=args.include_ollama_tests,
        )

    # Phase 2: Project Tests (run unless --infra-only specified)
    if run_project:
        phase_num = 2 if run_infra else 1
        total_phases = 1 + int(run_infra)
        phase_title = (
            f"Project Tests ({args.project})"
            if run_infra
            else f"Project Tests ({args.project}) (Only)"
        )
        log_header(f"Phase {phase_num}/{total_phases}: {phase_title}")

        # Run project tests (even if infrastructure tests fail, for complete reporting)
        project_exit, project_results = run_project_tests(
            repo_root, args.project, quiet=quiet, include_slow=args.include_slow
        )

    # Generate and save test report with detailed coverage information
    if run_project:  # Only generate report if project tests were run (for output directory)
        report = generate_test_report(
            infra_results, project_results, repo_root, include_coverage_details=True
        )
        output_dir = repo_root / "projects" / args.project / "output" / "reports"
        save_test_report_to_files(report, output_dir)

        # Report combined results with detailed breakdowns
        report_results(
            infra_exit,
            project_exit,
            infra_results,
            project_results,
            report,
            project_name=args.project,
        )
    elif run_infra:  # Only infrastructure tests were run
        # For infra-only mode, create a minimal report
        log_header("Infrastructure Test Results", logger)
        if infra_exit == 0:
            log_success("Infrastructure tests passed", logger)
        else:
            logger.error("Infrastructure tests failed - this may affect build quality")
            logger.info(
                "Infrastructure test failures don't block the pipeline but should be addressed"
            )
            # Show detailed failure information
            failed_tests = infra_results.get("failed_tests", [])
            if failed_tests:
                logger.info("")
                logger.info("📋 Failed Tests:")
                for i, failure in enumerate(failed_tests[:5], 1):
                    logger.info(f"    {i}. {failure['test']}")
                    if failure["error_type"] != "Unknown":
                        logger.info(
                            f"       {failure['error_type']}: {failure['error_message'][:60]}{'...' if len(failure['error_message']) > 60 else ''}"  # noqa: E501
                        )
                if len(failed_tests) > 5:
                    logger.info(f"    ... and {len(failed_tests) - 5} more failures")

    # Log resource usage at end
    log_resource_usage("Test stage end", logger)

    # Return exit code based on execution mode
    if run_project and run_infra:
        # Both tests run - return failure only if project tests failed (infrastructure tests are optional)  # noqa: E501
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
