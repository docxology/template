"""Bounded subprocess execution for project hooks and analysis scripts.

Implements the secure execution boundary required by the ``SECURE-RUN-1``
and ``PROJECT-EXECUTION-BOUNDARY-1`` backlog items. A "hostile hook" must
not be able to read credentials, escape the project root, or outlive a
failed/timed-out run.

The module provides four composable layers:

* :func:`classify_lifecycle_link` — distinguish an intentional lifecycle
  symlink (points back into the allowed tree) from an escape attempt.
* :func:`validate_hook_root` — enforce that a hook/script resolves inside
  an allowed hook root (traversal + symlink policy).
* :func:`build_bounded_env` — strip credential-like environment variables
  unless explicitly allow-listed (secret policy).
* :func:`run_bounded_subprocess` — execute ``argv`` in a fresh process
  group so a timeout can kill the whole process tree (no orphaned
  descendants), with root confinement, secret stripping, and an optional
  egress hook that is consulted before launch.

All functions are testable with real files/subprocesses (No-Mocks policy).
"""

from __future__ import annotations

import contextlib
import ctypes
import os
import signal
import subprocess  # nosec B404
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from infrastructure.core._bounded_run_guardian import (
    BoundedRunGuardian as _BoundedRunGuardian,
)
from infrastructure.core._bounded_run_guardian import (
    start_bounded_run_guardian as _start_bounded_run_guardian,
)
from infrastructure.core.secrets import strip_secret_env


@dataclass(frozen=True)
class LinkClassification:
    """Result of classifying one symlink found under a project root."""

    path: Path
    target: Path
    kind: str
    detail: str

    @property
    def allowed(self) -> bool:
        """Return ``True`` when this is an intentional lifecycle link."""
        return self.kind == "lifecycle"


def classify_lifecycle_link(
    link: Path,
    *,
    allowed_roots: Sequence[Path],
) -> LinkClassification:
    """Classify *link* as an intentional lifecycle link or an escape.

    A lifecycle link is a symlink whose *resolved* target stays inside one of
    the *allowed_roots*. Anything that resolves outside the allowed roots is
    classified ``escape`` and must not be followed by a bounded executor.

    Args:
        link: The symlink path (resolve is attempted leniently).
        allowed_roots: Canonical absolute roots that the target may live in.

    Returns:
        A :class:`LinkClassification` describing the kind and a human detail.
    """
    canonical_roots = [Path(r).resolve() for r in allowed_roots]
    try:
        target = link.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        return LinkClassification(
            path=link,
            target=link,
            kind="error",
            detail=f"cannot resolve {link}: {exc}",
        )
    for root in canonical_roots:
        try:
            target.relative_to(root)
        except ValueError:
            continue
        return LinkClassification(
            path=link,
            target=target,
            kind="lifecycle",
            detail=f"resolves inside allowed root {root}",
        )
    return LinkClassification(
        path=link,
        target=target,
        kind="escape",
        detail=f"resolves outside allowed roots: {target}",
    )


def validate_hook_root(
    candidate: Path,
    *,
    hook_root: Path,
    hook_root_must_exist: bool = True,
) -> Path:
    """Return the canonical *candidate* only when it resolves inside *hook_root*.

    Rejects absolute escapes, ``..`` traversal, and symlink components that
    point outside the hook root. This is the root-confinement predicate for
    project hooks and analysis scripts.

    Args:
        candidate: The hook/script path (may be relative or absolute).
        hook_root: The canonical root the hook must live inside.

    Returns:
        The resolved, confined ``Path``.

    Raises:
        ValueError: When the candidate escapes the hook root or the root is
            not a real directory.
    """
    root = Path(hook_root).resolve()
    if hook_root_must_exist and not root.is_dir():
        raise ValueError(f"hook root is not a real directory: {root}")
    resolved = Path(candidate).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"hook must resolve inside hook root {root}: {candidate}") from exc
    return resolved


def build_bounded_env(
    base_env: dict[str, str] | None = None,
    *,
    allow_secret_names: Sequence[str] = (),
    passthrough: Sequence[str] = (),
) -> dict[str, str]:
    """Build a subprocess environment with credential-like variables stripped.

    Args:
        base_env: Environment to sanitize (defaults to ``os.environ``).
        allow_secret_names: Exact variable names to keep even if they look
            like credentials (explicit opt-in only).
        passthrough: Exact variable names to keep as-is.

    Returns:
        A new environment dictionary with secrets removed unless they are in
        ``allow_secret_names`` or ``passthrough``.
    """
    return strip_secret_env(
        base_env,
        allow_secret_names=allow_secret_names,
        passthrough=passthrough,
    )


@dataclass
class BoundedSubprocessResult:
    """Result of :func:`run_bounded_subprocess`."""

    argv: tuple[str, ...]
    returncode: int
    timed_out: bool
    stdout: str = ""
    stderr: str = ""
    command_error: str = ""


# An optional ``(argv, cwd, env) -> None`` callable consulted before launch.
# Raise to refuse execution (policy violation / network egress).
EgressCheck = Callable[[Sequence[str], Path, dict[str, str]], None]
_RUN_IDS_ENV = "TEMPLATE_BOUNDED_RUN_IDS"


def build_bounded_run_env(env: dict[str, str]) -> tuple[dict[str, str], str]:
    """Append a unique inherited identity and return ``(environment, token)``."""
    run_token = uuid.uuid4().hex
    process_env = dict(env)
    inherited_run_ids = process_env.get(_RUN_IDS_ENV, "").strip()
    process_env[_RUN_IDS_ENV] = f"{inherited_run_ids}:{run_token}" if inherited_run_ids else run_token
    return process_env, run_token


def run_bounded_subprocess(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: float,
    group_id: int | None = None,
    egress_check: EgressCheck | None = None,
    capture_output: bool = True,
) -> BoundedSubprocessResult:
    """Run *argv* in an isolated process group with cleanup on timeout.

    Security contract (SECURE-RUN-1):
    * The child starts in a new session/process group owned by ``group_id``
      (or a fresh group when ``None``).
    * On timeout the root is frozen, descendants are discovered across nested
      sessions, and the complete known tree plus original process group is
      killed before the result is marked ``timed_out=True``; the caller's run
      cannot outlive the hook.
    * If the caller is interrupted while waiting, the same tree and inherited
      run identity are terminated and the root is reaped before the original
      exception is re-raised.
    * ``egress_check`` is called just before launch; raising aborts the run
      with ``command_error`` set (network/egress policy).

    Args:
        argv: Executable + arguments.
        cwd: Working directory (normalized to ``Path``).
        env: Sanitized environment (see :func:`build_bounded_env`).
        timeout: Seconds to wait before killing the group.
        group_id: Optional fixed process-group id (used by tests that want to
            assert cleanup on a known value; default creates a new group).
        egress_check: Optional policy callback consulted before launch.
        capture_output: When True, capture stdout/stderr.

    Returns:
        A :class:`BoundedSubprocessResult`.
    """
    cmd = list(argv)
    workdir = Path(cwd)
    proc: subprocess.Popen[str] | None = None
    process_env, run_token = build_bounded_run_env(env)
    try:
        if egress_check is not None:
            egress_check(cmd, workdir, process_env)
    except Exception as exc:  # noqa: BLE001 - policy violation aborts the run
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=1,
            timed_out=False,
            command_error=f"refused by egress policy: {exc}",
        )
    try:
        guardian = _start_bounded_run_guardian(env)
    except (OSError, RuntimeError, TimeoutError) as exc:
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=1,
            timed_out=False,
            command_error=f"failed to start bounded-run guardian: {exc}",
        )
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(workdir),
            env=process_env,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True if capture_output else None,
        )
    except BaseException as exc:
        if guardian is not None:
            guardian.close()
        if isinstance(exc, OSError):
            return BoundedSubprocessResult(
                argv=tuple(cmd),
                returncode=1,
                timed_out=False,
                command_error=f"failed to launch: {exc}",
            )
        raise

    # Effective group id: the child got a fresh session (its pid == pgid).
    effective_group = proc.pid if group_id is None else group_id
    if guardian is not None:
        try:
            guardian.arm(root_pid=proc.pid, run_token=run_token)
        except BaseException as exc:
            terminate_process_tree(proc.pid, group_id=effective_group)
            terminate_bounded_run_processes(run_token)
            guardian.close()
            with _suppress():
                proc.wait(timeout=5)
            if isinstance(exc, (OSError, RuntimeError)):
                return BoundedSubprocessResult(
                    argv=tuple(cmd),
                    returncode=1,
                    timed_out=False,
                    command_error=f"failed to arm bounded-run guardian: {exc}",
                )
            raise

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        cleanup_error = _complete_bounded_run_cleanup(guardian, run_token)
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=1 if cleanup_error else (proc.returncode if proc.returncode is not None else 0),
            timed_out=False,
            stdout=stdout or "",
            stderr=stderr or "",
            command_error=cleanup_error,
        )
    except subprocess.TimeoutExpired as exc:
        terminate_process_tree(proc.pid, group_id=effective_group)
        cleanup_error = _complete_bounded_run_cleanup(guardian, run_token)
        # Always reap the root process. With inherited stdout/stderr,
        # skipping ``communicate``/``wait`` would leave a defunct child
        # owned by a long-running pipeline orchestrator.
        try:
            timed_out_stdout, timed_out_stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            if proc.stdout is not None:
                proc.stdout.close()
            if proc.stderr is not None:
                proc.stderr.close()
            with _suppress():
                proc.wait(timeout=5)
            timed_out_stdout = _timeout_output_text(exc.stdout)
            timed_out_stderr = _timeout_output_text(exc.stderr)
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=-signal.SIGKILL,
            timed_out=True,
            stdout=timed_out_stdout or "",
            stderr=timed_out_stderr or "",
            command_error=cleanup_error,
        )
    except Exception as exc:  # noqa: BLE001 - any post-launch failure must clean up the group
        _terminate_and_reap_interrupted_process(
            proc,
            group_id=effective_group,
            run_token=run_token,
            guardian=guardian,
        )
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=1,
            timed_out=False,
            command_error=f"bounded subprocess failed after launch: {exc}",
        )
    except BaseException:
        _terminate_and_reap_interrupted_process(
            proc,
            group_id=effective_group,
            run_token=run_token,
            guardian=guardian,
        )
        raise


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


__all__ = [
    "BoundedSubprocessResult",
    "LinkClassification",
    "build_bounded_env",
    "build_bounded_run_env",
    "classify_lifecycle_link",
    "run_bounded_subprocess",
    "terminate_bounded_run_processes",
    "terminate_process_tree",
    "validate_hook_root",
]
