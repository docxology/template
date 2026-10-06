"""Finite cleanup of trusted descendants inheriting an exact private run marker."""

from __future__ import annotations

import contextlib
import ctypes
import os
import signal
import subprocess
import sys

TOKEN_KEY = "TEMPLATE_CODE_EXECUTOR_RUN_ID"


def kill_group(pid: int) -> None:
    """Ignore an already exited group; verify live descendants separately."""
    with contextlib.suppress(OSError):
        os.killpg(pid, signal.SIGKILL)


def _darwin_environment(pid: int) -> tuple[bytes, ...]:
    libc = ctypes.CDLL(None, use_errno=True)
    query = libc.sysctl
    mib = (ctypes.c_int * 3)(1, 49, pid)
    for _ in range(2):
        size = ctypes.c_size_t(0)
        if query(mib, 3, None, ctypes.byref(size), None, 0) or not 0 < size.value <= 4 * 1024 * 1024:
            return ()
        buffer = ctypes.create_string_buffer(size.value)
        if query(mib, 3, buffer, ctypes.byref(size), None, 0):
            continue
        content = buffer.raw[: size.value]
        argc = int.from_bytes(content[:4], byteorder=sys.byteorder, signed=True)
        if not 0 <= argc <= 65536:
            return ()
        cursor = content.find(b"\0", 4) + 1
        if cursor == 0:
            return ()
        while cursor < len(content) and content[cursor] == 0:
            cursor += 1
        for _ in range(argc):
            cursor = content.find(b"\0", cursor) + 1
            if cursor == 0:
                return ()
        while cursor < len(content) and content[cursor] == 0:
            cursor += 1
        return tuple(content[cursor:].split(b"\0"))
    return ()


def tagged_pids(token: str) -> set[int]:
    """Keep process environments private; retain only exact marker matches."""
    marker = f"{TOKEN_KEY}={token}"
    command = ["/bin/ps", "-x", "-o", "pid=,stat="] if sys.platform == "darwin" else ["/bin/ps", "auxeww"]
    observed = subprocess.run(command, capture_output=True, text=True, timeout=3, check=False)
    if observed.returncode:
        raise RuntimeError("cannot verify descendant cleanup")
    matched = set()
    if sys.platform == "darwin":
        for line in observed.stdout.splitlines():
            fields = line.split()
            if len(fields) == 2 and not fields[1].startswith("Z"):
                pid = int(fields[0])
                if marker.encode() in _darwin_environment(pid):
                    matched.add(pid)
    else:
        for line in observed.stdout.splitlines()[1:]:
            if marker in line.split():
                matched.add(int(line.split(None, 2)[1]))
    return matched - {os.getpid()}


def kill_tagged(token: str) -> None:
    """Freeze, re-admit and remove token holders before declaring cleanup."""
    stopped: set[int] = set()
    for _ in range(4):
        current = tagged_pids(token)
        for pid in stopped - current:
            with contextlib.suppress(OSError):
                os.kill(pid, signal.SIGCONT)
        stopped.intersection_update(current)
        fresh = current - stopped
        for pid in fresh:
            with contextlib.suppress(OSError):
                os.kill(pid, signal.SIGSTOP)
        stopped.update(fresh)
        if not fresh:
            break
    admitted = stopped & tagged_pids(token)
    for pid in stopped - admitted:
        with contextlib.suppress(OSError):
            os.kill(pid, signal.SIGCONT)
    for pid in admitted:
        with contextlib.suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
    for _ in range(3):
        if not tagged_pids(token):
            return
    raise RuntimeError("token-bound descendants remain after cleanup")
