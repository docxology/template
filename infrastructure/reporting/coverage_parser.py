"""Coverage and test output parsing utilities.

Provides parsing functions to extract coverage metrics, failed test names,
timeout errors, and coverage capabilities from pytest output.
Import from this module directly; functions are not re-exported via the package surface.
"""

from __future__ import annotations


import os
import re
import time
from pathlib import Path
from typing import TypedDict

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.config.queries import get_testing_config

from .coverage_json_parser import read_coverage_total


class FailedTestInfo(TypedDict, total=False):
    """Shape of a failed-test entry returned by extract_failed_tests."""

    test: str
    error_type: str
    error_message: str
    traceback: list[str]


class TimeoutErrorInfo(TypedDict):
    """Shape of a timeout-error entry returned by extract_timeout_errors."""

    test: str
    timeout_duration: str
    suggestion: str


logger = get_logger(__name__)


def _parse_failures_section(combined_output: str) -> list[FailedTestInfo]:
    """Parse failures from the FAILURES section (--tb=line format)."""
    failed_tests: list[FailedTestInfo] = []
    failures_section = False
    current_test = None

    for line in combined_output.split("\n"):
        line = line.strip()
        if "FAILURES" in line and "===" in line:
            failures_section = True
            continue
        elif line.startswith("=") and "durations" in line.lower():
            break
        if failures_section:
            if line.startswith("__") and "__" in line:
                m = re.search(r"__\s+([^_\s]+)\s+__", line)
                if m:
                    current_test = m.group(1)
            elif line.startswith("/") and ".py:" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3 and ":" in parts[2]:
                    error_split = parts[2].strip().split(":", 1)
                    path = parts[0].strip()
                    failed_tests.append(
                        {
                            "test": current_test or (path.split("/")[-1] if "/" in path else path),
                            "error_type": error_split[0].strip(),
                            "error_message": error_split[1].strip(),
                            "traceback": [],
                        }
                    )
    return failed_tests


def _parse_failures_verbose(combined_output: str) -> list[FailedTestInfo]:
    """Parse failures from verbose output (--verbose format)."""
    failed_tests: list[FailedTestInfo] = []
    for line in combined_output.split("\n"):
        if " FAILED" in line and "::" in line and not line.strip().startswith("="):
            m = re.search(r"([^\s]+)\s+FAILED", line.strip())
            if m:
                failed_tests.append(
                    {
                        "test": m.group(1),
                        "error_type": "Unknown",
                        "error_message": "Failed (use --tb=short for details)",
                    }
                )
    return failed_tests


def _parse_failures_short(combined_output: str) -> list[FailedTestInfo]:
    """Parse failures from short FAILED lines."""
    failed_tests: list[FailedTestInfo] = []
    for line in combined_output.split("\n"):
        if line.strip().startswith("FAILED ") and "::" in line:
            m = re.search(r"FAILED\s+([^\s]+)", line)
            if m:
                error_type, error_message = "Unknown", "Run with -v for details"
                if " - " in line:
                    error_part = line.split(" - ", 1)[1]
                    if ":" in error_part:
                        e = error_part.split(":", 1)
                        error_type, error_message = e[0].strip(), e[1].strip()
                failed_tests.append({"test": m.group(1), "error_type": error_type, "error_message": error_message})
    return failed_tests


def _parse_failures_timeout(combined_output: str) -> list[FailedTestInfo]:
    """Parse timeout failures by scanning context around timeout lines."""
    failed_tests: list[FailedTestInfo] = []
    lines = combined_output.split("\n")
    for i, line in enumerate(lines):
        if "timeout" in line.lower() or "pytest_timeout" in line.lower():
            for j in range(max(0, i - 3), i):
                # A passing test can be followed by timeout-related plugin
                # output (configuration, warnings, or another test's context).
                # Only a nearby explicit FAILED status is evidence that this
                # timeout belongs in the failed-test ledger.
                if "::" in lines[j] and "FAILED" in lines[j]:
                    m = re.search(r"([^\s]+)\s+(?:PASSED|FAILED)", lines[j])
                    if m:
                        failed_tests.append(
                            {
                                "test": m.group(1),
                                "error_type": "TimeoutError",
                                "error_message": "Test timed out (increase timeout or optimize test)",
                            }
                        )
                        break
    return failed_tests


def _parse_failures_fallback(combined_output: str) -> list[FailedTestInfo]:
    """Parse any remaining FAILED lines as a last resort."""
    failed_tests: list[FailedTestInfo] = []
    for line in combined_output.split("\n"):
        if line.strip().startswith("FAILED") and "::" in line:
            m = re.search(r"FAILED\s+([^\s]+)", line)
            if m:
                failed_tests.append(
                    {
                        "test": m.group(1),
                        "error_type": "Unknown",
                        "error_message": "Test failed (use --tb=short -v for details)",
                    }
                )
    return failed_tests


_FAILURE_STRATEGIES = [
    _parse_failures_section,
    _parse_failures_verbose,
    _parse_failures_short,
    _parse_failures_timeout,
    _parse_failures_fallback,
]


def extract_failed_tests(stdout: str, stderr: str) -> list[FailedTestInfo]:
    """Extract failed test info from pytest output using cascading parse strategies."""
    combined_output = stdout + "\n" + stderr
    for strategy in _FAILURE_STRATEGIES:
        result = strategy(combined_output)
        if result:
            return result
    return []


def extract_timeout_errors(stdout: str, stderr: str) -> list[TimeoutErrorInfo]:
    """Extract timeout errors from pytest output."""
    timeout_errors: list[TimeoutErrorInfo] = []
    combined_output = stdout + "\n" + stderr

    timeout_patterns = [
        r"timeout",
        r"pytest_timeout",
        r"timeouterror",
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
                test_match = re.search(r"([^\s]+\.py(?:::[^\s]+)*)\s+(?:PASSED|FAILED|ERROR)", prev_line)
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
    env_value = os.environ.get(env_var)
    if env_value is not None:
        try:
            max_failures = int(env_value)
        except (ValueError, TypeError):
            max_failures = 0
    else:
        testing_config = get_testing_config(repo_root)
        max_failures = int(getattr(testing_config, config_key, 0) or 0)

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


def _wait_for_coverage_total(paths: list[Path], max_retries: int = 3, delay: float = 0.5) -> float | None:
    """Read the first available measured total in configured path order."""
    if not paths:
        return None
    for attempt in range(max_retries):
        if attempt > 0:
            time.sleep(delay)
        for path in paths:
            percent = read_coverage_total(path)
            if percent is not None:
                return percent
    return None


def extract_coverage_percentage(stdout_text: str, coverage_json_paths: list[Path]) -> tuple[bool, float | None]:
    """Extract a measured JSON total or a recognized console coverage summary."""
    percent = _wait_for_coverage_total(coverage_json_paths)
    if percent is not None:
        logger.info(f"✓ Found coverage: {percent:.1f}%")
        return True, percent

    from .pytest_output_parser import _strip_ansi

    clean_text = _strip_ansi(stdout_text)
    match = re.search(r"(?im)^[ \t]*TOTAL[ \t]+(?:\d+[ \t]+){2,4}(\d+(?:\.\d+)?)%(?=[ \t\r]|$)", clean_text)
    if not match:
        match = re.search(r"(?im)(?:^[ \t]*coverage:|\btotal[ \t]+coverage:)[ \t]*(\d+(?:\.\d+)?)%", clean_text)
    if match:
        percent = float(match.group(1))
        if 0 <= percent <= 100:
            logger.info(f"✓ Found coverage from console: {percent:.1f}%")
            return True, percent
    return False, None


__all__ = [
    "FailedTestInfo",
    "TimeoutErrorInfo",
]
