"""Coverage plugin capability probes (Layer 1 — no reporting imports)."""

from __future__ import annotations

import subprocess

from infrastructure.core.runtime.environment import get_python_command


def check_cov_datafile_support() -> bool:
    """Return True if pytest-cov supports the ``--cov-datafile`` flag."""
    try:
        cmd = get_python_command() + ["-m", "pytest", "--help"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
        return "--cov-datafile" in result.stdout
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False


__all__ = ["check_cov_datafile_support"]
