"""Process-tree termination for bounded subprocess runs.

Extracted from ``execution_boundary`` (which re-exports the public names)
so the security-critical platform-kill logic — POSIX descendant scans and
the macOS ``KERN_PROCARGS2`` ctypes path — is reviewable in isolation.
"""

from __future__ import annotations

import contextlib
import ctypes
import os
import signal
import subprocess  # nosec B404
import sys
from pathlib import Path

from infrastructure.core._bounded_run_guardian import (
    BoundedRunGuardian as _BoundedRunGuardian,
)

_RUN_IDS_ENV = "TEMPLATE_BOUNDED_RUN_IDS"


def _terminate_process_group(group_id: int) -> None:
    """Send SIGKILL to the process group *group_id* (POSIX only)."""
    if os.name == "nt":
        return
    with _suppress():
        os.killpg(group_id, signal.SIGKILL)


def _timeout_output_text(value: str | bytes | None) -> str:
    """Normalize ``TimeoutExpired`` partial output across Python versions."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _terminate_and_reap_interrupted_process(
    process: subprocess.Popen[str],
    *,
    group_id: int,
    run_token: str,
    guardian: _BoundedRunGuardian | None,
) -> None:
    """Best-effort complete cleanup while preserving the caller's exception."""
    with contextlib.suppress(Exception):
        terminate_process_tree(process.pid, group_id=group_id)
    with contextlib.suppress(Exception):
        _complete_bounded_run_cleanup(guardian, run_token)
    for pipe in (process.stdout, process.stderr):
        if pipe is not None:
            with contextlib.suppress(Exception):
                pipe.close()
    with contextlib.suppress(Exception):
        process.kill()
    with contextlib.suppress(Exception):
        process.wait(timeout=5)


def _complete_bounded_run_cleanup(
    guardian: _BoundedRunGuardian | None,
    run_token: str,
) -> str:
    """Wait for independent cleanup, run a caller-side sweep, and report errors."""
    cleanup_error = ""
    if guardian is not None:
        try:
            guardian.wait_for_cleanup()
        except (OSError, RuntimeError, TimeoutError, subprocess.SubprocessError) as exc:
            cleanup_error = f"bounded-run guardian cleanup failed: {exc}"
        finally:
            guardian.close()
    terminate_bounded_run_processes(run_token)
    return cleanup_error


def terminate_process_tree(root_pid: int, *, group_id: int | None = None) -> None:
    """Kill *root_pid* and all descendants, including detached sessions.

    Process-group cleanup alone cannot reach a nested runner that called
    ``setsid()``. Freeze the root, repeatedly discover and freeze descendants,
    then kill every known PID and the original group. This is used by both the
    generic bounded executor and streaming Stage-01 commands so a timeout can
    never release an output lock while a detached writer survives.
    """
    if os.name == "nt":  # pragma: no cover - Windows-only tree cleanup
        subprocess.run(  # nosec B603 - fixed system utility argv
            ["taskkill", "/PID", str(root_pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
        return
    with _suppress():
        os.kill(root_pid, signal.SIGSTOP)
    descendants: set[int] = set()
    for _ in range(4):
        current = _posix_descendant_pids(root_pid)
        new_pids = current - descendants
        descendants.update(current)
        for pid in new_pids:
            with _suppress():
                os.kill(pid, signal.SIGSTOP)
        if not new_pids:
            break
    for pid in sorted(descendants, reverse=True):
        with _suppress():
            os.kill(pid, signal.SIGKILL)
    if group_id is not None:
        _terminate_process_group(group_id)
    with _suppress():
        os.kill(root_pid, signal.SIGKILL)


def _posix_descendant_pids(root_pid: int) -> set[int]:
    """Return descendants of *root_pid* from one portable POSIX ``ps`` scan."""
    ps_command = "/bin/ps" if Path("/bin/ps").is_file() else "ps"
    try:
        completed = subprocess.run(  # nosec B603 - fixed process-table query
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


def terminate_bounded_run_processes(run_token: str) -> set[int]:
    """Kill surviving descendants by their inherited bounded-run identity.

    A child can create a new session and become reparented after the direct
    root exits, at which point PPID and process-group traversal cannot find it.
    Every bounded run therefore appends an unguessable identity to its
    environment. Descendants created by the trusted project execution paths
    inherit that identity even across nested bounded runners, allowing final
    cleanup after an early root exit.
    """
    if os.name == "nt":
        return set()
    if sys.platform == "darwin":
        return _terminate_darwin_bounded_run_processes(run_token)
    matched: set[int] = set()
    empty_scans = 0
    for _ in range(4):
        current = _tagged_process_pids(run_token) - {os.getpid()}
        new_pids = current - matched
        matched.update(current)
        for pid in new_pids:
            with _suppress():
                os.kill(pid, signal.SIGSTOP)
        empty_scans = 0 if new_pids else empty_scans + 1
        if empty_scans >= 2:
            break
    for pid in sorted(matched, reverse=True):
        with _suppress():
            os.kill(pid, signal.SIGKILL)
    return matched


def _terminate_darwin_bounded_run_processes(run_token: str) -> set[int]:
    """Freeze and re-verify token-bound processes before killing them.

    macOS does not provide ``pidfd`` handles. A second token check while each
    candidate is stopped therefore closes the practical PID-reuse window: a
    PID that disappeared or no longer carries the token is resumed rather
    than killed.
    """
    stopped: set[int] = set()
    empty_scans = 0
    for _ in range(4):
        current = _darwin_tagged_process_pids(run_token) - {os.getpid()}
        stale = stopped - current
        for pid in stale:
            with _suppress():
                os.kill(pid, signal.SIGCONT)
        stopped.intersection_update(current)

        new_pids = current - stopped
        for pid in new_pids:
            with _suppress():
                os.kill(pid, signal.SIGSTOP)
        stopped.update(new_pids)
        empty_scans = 0 if new_pids else empty_scans + 1
        if empty_scans >= 2:
            break

    verified = stopped & _darwin_tagged_process_pids(run_token)
    for pid in stopped - verified:
        with _suppress():
            os.kill(pid, signal.SIGCONT)
    for pid in sorted(verified, reverse=True):
        with _suppress():
            os.kill(pid, signal.SIGKILL)
    return verified


def _tagged_process_pids(run_token: str) -> set[int]:
    """Return same-user processes whose environment contains *run_token*."""
    if sys.platform == "darwin":
        return _darwin_tagged_process_pids(run_token)
    ps_command = "/bin/ps" if Path("/bin/ps").is_file() else "ps"
    try:
        completed = subprocess.run(  # nosec B603 - fixed process-table query
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


def _darwin_tagged_process_pids(run_token: str) -> set[int]:
    """Find live token holders without a whole-user ``ps eww`` expansion.

    ``ps auxeww`` asks macOS to expand every process environment before the
    caller can filter it. A single uninterruptible I/O process can make that
    operation take longer than the bounded run itself. Instead, take a cheap
    PID/state snapshot and query ``KERN_PROCARGS2`` directly for each live PID.
    The kernel calls are fast for sleeping and uninterruptible processes and
    only the exact bounded-run environment entry is retained.
    """
    ps_command = "/bin/ps" if Path("/bin/ps").is_file() else "ps"
    try:
        completed = subprocess.run(  # nosec B603 - fixed process-state query
            [ps_command, "-x", "-o", "pid=,stat="],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if completed.returncode != 0:
        return set()

    libc = ctypes.CDLL(None, use_errno=True)
    sysctl = libc.sysctl
    matches: set[int] = set()
    for line in completed.stdout.splitlines():
        fields = line.split(None, 1)
        if len(fields) != 2 or fields[1].startswith("Z"):
            continue
        try:
            pid = int(fields[0])
        except ValueError:
            continue
        raw_args = _darwin_process_args(sysctl, pid)
        if raw_args is not None and _darwin_args_have_run_token(raw_args, run_token):
            matches.add(pid)
    return matches


def _darwin_process_args(sysctl: object, pid: int) -> bytes | None:
    """Return one process's ``KERN_PROCARGS2`` buffer, if still available."""
    query = sysctl
    if not callable(query):
        return None
    mib = (ctypes.c_int * 3)(1, 49, pid)  # CTL_KERN, KERN_PROCARGS2, pid
    for _ in range(2):
        size = ctypes.c_size_t(0)
        if query(mib, 3, None, ctypes.byref(size), None, 0) != 0 or size.value == 0:
            return None
        buffer = ctypes.create_string_buffer(size.value)
        if query(mib, 3, buffer, ctypes.byref(size), None, 0) == 0:
            return bytes(buffer.raw[: size.value])
        # An exec between the sizing and data calls can change the required
        # buffer size. Retry once against the process's new argument image.
    return None


def _darwin_args_have_run_token(raw_args: bytes, run_token: str) -> bool:
    """Return whether parsed ``KERN_PROCARGS2`` environment has *run_token*."""
    int_size = ctypes.sizeof(ctypes.c_int)
    if len(raw_args) < int_size:
        return False
    argc = int.from_bytes(raw_args[:int_size], byteorder=sys.byteorder, signed=True)
    if argc < 0:
        return False

    cursor = raw_args.find(b"\0", int_size)
    if cursor < 0:
        return False
    cursor += 1
    while cursor < len(raw_args) and raw_args[cursor] == 0:
        cursor += 1
    for _ in range(argc):
        cursor = raw_args.find(b"\0", cursor)
        if cursor < 0:
            return False
        cursor += 1
    while cursor < len(raw_args) and raw_args[cursor] == 0:
        cursor += 1

    prefix = f"{_RUN_IDS_ENV}=".encode("ascii")
    token = run_token.encode("ascii")
    for entry in raw_args[cursor:].split(b"\0"):
        if entry.startswith(prefix) and token in entry[len(prefix) :].split(b":"):
            return True
    return False


def _suppress() -> "contextlib.AbstractContextManager[None]":
    return contextlib.suppress(OSError, ProcessLookupError, subprocess.TimeoutExpired)
