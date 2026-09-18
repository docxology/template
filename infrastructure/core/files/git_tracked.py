"""Git-aware tracking queries used by output-directory cleanup.

The pipeline's stage-01 clean wipes project ``output/`` directories before a
fresh run. Those directories can contain git-tracked files (committed release
artifacts such as PDFs, SHA256SUMS, and manifests) that a clean must never
destroy. This module answers "which paths under a directory are tracked by the
enclosing repository?" with one batched ``git ls-files`` per directory — cheap
enough to run at clean time.

Fail-closed: when git is available but cannot enumerate tracked files inside a
repository, the caller must refuse to delete rather than risk destroying
tracked files. A directory outside any git work tree can have no tracked
files, so an empty set is returned there.
"""

import os
import subprocess
from pathlib import Path

from infrastructure.core.exceptions import FileOperationError
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_GIT_TIMEOUT_SECONDS = 30
_NOT_A_REPOSITORY_MESSAGE = "not a git repository"


def _run_git(args: list[str], cwd: Path, *, what: str) -> subprocess.CompletedProcess[bytes]:
    """Run a short git command and return the completed process.

    Args:
        args: Arguments passed to ``git``.
        cwd: Working directory for the invocation.
        what: Human-readable purpose used in error messages.

    Returns:
        The completed process (caller inspects ``returncode``).

    Raises:
        FileOperationError: If git is missing, times out, or cannot be run.
    """
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            timeout=_GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except OSError as exc:  # git not installed or not executable
        raise FileOperationError(f"git unavailable while {what}: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise FileOperationError(f"git timed out while {what}") from exc


def tracked_files_under(directory: Path) -> frozenset[Path]:
    """Return the git-tracked file paths under *directory*, relative to it.

    One ``git ls-files`` invocation enumerates every tracked file below
    *directory* (including files deleted from the work tree but still in the
    index — such entries cannot be deleted by a filesystem walk anyway).

    Args:
        directory: Directory to inspect; must not be a symlink (callers
            already reject symlinked output directories).

    Returns:
        Relative paths of tracked files. Empty when *directory* is outside
        any git work tree, since nothing can be tracked there.

    Raises:
        FileOperationError: If git is available but fails to enumerate tracked
            files — callers must treat this as "cannot prove untracked" and
            refuse to delete (fail-closed).
    """
    probe = _run_git(["rev-parse", "--show-toplevel"], cwd=directory, what="locating the enclosing repository")
    if probe.returncode != 0:
        stderr = probe.stderr.decode("utf-8", errors="replace")
        if _NOT_A_REPOSITORY_MESSAGE in stderr:
            logger.debug("No git repository above %s; no tracked files to preserve", directory)
            return frozenset()
        raise FileOperationError(f"git failed while locating the repository above {directory}: {stderr.strip()}")

    listing = _run_git(["ls-files", "-z"], cwd=directory, what="enumerating tracked files")
    if listing.returncode != 0:
        stderr = listing.stderr.decode("utf-8", errors="replace")
        raise FileOperationError(f"git failed to list tracked files under {directory}: {stderr.strip()}")

    return frozenset(Path(os.fsdecode(entry)) for entry in listing.stdout.split(b"\0") if entry)
