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
import uuid
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


_RUN_IDS_ENV = "TEMPLATE_BOUNDED_RUN_IDS"


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
    run_token = uuid.uuid4().hex
    process_env = dict(env)
    inherited_run_ids = process_env.get(_RUN_IDS_ENV, "").strip()
    process_env[_RUN_IDS_ENV] = f"{inherited_run_ids}:{run_token}" if inherited_run_ids else run_token
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=process_env,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        _terminate_tagged_processes(run_token)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_tree(process.pid)
        _terminate_tagged_processes(run_token)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
            with contextlib.suppress(OSError, ProcessLookupError, subprocess.TimeoutExpired):
                process.wait(timeout=5)
            stdout = _timeout_output_text(exc.stdout)
            stderr = _timeout_output_text(exc.stderr)
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


def _timeout_output_text(value: str | bytes | None) -> str:
    """Normalize ``TimeoutExpired`` partial output across Python versions."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _terminate_process_tree(root_pid: int) -> None:
    """Kill a standalone runner and descendants that created new sessions."""
    if os.name == "nt":  # pragma: no cover - Windows-only cleanup
        subprocess.run(
            ["taskkill", "/PID", str(root_pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
        return
    with contextlib.suppress(OSError, ProcessLookupError):
        os.kill(root_pid, signal.SIGSTOP)
    descendants: set[int] = set()
    for _ in range(4):
        current = _posix_descendant_pids(root_pid)
        new_pids = current - descendants
        descendants.update(current)
        for pid in new_pids:
            with contextlib.suppress(OSError, ProcessLookupError):
                os.kill(pid, signal.SIGSTOP)
        if not new_pids:
            break
    for pid in sorted(descendants, reverse=True):
        with contextlib.suppress(OSError, ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
    with contextlib.suppress(OSError, ProcessLookupError):
        os.killpg(root_pid, signal.SIGKILL)
    with contextlib.suppress(OSError, ProcessLookupError):
        os.kill(root_pid, signal.SIGKILL)


def _posix_descendant_pids(root_pid: int) -> set[int]:
    """Return descendants of *root_pid* from one portable process-table scan."""
    ps_command = "/bin/ps" if Path("/bin/ps").is_file() else "ps"
    try:
        completed = subprocess.run(
            [ps_command, "-axo", "pid=,ppid="],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if completed.returncode != 0:
        return set()
    children: dict[int, list[int]] = {}
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        try:
            pid, parent_pid = (int(part) for part in parts)
        except ValueError:
            continue
        children.setdefault(parent_pid, []).append(pid)
    descendants: set[int] = set()
    pending = list(children.get(root_pid, ()))
    while pending:
        pid = pending.pop()
        if pid in descendants:
            continue
        descendants.add(pid)
        pending.extend(children.get(pid, ()))
    return descendants


def _terminate_tagged_processes(run_token: str) -> set[int]:
    """Kill surviving descendants by inherited bounded-run identity."""
    if os.name == "nt":
        return set()
    matched: set[int] = set()
    for _ in range(4):
        current = _tagged_process_pids(run_token) - {os.getpid()}
        new_pids = current - matched
        matched.update(current)
        for pid in new_pids:
            with contextlib.suppress(OSError, ProcessLookupError):
                os.kill(pid, signal.SIGSTOP)
        if not new_pids:
            break
    for pid in sorted(matched, reverse=True):
        with contextlib.suppress(OSError, ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
    return matched


def _tagged_process_pids(run_token: str) -> set[int]:
    """Return same-user processes whose environment contains *run_token*."""
    ps_command = "/bin/ps" if Path("/bin/ps").is_file() else "ps"
    try:
        completed = subprocess.run(
            [ps_command, "auxeww"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if completed.returncode != 0:
        return set()
    matches: set[int] = set()
    for line in completed.stdout.splitlines()[1:]:
        if run_token not in line:
            continue
        fields = line.split(None, 2)
        if len(fields) < 2:
            continue
        try:
            matches.add(int(fields[1]))
        except ValueError:
            continue
    return matches


__all__ = ["PortableSubprocessResult", "build_bounded_env", "run_bounded_subprocess"]
