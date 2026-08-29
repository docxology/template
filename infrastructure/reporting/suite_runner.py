"""Test runner infrastructure for pytest execution.

Provides pytest streaming execution and a common retry/coverage-conflict
loop used by both infrastructure and project test suites.
"""

import collections
import contextlib
import os
import select
import subprocess
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any

from infrastructure.core._bounded_run_guardian import (
    start_bounded_run_guardian as _start_bounded_run_guardian,
)
from infrastructure.core.execution_boundary import (
    _complete_bounded_run_cleanup,
    build_bounded_env,
    build_bounded_run_env,
    terminate_process_tree,
)
from infrastructure.core.files.coverage_cleanup import clean_coverage_files
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.logging.progress import log_with_spinner
from infrastructure.reporting.coverage_parser import (
    check_test_failures,
    extract_coverage_percentage,
    extract_failed_tests,
)
from infrastructure.reporting.coverage_reporter import parse_pytest_output

logger = get_logger(__name__)

DEFAULT_TEST_SUITE_TIMEOUT_SECONDS = 1800.0
DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS = 6900.0

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


def _passes_quiet_filter(char: str, line: str, quiet: bool) -> bool:
    """Return True if the current line/dot passes the quiet-mode output filter."""
    if not quiet:
        return char == "." or not _is_internal_stack_line(line)
    # quiet mode: only print summary lines
    if char == "\n":
        return any(k in line for k in _SUMMARY_KEYWORDS) or line.count("=") >= 10
    return False


def _terminate_stream_process(process: subprocess.Popen[bytes]) -> None:
    """Terminate a streaming subprocess and descendants across sessions.

    A nested project runner may deliberately start its own sessions for
    per-command timeouts. Killing only the outer process group would then leave
    those detached descendants alive after the project output lock is released.
    On POSIX, freeze the root, discover descendants from the process table until
    stable, then kill every PID as well as the original group. Windows uses
    ``taskkill /T`` for the equivalent tree operation.
    """
    terminate_process_tree(process.pid, group_id=process.pid)


def run_pytest_stream(
    cmd: list[str],
    repo_root: Path,
    env: dict[str, str],
    quiet: bool,
    *,
    timeout_seconds: float = DEFAULT_TEST_SUITE_TIMEOUT_SECONDS,
) -> tuple[int, str, str]:
    """Run pytest with streaming output, a real deadline, and group cleanup."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    stdout_buf: list[str] = []
    recent_lines: collections.deque[str] = collections.deque(maxlen=10)

    base_env = build_bounded_env(env)
    process_env, run_token = build_bounded_run_env(base_env)
    guardian = _start_bounded_run_guardian(base_env)
    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(repo_root),
            env=process_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,  # Use binary mode for non-blocking IO
            bufsize=0,
            start_new_session=(os.name != "nt"),
        )
    except BaseException:
        if guardian is not None:
            guardian.close()
        raise
    if guardian is not None:
        try:
            guardian.arm(root_pid=process.pid, run_token=run_token)
        except BaseException as exc:
            _terminate_stream_process(process)
            guardian.close()
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                process.wait(timeout=5)
            if isinstance(exc, (OSError, RuntimeError)):
                raise RuntimeError(f"failed to arm bounded-run guardian: {exc}") from exc
            raise

    assert process.stdout is not None
    fd = process.stdout.fileno()
    os.set_blocking(fd, False)

    timed_out = False
    deadline = monotonic() + timeout_seconds
    cleanup_error = ""
    try:
        current_line = ""
        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                timed_out = True
                break
            reads, _, _ = select.select([fd], [], [], min(0.1, remaining))

            if fd in reads:
                raw_chunk = process.stdout.read(4096)
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

                        if _passes_quiet_filter(char, current_line, quiet):
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

        try:
            process.wait(timeout=max(0.0, deadline - monotonic()))
        except subprocess.TimeoutExpired:
            timed_out = True
    finally:
        if timed_out:
            _terminate_stream_process(process)
        elif process.poll() is None:
            _terminate_stream_process(process)
        cleanup_error = _complete_bounded_run_cleanup(guardian, run_token)
        if process.poll() is None:
            process.wait()
        if timed_out:
            stderr_text = f"streaming subprocess timed out after {timeout_seconds:g}s"
        else:
            stderr_text = ""
        if process.stdout is not None:
            process.stdout.close()

    if cleanup_error:
        raise RuntimeError(cleanup_error)
    return (124 if timed_out else process.returncode), "".join(stdout_buf), stderr_text


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
    streaming_subprocess: bool = False
    timeout_seconds: float = DEFAULT_TEST_SUITE_TIMEOUT_SECONDS
    total_timeout_seconds: float | None = None
    coverage_cleanup_scope_dir: Path | None = None
    coverage_cleanup_recursive: bool = True

    def __post_init__(self) -> None:
        """Populate display defaults and validate opt-in total capacity."""
        if not self.spinner_label:
            self.spinner_label = f"Running {self.label.lower()} tests"
        if self.total_timeout_seconds is not None and self.total_timeout_seconds <= 0:
            raise ValueError("total_timeout_seconds must be positive when provided")


def _remaining_attempt_timeout_seconds(
    per_attempt_timeout_seconds: float,
    total_deadline_seconds: float | None,
    *,
    now_seconds: float | None = None,
) -> float:
    """Return the next subprocess budget under an optional absolute deadline."""
    if total_deadline_seconds is None:
        return per_attempt_timeout_seconds
    current_time = monotonic() if now_seconds is None else now_seconds
    return max(0.0, min(per_attempt_timeout_seconds, total_deadline_seconds - current_time))


def run_test_suite(config: "TestSuiteConfig") -> tuple[int, dict[str, Any]]:
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
    if config.timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    max_retries = 1
    retry_count = 0
    total_deadline_seconds = (
        monotonic() + config.total_timeout_seconds if config.total_timeout_seconds is not None else None
    )

    exit_code = 1
    stdout_text = ""
    stderr_text = ""
    while retry_count <= max_retries:
        attempt_timeout_seconds = _remaining_attempt_timeout_seconds(
            config.timeout_seconds,
            total_deadline_seconds,
        )
        if attempt_timeout_seconds <= 0:
            exit_code = 124
            total_timeout_message = (
                f"{config.label.lower()} test suite exhausted its "
                f"{config.total_timeout_seconds:g}s total timeout before retry attempt {retry_count + 1}"
            )
            stderr_text = f"{stderr_text}\n{total_timeout_message}" if stderr_text else total_timeout_message
            logger.error(total_timeout_message)
            break
        try:
            spinner_ctx = (
                nullcontext() if config.streaming_subprocess else log_with_spinner(config.spinner_label, logger)
            )
            with spinner_ctx:
                exit_code, stdout_text, stderr_text = run_pytest_stream(
                    config.cmd,
                    config.repo_root,
                    config.env,
                    config.quiet,
                    timeout_seconds=attempt_timeout_seconds,
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
                        "Coverage data conflict detected for %s tests, cleaning stale files and retrying (%d/%d)...",
                        config.label.lower(),
                        retry_count,
                        max_retries,
                    )
                    clean_coverage_files(
                        config.repo_root,
                        scope_dir=config.coverage_cleanup_scope_dir,
                        recursive=config.coverage_cleanup_recursive,
                    )
                    continue
                else:
                    logger.error(
                        "Coverage data conflict persisted for %s tests after cleanup retry.",
                        config.label.lower(),
                    )
            break

        except subprocess.SubprocessError as e:
            error_msg = str(e)
            if "coverage.exceptions.DataError" in error_msg or "no such table: file" in error_msg:
                retry_count += 1
                if retry_count <= max_retries:
                    logger.warning(
                        "Coverage database corruption detected for %s, cleaning and retrying (%d/%d)...",
                        config.label.lower(),
                        retry_count,
                        max_retries,
                    )
                    clean_coverage_files(
                        config.repo_root,
                        scope_dir=config.coverage_cleanup_scope_dir,
                        recursive=config.coverage_cleanup_recursive,
                    )
                    continue
                else:
                    logger.error(
                        "Coverage database corruption persisted after cleanup for %s",
                        config.label.lower(),
                    )
                    raise
            raise

    coverage_found, coverage_pct = extract_coverage_percentage(stdout_text, config.coverage_json_paths)

    if not coverage_found:
        logger.warning(f"No {config.label.lower()} coverage percentage found")

    test_results = parse_pytest_output(stdout_text, stderr_text, exit_code)

    if coverage_pct is not None:
        test_results["coverage_percent"] = coverage_pct

    failed_tests = extract_failed_tests(stdout_text, stderr_text)
    # The parser is intentionally conservative, but a zero-exit pytest run is
    # the final source of truth for the result ledger. Never persist diagnostic
    # text as failed tests when pytest reports no failures; stale entries make
    # generated evidence internally contradictory.
    if exit_code == 0 and test_results.get("failed", 0) == 0:
        failed_tests = []
    test_results["failed_tests"] = failed_tests

    warning_count = stdout_text.count(" warning") + stderr_text.count(" warning")
    if warning_count > 0:
        logger.warning(f"{config.label} tests completed with {warning_count} warning(s)")

    failed_count = test_results.get("failed", 0)
    should_halt, message = check_test_failures(
        failed_count,
        config.label,
        config.repo_root,
        config.max_failures_env_var,
        config.max_failures_config_key,
    )

    if exit_code != 0:
        if should_halt:
            logger.error(message)
        elif failed_count > 0:
            # Tolerated test failures (failed_count within the configured max):
            # suppress the non-zero exit so the pipeline may continue.
            logger.warning(message)
            exit_code = 0
        else:
            # Non-zero exit with zero test failures is NOT a tolerated test
            # failure — it is a coverage-below-floor gate failure or an internal
            # pytest error. Suppressing it here would green-wash a failed
            # coverage gate (every test passing while coverage < threshold).
            logger.error(
                f"{config.label}: non-zero exit ({exit_code}) with no test "
                "failures — coverage gate or pytest error; not suppressed"
            )

    # Keep the results dict in sync with the (possibly suppressed) exit code
    test_results["exit_code"] = exit_code

    return exit_code, test_results
