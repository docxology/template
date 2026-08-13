"""Output-tree visibility and digest helpers for isolated project test runs."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy

logger = get_logger(__name__)


def _fallback_output_files(output_dir: Path) -> list[Path]:
    """Return every file in an output tree when Git visibility is unavailable."""
    return sorted(
        (path for path in output_dir.rglob("*") if path.is_file() or path.is_symlink()),
        key=lambda path: path.as_posix(),
    )


def _repository_root(path: Path) -> Path | None:
    """Return the nearest Git worktree root for *path*, if one is discoverable."""
    resolved = path.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _visible_output_files(project_root: Path) -> list[Path]:
    """Return tracked and non-ignored untracked files under a project output tree.

    Ignored files are deliberately excluded because the repository contract
    classifies caches, logs, and build intermediates as local-only.  A clean
    checkout is allowed to create those files during a test lane; tracked
    output mutations and non-ignored additions remain visible and fail closed.
    """
    output_dir = project_root / "output"
    if not output_dir.is_dir():
        return []
    repo_root = _repository_root(project_root)
    if repo_root is None:
        return _fallback_output_files(output_dir)
    try:
        relative_output = output_dir.resolve().relative_to(repo_root)
    except ValueError:
        return _fallback_output_files(output_dir)
    result = run_with_policy(
        (
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            relative_output.as_posix(),
        ),
        cwd=repo_root,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        policy=SubprocessPolicy(
            policy_id="output-visibility",
            source_path="infrastructure/core/test_runner_outputs.py",
            timeout_seconds=30,
            capture_output=True,
            credential_free=True,
        ),
    )
    if result.returncode != 0 or result.timed_out:
        logger.warning(
            "Could not determine Git-visible output files for %s; using filesystem fallback",
            output_dir,
        )
        return _fallback_output_files(output_dir)
    stdout = result.stdout or ""
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="surrogateescape")
    files: list[Path] = []
    for entry in stdout.split("\0"):
        if not entry:
            continue
        path = repo_root / entry
        try:
            path.relative_to(output_dir.resolve())
        except ValueError:
            continue
        if path.is_file() or path.is_symlink():
            files.append(path)
    return sorted(files, key=lambda path: path.as_posix())


def output_tree_digest(project_root: Path) -> str:
    """Return a content digest of visible files in a project's ``output/`` tree.

    Git-ignored caches, logs, and build intermediates are excluded to match
    the repository's clean-status contract. A missing output tree uses the
    SHA-256 digest of the empty tree so every executed lane carries an explicit
    output-isolation identity.
    """
    output_dir = project_root / "output"
    if not output_dir.is_dir():
        return hashlib.sha256(b"").hexdigest()
    digest = hashlib.sha256()
    for path in _visible_output_files(project_root):
        relative = path.relative_to(project_root)
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        if path.is_symlink():
            digest.update(b"symlink\0")
            digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
        else:
            digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


__all__ = ["output_tree_digest"]
