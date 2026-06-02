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
* **Cross-process re-entrant.** The pipeline executor holds the lock for an
  entire run and spawns its test stage (``01_run_tests.py``) as a subprocess
  that *also* asks for the lock. To avoid the child blocking on a lock its
  parent already holds, the holder exports an environment marker that
  descendant processes inherit and honor as a no-op acquisition.
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
import os
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_ENV_PREFIX = "TEMPLATE_PROJECT_LOCK_"
_POLL_INTERVAL_SEC = 0.25


def _lock_key(project_root: Path) -> str:
    """Return a stable short key for a project derived from its resolved path."""
    resolved = str(project_root.resolve())
    return hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:16]


def _env_var(key: str) -> str:
    return f"{_ENV_PREFIX}{key}"


def _lock_path(key: str) -> Path:
    return Path(tempfile.gettempdir()) / f"template-project-{key}.lock"


@contextlib.contextmanager
def project_output_lock(project_root: Path, *, timeout: float | None = None) -> Iterator[None]:
    """Hold an exclusive per-project lock for the duration of the context.

    Args:
        project_root: The project directory (``projects/<name>/``) whose
            ``output/`` tree the caller is about to write or clean.
        timeout: Maximum seconds to wait for the lock. ``None`` blocks
            indefinitely (the correct default for a pipeline run — concurrent
            same-project runs *should* serialize). A positive value polls and
            raises :class:`TimeoutError` if the lock cannot be acquired in time.

    Yields:
        ``None``. The lock is released on context exit, including on error.

    Re-entrant across process boundaries: if an ancestor already holds this
    project's lock (signalled via an inherited environment marker), the context
    is a no-op so a child process cannot deadlock against its parent.
    """
    key = _lock_key(project_root)
    env_var = _env_var(key)

    if os.environ.get(env_var) == "1":
        # An ancestor (typically the pipeline executor) already holds the lock.
        yield
        return

    try:
        import fcntl
    except ImportError:  # pragma: no cover - non-POSIX fallback (CI/dev are POSIX)
        os.environ[env_var] = "1"
        try:
            yield
        finally:
            os.environ.pop(env_var, None)
        return

    lock_path = _lock_path(key)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "w", encoding="utf-8") as handle:
        _acquire(handle.fileno(), fcntl, project_root, timeout)
        os.environ[env_var] = "1"
        try:
            yield
        finally:
            os.environ.pop(env_var, None)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


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
