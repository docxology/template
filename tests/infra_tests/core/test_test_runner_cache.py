"""Negative controls for isolated-matrix cache identity."""

from __future__ import annotations

import subprocess
from pathlib import Path

from infrastructure.core.test_runner_cache import _cache_identity_inputs


def _git_repo(tmp_path: Path) -> Path:
    """Create a minimal checkout whose index and worktree can be varied."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "cache@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Cache Test"], cwd=tmp_path, check=True)
    (tmp_path / "src.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "src.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=tmp_path, check=True)
    return tmp_path


def _identity(repo: Path) -> dict[str, str]:
    return _cache_identity_inputs(
        repo,
        profile="quick",
        marker_expr=None,
        worker_info="outer=serial, inner=none",
        project_names=("templates/example",),
    )


def test_cache_identity_exposes_index_worktree_and_untracked_states(tmp_path: Path) -> None:
    identity = _identity(_git_repo(tmp_path))

    assert identity["commit"] != "unknown"
    assert len(identity["index_state"]) == 64
    assert len(identity["worktree_state"]) == 64
    assert len(identity["untracked_state"]) == 64
    assert len(identity["index_worktree"]) == 64


def test_staged_and_unstaged_changes_invalidate_distinct_cache_inputs(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    baseline = _identity(repo)

    (repo / "src.py").write_text("VALUE = 2\n", encoding="utf-8")
    staged = _identity(repo)
    assert staged["worktree_state"] != baseline["worktree_state"]

    subprocess.run(["git", "add", "src.py"], cwd=repo, check=True)
    (repo / "src.py").write_text("VALUE = 3\n", encoding="utf-8")
    mixed = _identity(repo)
    assert mixed["index_state"] != baseline["index_state"]
    assert mixed["worktree_state"] != staged["worktree_state"]


def test_nonignored_untracked_content_is_part_of_cache_identity(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    baseline = _identity(repo)
    new_file = repo / "new_source.py"
    new_file.write_text("VALUE = 4\n", encoding="utf-8")
    changed = _identity(repo)

    assert changed["untracked_state"] != baseline["untracked_state"]
    assert changed["index_worktree"] != baseline["index_worktree"]
