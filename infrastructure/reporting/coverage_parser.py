"""Coverage and test output parsing utilities.

This module provides parsing functions to extract coverage metrics,
failed tests strings, timeout errors, and coverage capabilities from pytest output.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Optional

from infrastructure.core.environment import get_python_command
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.config_loader import get_testing_config

logger = get_logger(__name__)


def check_cov_datafile_support() -> bool:
    """Check if pytest-cov supports the --cov-datafile flag.

    Returns:
        True if --cov-datafile is supported, False otherwise
    """
    try:
        cmd = get_python_command() + ["-m", "pytest", "--help"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
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
    failed_tests = []  # type: ignore
    combined_output = stdout + "\n" + stderr

    # Method 1: Extract from FAILURES section (--tb=line format)
    failures_section = False
    current_test = None

    for line in combined_output.split("\n"):
        line = line.strip()

        if "FAILURES" in line and "===" in line:
            failures_section = True
            continue
        elif line.startswith("=") and "durations" in line.lower():
            failures_section = False
            break

        if failures_section:
            if line.startswith("__") and "__" in line:
                test_func_match = re.search(r"__\s+([^_\s]+)\s+__", line)
                if test_func_match:
                    current_test = test_func_match.group(1)

            elif line.startswith("/") and ".py:" in line and ":" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    error_part = parts[2].strip()
                    if ":" in error_part:
                        error_split = error_part.split(":", 1)
                        error_type = error_split[0].strip()
                        error_message = error_split[1].strip()

                        test_name = current_test
                        if not test_name:
                            path_part = parts[0].strip()
                            if "/" in path_part:
                                test_name = path_part.split("/")[-1]
                            else:
                                test_name = path_part

                        failed_tests.append(
                            {
                                "test": test_name,
                                "error_type": error_type,
                                "error_message": error_message,
                                "traceback": [],
                            }
                        )

    # Method 2: Extract from verbose output (--verbose format)
    if not failed_tests:
        verbose_lines = [
            l
            for l in combined_output.split("\n")
            if " FAILED" in l and "::" in l and not l.strip().startswith("=")
        ]
        for line in verbose_lines:
            test_match = re.search(r"([^\s]+)\s+FAILED", line.strip())
            if test_match:
                test_name = test_match.group(1)
                failed_tests.append(
                    {
                        "test": test_name,
                        "error_type": "Unknown",
                        "error_message": "Failed (use --tb=short for details)",
                    }
                )

    # Method 3: Extract from short FAILED lines
    if not failed_tests:
        short_failed_lines = [
            l for l in combined_output.split("\n") if l.strip().startswith("FAILED ") and "::" in l
        ]
        for line in short_failed_lines:
            test_match = re.search(r"FAILED\s+([^\s]+)", line)
            if test_match:
                test_name = test_match.group(1)
                error_type = "Unknown"
                error_message = "Run with -v for details"

                if " - " in line:
                    error_part = line.split(" - ", 1)[1]
                    if ":" in error_part:
                        error_split = error_part.split(":", 1)
                        error_type = error_split[0].strip()
                        error_message = error_split[1].strip()

                failed_tests.append(
                    {"test": test_name, "error_type": error_type, "error_message": error_message}
                )

    # Method 4: Extract timeout errors specifically
    if not failed_tests:
        timeout_lines = [
            l
            for l in combined_output.split("\n")
            if "timeout" in l.lower() or "pytest_timeout" in l.lower()
        ]
        for line in timeout_lines:
            test_lines = []
            lines = combined_output.split("\n")
            for i, l in enumerate(lines):
                if "timeout" in l.lower():
                    for j in range(max(0, i - 3), i):
                        if "::" in lines[j] and ("PASSED" in lines[j] or "FAILED" in lines[j]):
                            test_match = re.search(r"([^\s]+)\s+(?:PASSED|FAILED)", lines[j])
                            if test_match:
                                test_lines.append(test_match.group(1))

            for test_name in test_lines:
                failed_tests.append(
                    {
                        "test": test_name,
                        "error_type": "TimeoutError",
                        "error_message": "Test timed out (increase timeout or optimize test)",
                    }
                )

    # Method 5: Ultimate fallback
    if not failed_tests:
        any_failed_lines = [
            l for l in combined_output.split("\n") if l.strip().startswith("FAILED") and "::" in l
        ]
        for line in any_failed_lines:
            test_match = re.search(r"FAILED\s+([^\s]+)", line)
            if test_match:
                failed_tests.append(
                    {
                        "test": test_match.group(1),
                        "error_type": "Unknown",
                        "error_message": "Test failed (use --tb=short -v for details)",
                    }
                )

    return failed_tests


def extract_timeout_errors(stdout: str, stderr: str) -> list[dict]:
    """Extract timeout errors from pytest output."""
    timeout_errors = []
    combined_output = stdout + "\n" + stderr

    timeout_patterns = [
        r"timeout",
        r"pytest_timeout",
        r"TimeoutError",
        r"test.*timed out",
        r"exceeded.*timeout",
    ]

    lines = combined_output.split("\n")
    for i, line in enumerate(lines):
        line_lower = line.lower()
        has_timeout = any(pattern in line_lower for pattern in timeout_patterns)
        if has_timeout:
            test_name = "Unknown"
            for j in range(max(0, i - 5), i):
                prev_line = lines[j]
                test_match = re.search(
                    r"([^\s]+\.py(?:::[^\s]+)*)\s+(?:PASSED|FAILED|ERROR)", prev_line
                )
                if test_match:
                    test_name = test_match.group(1)
                    break

            timeout_duration = "Unknown"
            duration_match = re.search(r"(\d+(?:\.\d+)?)\s*s(?:econds?)?", line_lower)
            if duration_match:
                timeout_duration = f"{duration_match.group(1)}s"

            timeout_errors.append(
                {
                    "test": test_name,
                    "timeout_duration": timeout_duration,
                    "suggestion": "Increase timeout with --timeout=N or optimize slow test",
                }
            )

    return timeout_errors


def check_test_failures(
    failed_count: int,
    test_suite: str,
    repo_root: Path,
    env_var: str = "MAX_TEST_FAILURES",
    config_key: str = "max_test_failures",
) -> tuple[bool, str]:
    """Check if test failures are within tolerance."""
    env_value = os.environ.get(env_var) or os.environ.get("MAX_TEST_FAILURES")

    if env_value is not None:
        try:
            max_failures = int(env_value)
        except (ValueError, TypeError):
            max_failures = 0
    else:
        testing_config = get_testing_config(repo_root)
        config_value = testing_config.get(config_key) or testing_config.get("max_test_failures")

        if config_value is not None:
            max_failures = int(config_value)  # type: ignore
        else:
            max_failures = 0

    if failed_count == 0:
        return False, f"{test_suite}: All tests passed"
    elif failed_count <= max_failures:
        return (
            False,
            f"{test_suite}: {failed_count} failure(s) within tolerance (max: {max_failures})",
        )
    else:
        return (
            True,
            f"{test_suite}: {failed_count} failure(s) exceeds tolerance (max: {max_failures})",
        )


def extract_coverage_percentage(
    stdout_text: str, coverage_json_paths: list[Path], is_infra: bool = False
) -> tuple[bool, Optional[float]]:
    """Extract coverage percentage from defined JSON paths or stdout fallback.

    Args:
        stdout_text: Stdout text from pytest run to act as fallback
        coverage_json_paths: List of paths to coverage JSON files to parse
        is_infra: Boolean indicating if this is an infrastructure test run, for logs

    Returns:
        tuple (coverage_found, coverage_pct)
    """
    coverage_found = False
    coverage_pct: Optional[float] = None

    if is_infra:
        logger.debug("Looking for coverage files")

    # Wait for coverage files to be written (retry up to 3 times with 0.5s delay)
    max_retries = 3
    for attempt in range(max_retries):
        if attempt > 0:
            time.sleep(0.5)  # Wait for file to be written

        for coverage_json_path in coverage_json_paths:
            if is_infra:
                logger.debug(
                    f"Attempt {attempt + 1}/{max_retries}: Checking coverage file: {coverage_json_path} (exists: {coverage_json_path.exists()})"  # noqa: E501
                )

            if coverage_json_path.exists():
                file_size = coverage_json_path.stat().st_size
                if is_infra:
                    logger.debug(f"Coverage file size: {file_size} bytes")

                if file_size < 100:  # Coverage JSON should be much larger
                    if is_infra:
                        logger.debug(
                            f"Coverage file too small ({file_size} bytes), likely incomplete"
                        )
                    continue

                try:
                    with open(coverage_json_path, "r") as f:
                        coverage_data = json.load(f)
                    overall_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
                    if is_infra:
                        logger.debug(
                            f"Coverage data from {coverage_json_path}: totals={coverage_data.get('totals', {})}"  # noqa: E501
                        )
                    if overall_coverage > 0:
                        logger.info(f"✓ Found coverage: {overall_coverage:.1f}%")
                        coverage_pct = overall_coverage
                        coverage_found = True
                        break
                    else:
                        if is_infra:
                            logger.debug(
                                f"Coverage file exists but overall_coverage is 0 or None: {overall_coverage}"  # noqa: E501
                            )
                except json.JSONDecodeError as e:
                    if is_infra:
                        logger.debug(
                            f"JSON decode error for {coverage_json_path}: {e} (file may be incomplete)"  # noqa: E501
                        )
                except Exception as e:
                    logger.debug(f"Could not read coverage from {coverage_json_path}: {e}")

            if coverage_found:
                break
        if coverage_found:
            break

    # Fallback to stdout parsing if JSON not found
    if not coverage_found:
        coverage_match = re.search(r"TOTAL\s+.*?\s+(\d+\.\d+)%", stdout_text)
        if not coverage_match:
            coverage_match = re.search(r"(\d+\.\d+)%", stdout_text)

        if coverage_match:
            coverage_pct = float(coverage_match.group(1))
            logger.info(f"✓ Found coverage: {coverage_pct:.1f}%")
            coverage_found = True

    return coverage_found, coverage_pct
