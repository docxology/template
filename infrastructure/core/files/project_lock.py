"""Cross-process per-project advisory lock that serializes pipeline/test runs.

Two pipeline or test-suite runs on the *same* project both write to the same
``projects/<name>/output`` tree. One run's Stage-1 ``Clean Output Directories``
step deletes ``output/`` while another run's gate tests are mid-read, which
corrupts artifacts and produces *random-location* "artifact missing" failures
(for example ``si_trace_present`` resolving to ``None``). Those failures look
like flaky tests but are an environmental race, not a code defect.

This module provides a per-project ``flock`` advisory lock so concurrent runs
serialize instead of racing. Key properties:

* **Crash-safe.** The lock is a POSIX advisory lock tied to an open file
  description; the kernel releases it automatically if the holding process
  dies, so a crashed run can never deadlock later runs.
* **Legacy child reentry.** The pipeline executor holds the lock for an
  entire run and spawns its test stage (``scripts/pipeline/stage_01_test.py``) as a subprocess
  that *also* asks for the lock. To avoid the child blocking on a lock its
  parent already holds, the holder exports an environment marker that
  descendant processes inherit and honor as a no-op acquisition.
  Recovery uses an actual locally held lock and never trusts that marker.
* **Best-effort off POSIX.** On platforms without ``fcntl`` (e.g. Windows) the
  context degrades to the re-entrancy marker only; CI and the supported dev
  targets are POSIX, where the real lock applies.

The lock file lives under the system temp directory keyed by the resolved
project path, deliberately *outside* the project's ``output/`` tree so that a
Stage-1 Clean cannot remove the lock out from under a waiting run.
"""

from __future__ import annotations

import contextlib
import hashlib
import math
import os
import stat
import tempfile
import threading
import time
from collections.abc import Iterator
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_ENV_PREFIX = "TEMPLATE_PROJECT_LOCK_"
_POLL_INTERVAL_SEC = 0.25
_LOCAL_OWNERS: dict[str, tuple[int, int]] = {}


def _lock_key(project_root: Path) -> str:
    """Return a stable short key for a project derived from its resolved path."""
    resolved = str(project_root.resolve())
    return hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:16]


def _env_var(key: str) -> str:
    return f"{_ENV_PREFIX}{key}"


def _lock_path(key: str) -> Path:
    return Path(tempfile.gettempdir()) / f"template-project-{key}.lock"


def _local_owner() -> tuple[int, int]:
    return os.getpid(), threading.get_ident()


@contextlib.contextmanager
def project_output_lock(project_root: Path, *, timeout: float | None = None) -> Iterator[None]:
    """Serialize project output work and preserve supervised child reentry."""
    key = _lock_key(project_root)
    owner = _LOCAL_OWNERS.get(key)
    current = _local_owner()
    inherited = os.environ.get(_env_var(key)) == "1" and (owner is None or owner[0] != current[0])
    if owner == current or inherited:
        yield
        return
    with _hold_project_output_lock(project_root, key, timeout, require_posix=False):
        yield


@contextlib.contextmanager
def owned_project_output_lock(project_root: Path, *, timeout: float) -> Iterator[None]:
    """Require a real local POSIX lock for a same-process recovery operation.

    The inherited legacy marker authorizes no new recovery. Nested calls may
    reuse only the actual lock held by this process and thread.
    """
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout < 0:
        raise ValueError("Owned project lock timeout must be finite and nonnegative")
    key = _lock_key(project_root)
    if _LOCAL_OWNERS.get(key) == _local_owner():
        yield
        return
    with _hold_project_output_lock(project_root, key, timeout, require_posix=True):
        yield


@contextlib.contextmanager
def _hold_project_output_lock(
    project_root: Path, key: str, timeout: float | None, *, require_posix: bool
) -> Iterator[None]:
    env_var = _env_var(key)
    try:
        import fcntl
    except ImportError as error:  # pragma: no cover - non-POSIX fallback
        if require_posix:
            raise OSError("Actual project output lock requires POSIX flock") from error
        previous_marker = os.environ.get(env_var)
        os.environ[env_var] = "1"
        try:
            yield
        finally:
            _restore_marker(env_var, previous_marker)
        return

    lock_path = _lock_path(key)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        held = os.fstat(descriptor)
        if not stat.S_ISREG(held.st_mode) or held.st_nlink != 1:
            raise ValueError("Project output lock must be a single regular file")
        _acquire(descriptor, fcntl, project_root, timeout)
        current = lock_path.lstat()
        if (current.st_dev, current.st_ino) != (held.st_dev, held.st_ino):
            raise ValueError("Project output lock changed during acquisition")
        previous_marker = os.environ.get(env_var)
        _LOCAL_OWNERS[key] = _local_owner()
        try:
            os.environ[env_var] = "1"
            yield
        finally:
            try:
                _restore_marker(env_var, previous_marker)
            finally:
                _LOCAL_OWNERS.pop(key)
                fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _restore_marker(name: str, previous: str | None) -> None:
    if previous is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = previous


def _acquire(fileno: int, fcntl_mod: object, project_root: Path, timeout: float | None) -> None:
    """Acquire the exclusive lock, blocking or polling up to ``timeout`` seconds."""
    flock = fcntl_mod.flock  # type: ignore[attr-defined]
    lock_ex = fcntl_mod.LOCK_EX  # type: ignore[attr-defined]
    lock_nb = fcntl_mod.LOCK_NB  # type: ignore[attr-defined]

    # Fast path: try once without blocking so the common (uncontended) case is
    # silent and immediate.
    try:
        flock(fileno, lock_ex | lock_nb)
        return
    except OSError:
        pass

    logger.info(
        "Waiting for per-project output lock (another pipeline/test run is active for '%s')...",
        project_root.name,
    )

    if timeout is None:
        flock(fileno, lock_ex)
        return

    deadline = time.monotonic() + timeout
    while True:
        try:
            flock(fileno, lock_ex | lock_nb)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Timed out after {timeout}s waiting for output lock on project '{project_root.name}'"
                ) from None
            time.sleep(_POLL_INTERVAL_SEC)
