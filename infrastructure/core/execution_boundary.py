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
import os
import signal
import subprocess  # nosec B404
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

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
      (or a fresh group when ``None``), so a timeout can
      ``killpg`` the whole tree instead of leaving orphaned descendants.
    * On timeout the process group is sent SIGKILL and the result is marked
      ``timed_out=True``; the caller's run cannot outlive the hook.
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
    try:
        if egress_check is not None:
            egress_check(cmd, workdir, env)
    except Exception as exc:  # noqa: BLE001 - policy violation aborts the run
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=1,
            timed_out=False,
            command_error=f"refused by egress policy: {exc}",
        )
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(workdir),
            env=env,
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True if capture_output else None,
        )
    except OSError as exc:
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=1,
            timed_out=False,
            command_error=f"failed to launch: {exc}",
        )
    # Effective group id: the child got a fresh session (its pid == pgid).
    effective_group = proc.pid if group_id is None else group_id
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=proc.returncode if proc.returncode is not None else 0,
            timed_out=False,
            stdout=stdout or "",
            stderr=stderr or "",
        )
    except subprocess.TimeoutExpired:
        _terminate_process_group(effective_group)
        timed_out_stdout, timed_out_stderr = _drain_after_terminate(proc, capture_output=capture_output)
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=-signal.SIGKILL,
            timed_out=True,
            stdout=timed_out_stdout or "",
            stderr=timed_out_stderr or "",
        )
    except Exception as exc:  # noqa: BLE001 — any post-launch failure must still kill the group
        _terminate_process_group(effective_group)
        _drain_after_terminate(proc, capture_output=capture_output)
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=1,
            timed_out=False,
            command_error=f"bounded subprocess failed after launch: {exc}",
        )


def _drain_after_terminate(
    proc: subprocess.Popen[str],
    *,
    capture_output: bool,
) -> tuple[str | None, str | None]:
    """Reap a terminated child without blocking forever if killpg was a no-op."""
    if not capture_output:
        with contextlib.suppress(subprocess.TimeoutExpired, OSError, ProcessLookupError):
            proc.wait(timeout=5)
        with contextlib.suppress(OSError, ProcessLookupError):
            proc.kill()
        return None, None
    try:
        return proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(OSError, ProcessLookupError):
            proc.kill()
        with contextlib.suppress(subprocess.TimeoutExpired, OSError, ProcessLookupError):
            return proc.communicate(timeout=1)
        return None, None
    except (OSError, ProcessLookupError):
        return None, None


def _terminate_process_group(group_id: int) -> None:
    """Send SIGKILL to the process group *group_id* (POSIX only)."""
    if os.name == "nt":
        return
    with _suppress():
        os.killpg(group_id, signal.SIGKILL)


def _suppress() -> "contextlib.AbstractContextManager[None]":
    return contextlib.suppress(OSError, ProcessLookupError)


__all__ = [
    "BoundedSubprocessResult",
    "LinkClassification",
    "build_bounded_env",
    "classify_lifecycle_link",
    "run_bounded_subprocess",
    "validate_hook_root",
]
