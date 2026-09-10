"""is_managed_symlink classification tests (formerly part of test_linking.py)."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.linking import is_managed_symlink, sync_private_project_links

from ._linking_helpers import _make_project, _make_private, _make_repo


def test_is_managed_symlink_true_for_in_private(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)
    assert is_managed_symlink(repo / "projects" / "active" / "alpha", private.resolve())


def test_is_managed_symlink_false_for_real_dir(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=[], name="priv")
    real = repo / "projects" / "active" / "native"
    _make_project(real)
    assert not is_managed_symlink(real, private.resolve())
