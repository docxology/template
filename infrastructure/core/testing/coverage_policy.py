"""Coverage plugin capability probes (Layer 1 — no reporting imports)."""

from __future__ import annotations

import subprocess

from infrastructure.core.runtime.environment import get_python_command

PYTEST_HELP_PROBE_TIMEOUT_SECONDS = 30


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


__all__ = ["PYTEST_HELP_PROBE_TIMEOUT_SECONDS", "check_cov_datafile_support"]
