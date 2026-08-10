"""Cache identity helpers for the isolated public-project test matrix."""

from __future__ import annotations

import hashlib
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Sequence

from infrastructure.core.subprocess_policy import SubprocessPolicy, run_with_policy


def _run_git_metadata(repo_root: Path, args: list[str]) -> str:
    """Return one bounded git metadata payload for cache identity construction."""
    try:
        completed = run_with_policy(
            ["git", *args],
            cwd=repo_root,
            env=None,
            policy=SubprocessPolicy(
                policy_id="git-cache-identity",
                source_path="infrastructure/core/test_runner_cache.py",
                timeout_seconds=30,
                capture_output=True,
            ),
        )
    except (OSError, ValueError):
        return "unavailable"
    if completed.returncode != 0:
        return "unavailable"
    return completed.stdout


def _digest_files(repo_root: Path, relative_paths: Sequence[Path]) -> str:
    """Hash the named lock/config files with paths and content in stable order."""
    digest = hashlib.sha256()
    for relative in sorted(set(relative_paths)):
        path = repo_root / relative
        if not path.is_file():
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _cache_identity_inputs(
    repo_root: Path,
    *,
    profile: str,
    marker_expr: str | None,
    worker_info: str,
    project_names: Sequence[str],
) -> dict[str, str]:
    """Collect the state that makes a project-matrix result reusable."""
    # Keep the three Git states separately addressable.  ``git diff HEAD`` is
    # useful as a combined digest, but it is not an adequate diagnostic when a
    # cached result changes: a staged edit and an unstaged edit can otherwise
    # look identical in a receipt.  The explicit fields also make cache
    # invalidation auditable for callers that persist matrix receipts.
    index_diff = _run_git_metadata(repo_root, ["diff", "--cached", "--binary", "--"])
    worktree_diff = _run_git_metadata(repo_root, ["diff", "--binary", "HEAD", "--"])
    status = _run_git_metadata(repo_root, ["status", "--porcelain=v1", "--untracked-files=all", "-z", "--"])
    untracked = _run_git_metadata(repo_root, ["ls-files", "--others", "--exclude-standard", "-z", "--"])
    source_digest = hashlib.sha256()
    for payload in (index_diff, worktree_diff, status):
        source_digest.update(payload.encode("utf-8", errors="replace"))
        source_digest.update(b"\0")
    untracked_digest = hashlib.sha256()
    ignored_parts = {".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
    for relative in sorted(item for item in untracked.split("\0") if item):
        path = repo_root / relative
        if not path.is_file() or any(part in ignored_parts for part in path.parts):
            continue
        untracked_digest.update(relative.encode("utf-8"))
        untracked_digest.update(b"\0")
        untracked_digest.update(path.read_bytes())
        untracked_digest.update(b"\0")
        source_digest.update(relative.encode("utf-8"))
        source_digest.update(b"\0")
        source_digest.update(path.read_bytes())
        source_digest.update(b"\0")

    lockfiles = [Path("pyproject.toml"), Path("uv.lock")]
    lockfiles.extend(
        path.relative_to(repo_root) for path in sorted((repo_root / "projects" / "templates").glob("*/pyproject.toml"))
    )
    tools: dict[str, str] = {}
    for package in (
        "pytest",
        "coverage",
        "pytest-cov",
        "pytest-xdist",
        "pytest-timeout",
        "pytest-benchmark",
        "ruff",
        "mypy",
        "bandit",
    ):
        try:
            tools[package] = version(package)
        except PackageNotFoundError:
            tools[package] = "unavailable"
    return {
        "commit": _resolve_roster_revision(repo_root),
        "index_worktree": source_digest.hexdigest(),
        "index_state": hashlib.sha256(index_diff.encode("utf-8", errors="replace")).hexdigest(),
        "worktree_state": hashlib.sha256(worktree_diff.encode("utf-8", errors="replace")).hexdigest(),
        "untracked_state": untracked_digest.hexdigest(),
        "interpreter": f"{sys.executable}|{platform.python_implementation()}|{platform.python_version()}",
        "lockfiles": _digest_files(repo_root, lockfiles),
        "profile": profile,
        "marker_expression": marker_expr or "",
        "worker_info": worker_info,
        "project_names": ",".join(sorted(project_names)),
        "tool_versions": ";".join(f"{key}={value}" for key, value in sorted(tools.items())),
    }


def _resolve_roster_revision(repo_root: Path) -> str:
    """Return the current git commit SHA, or ``"unknown"`` outside a checkout."""
    try:
        completed = run_with_policy(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            env=None,
            policy=SubprocessPolicy(
                policy_id="git-metadata-test-runner",
                source_path="infrastructure/core/test_runner_cache.py",
                timeout_seconds=30,
                capture_output=True,
            ),
        )
    except (OSError, ValueError):
        return "unknown"
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip() or "unknown"


__all__ = ["_cache_identity_inputs", "_resolve_roster_revision"]
