"""sync_private_project_links protection tests (formerly part of test_linking.py)."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.linking import (
    ACTIVE_SUBDIR,
    PROTECTED_NAMES,
    WORKING_SUBDIR,
    sync_private_project_links,
)

from ._linking_helpers import _make_project, _make_private, _make_repo


def test_protected_exemplar_never_overwritten(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    # A real exemplar directory with the same name as an (illegal) active source.
    exemplar = next(iter(PROTECTED_NAMES))
    _make_project(repo / "projects" / "active" / exemplar)
    private = _make_private(tmp_path, active=[exemplar], name="priv")
    result = sync_private_project_links(repo, private)
    assert (repo / "projects" / "active" / exemplar).is_dir()
    assert not (repo / "projects" / "active" / exemplar).is_symlink()
    assert any(exemplar in s for s in result.skipped)


def test_real_path_collision_skipped(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A real directory already occupies projects/active/alpha.
    _make_project(repo / "projects" / "active" / "alpha")
    result = sync_private_project_links(repo, private)
    assert (repo / "projects" / "active" / "alpha").is_dir()
    assert not (repo / "projects" / "active" / "alpha").is_symlink()
    assert any("alpha" in s and "real path" in s for s in result.skipped)


def test_md_file_in_active_not_linked(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    (private / ACTIVE_SUBDIR / "README.md").write_text("doc\n", encoding="utf-8")
    sync_private_project_links(repo, private)
    assert not (repo / "projects" / "active" / "README.md").exists()


def test_hidden_dir_in_active_skipped(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    (private / ACTIVE_SUBDIR / ".hidden").mkdir()
    sync_private_project_links(repo, private)
    assert not (repo / "projects" / "active" / ".hidden").exists()


def test_lifecycle_output_dir_is_not_linked_as_project(tmp_path: Path) -> None:
    """Generated lifecycle-level output/ spillover is not a project."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / WORKING_SUBDIR / "alpha")
    (private / WORKING_SUBDIR / "output" / "reports").mkdir(parents=True)

    result = sync_private_project_links(repo, private, dry_run=True)

    assert result.created == ["projects/working/alpha"]
    assert "projects/working/output" not in result.created
