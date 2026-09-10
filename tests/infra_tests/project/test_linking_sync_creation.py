"""sync_private_project_links creation and idempotency tests (formerly part of test_linking.py)."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.discovery import discover_projects
from infrastructure.project.linking import ACTIVE_SUBDIR, sync_private_project_links

from ._linking_helpers import _make_project, _make_private, _make_repo


def test_sync_creates_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    result = sync_private_project_links(repo, private)
    link = repo / "projects" / "active" / "alpha"
    assert link.is_symlink()
    assert result.created == ["projects/active/alpha"]


def test_created_symlink_resolves_to_source(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)
    link = repo / "projects" / "active" / "alpha"
    assert link.resolve() == (private / ACTIVE_SUBDIR / "alpha").resolve()


def test_active_lifecycle_entry_can_be_symlink_to_self_versioned_repo(tmp_path: Path) -> None:
    """A private lifecycle entry may point at a sibling canonical git checkout."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    canonical = _make_project(tmp_path / "AGEINT")
    (private / ACTIVE_SUBDIR / "AGEINT").symlink_to(canonical, target_is_directory=True)

    result = sync_private_project_links(repo, private)
    link = repo / "projects" / "active" / "AGEINT"

    assert result.created == ["projects/active/AGEINT"]
    assert link.is_symlink()
    assert link.resolve() == canonical.resolve()
    assert {p.name for p in discover_projects(repo)} == {"AGEINT"}


def test_sync_is_idempotent(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha", "beta"], name="priv")
    sync_private_project_links(repo, private)
    second = sync_private_project_links(repo, private)
    assert second.created == []
    assert second.updated == []
    assert second.removed == []
