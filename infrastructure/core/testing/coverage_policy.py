"""Coverage process policy for test runners and their subprocesses."""

from __future__ import annotations

import os
import subprocess

from infrastructure.core.runtime.environment import get_python_command

PYTEST_HELP_PROBE_TIMEOUT_SECONDS = 30


def coverage_free_subprocess_env() -> dict[str, str]:
    """Copy the environment without interpreter-startup coverage settings."""
    env = os.environ.copy()
    for name in (
        "COVERAGE_FILE",
        "COVERAGE_PROCESS_CONFIG",
        "COVERAGE_PROCESS_START",
        "COV_CORE_BRANCH",
        "COV_CORE_CONFIG",
        "COV_CORE_CONTEXT",
        "COV_CORE_DATAFILE",
        "COV_CORE_SOURCE",
    ):
        env.pop(name, None)
    return env


def check_cov_datafile_support() -> bool:
    """Return True if pytest-cov supports the ``--cov-datafile`` flag."""
    try:
        cmd = get_python_command() + ["-m", "pytest", "--help"]
        # Importing pytest can exceed ten seconds on a loaded macOS worker
        # while several xdist workers start concurrently. Keep the probe
        # bounded, but do not turn normal startup contention into a false
        # "pytest-cov is unsupported" result.
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=PYTEST_HELP_PROBE_TIMEOUT_SECONDS,
            check=False,
        )
        return "--cov-datafile" in result.stdout
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False


__all__ = ["PYTEST_HELP_PROBE_TIMEOUT_SECONDS", "check_cov_datafile_support", "coverage_free_subprocess_env"]
