"""Standalone bounded subprocess boundary for the Active Inference exemplar.

The public exemplar has its own project environment, so it cannot import the
root repository package during an isolated coverage run. This adapter keeps
the same process-group, timeout, and credential-redaction contract locally;
the root matrix uses the repository-wide equivalent in
``infrastructure.core.execution_boundary``.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PortableSubprocessResult:
    """Result of one bounded standalone subprocess."""

    returncode: int
    timed_out: bool
    stdout: str = ""
    stderr: str = ""
    command_error: str = ""


def build_bounded_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return an environment without credential-shaped variable names."""
    source = dict(os.environ if base_env is None else base_env)
    secret_markers = ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "PRIVATE_KEY", "CREDENTIAL")
    return {key: value for key, value in source.items() if not any(marker in key.upper() for marker in secret_markers)}


def run_bounded_subprocess(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: float,
    capture_output: bool = True,
) -> PortableSubprocessResult:
    """Run a command in a process group and kill descendants on timeout."""
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        return PortableSubprocessResult(
            returncode=124,
            timed_out=True,
            stdout=stdout or "",
            stderr=stderr or "",
            command_error=f"timed out after {timeout:g}s",
        )
    return PortableSubprocessResult(
        returncode=process.returncode or 0,
        timed_out=False,
        stdout=stdout or "",
        stderr=stderr or "",
    )


__all__ = ["PortableSubprocessResult", "build_bounded_env", "run_bounded_subprocess"]
