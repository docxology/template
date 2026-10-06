"""Bounded subprocess execution for project hooks and analysis scripts.

Implements finite process supervision and credential-environment filtering for
the ``SECURE-RUN-1`` and ``PROJECT-EXECUTION-BOUNDARY-1`` contracts. Arbitrary
Python hooks need a separate sandbox to restrict filesystem and network access.

The module provides four composable layers:

* :func:`classify_lifecycle_link` — distinguish an intentional lifecycle
  symlink (points back into the allowed tree) from an escape attempt.
* :func:`validate_hook_root` — enforce that a hook/script resolves inside
  an allowed hook root (traversal + symlink policy).
* :func:`build_bounded_env` — strip credential-like environment variables
  unless explicitly allow-listed (secret policy).
* :func:`run_bounded_subprocess` — execute ``argv`` in a fresh process
  group so a timeout can kill the whole process tree (no orphaned
  descendants). Callers admit their immutable plan and apply environment
  filtering before launch; sandboxed operations enforce network isolation.

All functions are testable with real files/subprocesses (No-Mocks policy).
"""

from __future__ import annotations

import signal
import math
import subprocess  # nosec B404
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from infrastructure.core._bounded_run_guardian import (
    start_bounded_run_guardian as _start_bounded_run_guardian,
    BoundedRunGuardian,
    GuardianCustodyError,
    DEFAULT_GUARDIAN_STARTUP_TIMEOUT_SECONDS,
    validate_guardian_startup_timeout,
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
    custody_refused: bool = False
    original_returncode: int | None = None


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
    capture_output: bool = True,
    guardian_startup_timeout_seconds: float = DEFAULT_GUARDIAN_STARTUP_TIMEOUT_SECONDS,
    guardian_env: dict[str, str] | None = None,
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
    * Startup, arming and command execution consume the original deadline.
      Cleanup is mandatory, and exceeding that deadline prevents success.

    Args:
        argv: Executable + arguments.
        cwd: Working directory (normalized to ``Path``).
        env: Sanitized environment (see :func:`build_bounded_env`).
        timeout: Seconds to wait before killing the group.
        group_id: Optional fixed process-group id (used by tests that want to
            assert cleanup on a known value; default creates a new group).
        capture_output: When True, capture stdout/stderr.
        guardian_startup_timeout_seconds: Finite READY/ARM phase allowance,
            always confined to the original whole-operation deadline.
        guardian_env: Optional separate environment for the cleanup guardian.
            Callers whose child must inherit a broader environment pass a
            sanitized one here so the guardian never holds credentials.

    Returns:
        A :class:`BoundedSubprocessResult`.
    """
    cmd = list(argv)
    workdir = Path(cwd)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("bounded execution requires a positive finite whole-operation timeout")
    validate_guardian_startup_timeout(guardian_startup_timeout_seconds)
    deadline = time.monotonic() + timeout
    proc: subprocess.Popen[str] | None = None
    process_env, run_token = build_bounded_run_env(env)
    if time.monotonic() >= deadline:
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=124,
            timed_out=True,
            command_error="bounded-run deadline expired before guardian startup",
        )
    try:
        guardian = _start_bounded_run_guardian(
            env if guardian_env is None else guardian_env,
            deadline_monotonic=deadline,
            startup_timeout_seconds=guardian_startup_timeout_seconds,
        )
    except GuardianCustodyError as exc:
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=75,
            timed_out=False,
            custody_refused=True,
            command_error=f"bounded-run guardian refused source custody: {exc}",
        )
    except TimeoutError as exc:
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=124,
            timed_out=True,
            command_error=f"bounded-run guardian startup timed out before command launch: {exc}",
        )
    except (OSError, RuntimeError) as exc:
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=1,
            timed_out=False,
            command_error=f"failed to start bounded-run guardian: {exc}",
        )
    if time.monotonic() >= deadline:
        if guardian is not None:
            guardian.close()
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=124,
            timed_out=True,
            command_error="bounded-run deadline expired before command launch",
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
            encoding="utf-8" if capture_output else None,
            errors="replace" if capture_output else None,
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
            guardian.arm(root_pid=proc.pid, run_token=run_token, deadline_monotonic=deadline)
        except BaseException as exc:
            terminate_process_tree(proc.pid, group_id=effective_group)
            terminate_bounded_run_processes(run_token)
            guardian.close()
            with _suppress():
                proc.wait(timeout=5)
            if isinstance(exc, GuardianCustodyError):
                return BoundedSubprocessResult(
                    argv=tuple(cmd),
                    returncode=130 if proc.returncode in {130, -signal.SIGINT} else 75,
                    timed_out=False,
                    custody_refused=True,
                    original_returncode=proc.returncode,
                    command_error=f"bounded-run guardian refused source custody: {exc}",
                )
            if isinstance(exc, TimeoutError):
                return BoundedSubprocessResult(
                    argv=tuple(cmd),
                    returncode=130 if proc.returncode in {130, -signal.SIGINT} else 124,
                    timed_out=proc.returncode not in {130, -signal.SIGINT},
                    original_returncode=proc.returncode,
                    command_error=f"bounded-run guardian arming timed out: {exc}",
                )
            if isinstance(exc, (OSError, RuntimeError)):
                return BoundedSubprocessResult(
                    argv=tuple(cmd),
                    returncode=130 if proc.returncode in {130, -signal.SIGINT} else 1,
                    timed_out=False,
                    original_returncode=proc.returncode,
                    command_error=f"failed to arm bounded-run guardian: {exc}",
                )
            raise

    try:
        stdout, stderr = proc.communicate(timeout=max(0.0, deadline - time.monotonic()))
        cleanup_error, custody_refused = _cleanup_result(guardian, run_token)
        code = proc.returncode if proc.returncode is not None else 0
        expired = time.monotonic() >= deadline
        return BoundedSubprocessResult(
            argv=tuple(cmd),
            returncode=130
            if code in {130, -2}
            else 124
            if expired
            else 75
            if custody_refused
            else 1
            if cleanup_error
            else code,
            timed_out=expired and code not in {130, -2},
            stdout=stdout or "",
            stderr=stderr or "",
            command_error=cleanup_error,
            custody_refused=custody_refused,
            original_returncode=proc.returncode,
        )
    except subprocess.TimeoutExpired as exc:
        terminate_process_tree(proc.pid, group_id=effective_group)
        try:
            cleanup_error, custody_refused = _cleanup_result(guardian, run_token)
        finally:
            # Reap even if an operator interrupts guardian cleanup after root kill.
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
            custody_refused=custody_refused,
            original_returncode=proc.returncode,
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
            original_returncode=proc.returncode,
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


from infrastructure.core._bounded_kill import (  # noqa: E402
    _RUN_IDS_ENV,
    _complete_bounded_run_cleanup,
    _suppress,
    _terminate_and_reap_interrupted_process,
    terminate_bounded_run_processes,
    terminate_process_tree,
)


def _timeout_output_text(value: str | bytes | None) -> str:
    """Normalize ``TimeoutExpired`` partial output across Python versions."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _cleanup_result(guardian: BoundedRunGuardian | None, run_token: str) -> tuple[str, bool]:
    """Only a positively typed custody refusal may receive that classification."""
    try:
        return _complete_bounded_run_cleanup(guardian, run_token), False
    except GuardianCustodyError as exc:
        return f"bounded-run guardian refused source custody after cleanup: {exc}", True


__all__ = [
    "BoundedSubprocessResult",
    "LinkClassification",
    "build_bounded_env",
    "build_bounded_run_env",
    "_complete_bounded_run_cleanup",
    "classify_lifecycle_link",
    "run_bounded_subprocess",
    "terminate_bounded_run_processes",
    "terminate_process_tree",
    "validate_hook_root",
]
