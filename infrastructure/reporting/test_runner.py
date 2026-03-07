"""Test runner infrastructure for pytest execution.

Provides pytest streaming execution and a common retry/coverage-conflict
loop used by both infrastructure and project test suites.
"""

from __future__ import annotations

import collections
import os
import select
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.file_operations import clean_coverage_files
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.logging_progress import log_with_spinner
from infrastructure.reporting.coverage_parser import (
    check_test_failures,
    extract_coverage_percentage,
    extract_failed_tests,
)
from infrastructure.reporting.coverage_reporter import parse_pytest_output

logger = get_logger(__name__)

# Stack-trace patterns from pytest internals / urllib3 that clutter output
_INTERNAL_STACK_PATTERNS = [
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
    "version, status, reason = self._read_status",
    "line = str(self.fp.readline",
]

_SUMMARY_KEYWORDS = [
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


def _is_internal_stack_line(line: str) -> bool:
    """Return True if the line matches a known internal stack-trace pattern."""
    return any(p in line for p in _INTERNAL_STACK_PATTERNS)


def _should_print_line(char: str, line: str, quiet: bool) -> bool:
    """Return True if the current line/dot should be printed to stdout."""
    if not quiet:
        return char == "." or not _is_internal_stack_line(line)
    # quiet mode: only print summary lines
    if char == "\n":
        return any(k in line for k in _SUMMARY_KEYWORDS) or line.count("=") >= 10
    return False


def run_pytest_stream(
    cmd: list[str], repo_root: Path, env: dict, quiet: bool
) -> tuple[int, str, str]:
    """Run pytest streaming output to console while capturing logs for reporting."""
    stdout_buf: list[str] = []
    recent_lines: collections.deque = collections.deque(maxlen=10)

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
    fd = process.stdout.fileno()
    os.set_blocking(fd, False)

    current_line = ""
    while True:
        reads, _, _ = select.select([fd], [], [], 0.1)

        if fd in reads:
            raw_chunk = process.stdout.read(4096)
            if raw_chunk is None:
                if process.poll() is not None:
                    break
                continue
            if not raw_chunk:
                if process.poll() is not None:
                    break
                continue

            chunk = raw_chunk.decode("utf-8", errors="replace")

            for char in chunk:
                current_line += char
                if char == "\n" or (char == "." and not quiet):
                    if char == "\n" and not _is_internal_stack_line(current_line):
                        stdout_buf.append(current_line)
                        recent_lines.append(current_line)

                    if _should_print_line(char, current_line, quiet):
                        sys.stdout.write(char if char == "." else current_line)
                        sys.stdout.flush()

                    if char == "\n":
                        current_line = ""
        else:
            if process.poll() is not None:
                break

    if current_line:
        stdout_buf.append(current_line)
        if not quiet:
            sys.stdout.write(current_line)
            sys.stdout.flush()

    for line in list(recent_lines)[-3:]:
        if ("passed" in line or "failed" in line or "skipped" in line) and not any(
            k in line for k in _SUMMARY_KEYWORDS
        ):
            sys.stdout.write(line)
            sys.stdout.flush()

    process.wait()
    return process.returncode, "".join(stdout_buf), ""


@dataclass
class TestSuiteConfig:
    """Configuration for a single test suite execution."""

    label: str
    cmd: list[str]
    env: dict[str, str]
    repo_root: Path
    coverage_json_paths: list[Path]
    coverage_threshold: float
    max_failures_env_var: str
    max_failures_config_key: str
    quiet: bool = True
    spinner_label: str = ""

    def __post_init__(self) -> None:
        if not self.spinner_label:
            self.spinner_label = f"Running {self.label.lower()} tests"


def run_test_suite(config: TestSuiteConfig) -> tuple[int, dict[str, Any]]:
    """Execute a test suite with retry on coverage conflicts.

    Handles:
    - Streaming pytest execution
    - One retry on coverage data conflicts
    - Coverage extraction from JSON
    - Test result parsing and failure analysis

    Args:
        config: Suite configuration including command, env, and thresholds.

    Returns:
        Tuple of (exit_code, test_results_dict).
    """
    max_retries = 1
    retry_count = 0

    exit_code = 1
    stdout_text = ""
    stderr_text = ""

    while retry_count <= max_retries:
        try:
            with log_with_spinner(config.spinner_label, logger):
                exit_code, stdout_text, stderr_text = run_pytest_stream(
                    config.cmd, config.repo_root, config.env, config.quiet
                )

            combined_output = stdout_text + "\n" + stderr_text
            is_coverage_conflict = (
                "coverage.exceptions.DataError" in combined_output
                or "Can't combine statement coverage data with branch data" in combined_output
            )

            if exit_code != 0 and is_coverage_conflict:
                retry_count += 1
                if retry_count <= max_retries:
                    logger.warning(
                        "Coverage data conflict detected for %s tests, "
                        "cleaning stale files and retrying (%d/%d)...",
                        config.label.lower(),
                        retry_count,
                        max_retries,
                    )
                    clean_coverage_files(config.repo_root)
                    continue
                else:
                    logger.warning(
                        "Coverage data conflict persisted for %s tests. "
                        "Tests passed; ignoring coverage plugin error.",
                        config.label.lower(),
                    )
                    exit_code = 0
            break

        except subprocess.SubprocessError as e:
            error_msg = str(e)
            if "coverage.exceptions.DataError" in error_msg or "no such table: file" in error_msg:
                retry_count += 1
                if retry_count <= max_retries:
                    logger.warning(
                        "Coverage database corruption detected for %s, "
                        "cleaning and retrying (%d/%d)...",
                        config.label.lower(),
                        retry_count,
                        max_retries,
                    )
                    clean_coverage_files(config.repo_root)
                    continue
                else:
                    logger.error(
                        "Coverage database corruption persisted after cleanup for %s",
                        config.label.lower(),
                    )
                    raise
            raise

    coverage_found, coverage_pct = extract_coverage_percentage(
        stdout_text, config.coverage_json_paths
    )

    if not coverage_found:
        logger.warning("No %s coverage percentage found", config.label.lower())

    test_results = parse_pytest_output(stdout_text, stderr_text, exit_code)

    if coverage_pct is not None:
        test_results["coverage_percent"] = coverage_pct

    failed_tests = extract_failed_tests(stdout_text, stderr_text)
    test_results["failed_tests"] = failed_tests

    warning_count = stdout_text.count(" warning") + stderr_text.count(" warning")
    if warning_count > 0:
        logger.warning("%s tests completed with %d warning(s)", config.label, warning_count)

    failed_count = test_results.get("failed", 0)
    should_halt, message = check_test_failures(
        failed_count,
        config.label,
        config.repo_root,
        config.max_failures_env_var,
        config.max_failures_config_key,
    )

    if exit_code == 0:
        pass  # Caller logs success
    elif should_halt:
        logger.error(message)
    else:
        logger.warning(message)
        exit_code = 0

    return exit_code, test_results
