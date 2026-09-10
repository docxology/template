"""Leading-underscore category grouping tests (formerly part of test_linking.py)."""

from __future__ import annotations

import shutil
from pathlib import Path

from infrastructure.project.linking import ARCHIVE_SUBDIR, sync_private_project_links

from ._linking_helpers import _make_project, _make_private, _make_repo, _mirror


def test_category_grouping_creates_nested_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ARCHIVE_SUBDIR / "_legal" / "foo_project")

    result = sync_private_project_links(repo, private)
    link = repo / "projects" / "archive" / "_legal" / "foo_project"

    assert result.created == ["projects/archive/_legal/foo_project"]
    assert link.is_symlink()
    assert link.resolve() == (private / ARCHIVE_SUBDIR / "_legal" / "foo_project").resolve()


def test_category_grouping_qualified_name_resolves(tmp_path: Path) -> None:
    from infrastructure.core.project_paths import resolve_project_root

    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ARCHIVE_SUBDIR / "_legal" / "foo_project")
    sync_private_project_links(repo, private)

    resolved = resolve_project_root(repo, "archive/_legal/foo_project")
    assert resolved.resolve() == (private / ARCHIVE_SUBDIR / "_legal" / "foo_project").resolve()


def test_flat_and_category_projects_coexist_in_same_lifecycle(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ARCHIVE_SUBDIR / "old_flat")
    _make_project(private / ARCHIVE_SUBDIR / "_legal" / "foo_project")

    result = sync_private_project_links(repo, private)

    assert set(result.created) == {"projects/archive/old_flat", "projects/archive/_legal/foo_project"}
    assert (repo / "projects" / "archive" / "old_flat").is_symlink()
    assert (repo / "projects" / "archive" / "_legal" / "foo_project").is_symlink()


def test_category_grouping_sync_is_idempotent(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ARCHIVE_SUBDIR / "_legal" / "foo_project")
    sync_private_project_links(repo, private)
    second = sync_private_project_links(repo, private)
    assert second.created == []
    assert second.updated == []
    assert second.removed == []


def test_category_grouping_prune_removes_stale_link_and_empty_category(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ARCHIVE_SUBDIR / "_legal" / "foo_project")
    sync_private_project_links(repo, private)
    category_dir = repo / "projects" / "archive" / "_legal"
    assert category_dir.is_dir()

    # foo_project leaves the archive entirely (e.g. deleted upstream).
    shutil.rmtree(private / ARCHIVE_SUBDIR / "_legal")
    result = sync_private_project_links(repo, private)

    assert result.removed == ["projects/archive/_legal/foo_project"]
    assert not (category_dir / "foo_project").exists()
    assert not category_dir.exists()  # emptied category dir is tidied up


def test_category_grouping_prune_keeps_sibling_in_same_category(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ARCHIVE_SUBDIR / "_legal" / "foo_project")
    _make_project(private / ARCHIVE_SUBDIR / "_legal" / "bar_project")
    sync_private_project_links(repo, private)

    shutil.rmtree(private / ARCHIVE_SUBDIR / "_legal" / "foo_project")
    result = sync_private_project_links(repo, private)

    assert result.removed == ["projects/archive/_legal/foo_project"]
    category_dir = repo / "projects" / "archive" / "_legal"
    assert category_dir.is_dir()  # not tidied up — bar_project still lives here
    assert (category_dir / "bar_project").is_symlink()


def test_category_nesting_is_only_one_level_deep(tmp_path: Path) -> None:
    """A category's own children are never treated as further categories."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ARCHIVE_SUBDIR / "_legal" / "_sub" / "deep_project")

    result = sync_private_project_links(repo, private)

    # "_sub" is mirrored as a single opaque entry under "_legal/", not expanded
    # into "_legal/_sub/deep_project".
    assert result.created == ["projects/archive/_legal/_sub"]
    link = repo / "projects" / "archive" / "_legal" / "_sub"
    assert link.is_symlink()
    assert link.resolve() == (private / ARCHIVE_SUBDIR / "_legal" / "_sub").resolve()


def test_category_grouping_hidden_dir_skipped(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    (private / ARCHIVE_SUBDIR / "_legal").mkdir(parents=True)
    (private / ARCHIVE_SUBDIR / "_legal" / ".hidden").mkdir()
    result = sync_private_project_links(repo, private)
    assert not (repo / "projects" / "archive" / "_legal" / ".hidden").exists()
    assert result.created == []


def test_category_grouping_output_dir_grandchild_not_linked(tmp_path: Path) -> None:
    """A generated ``output/`` spillover inside a category is not a project."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ARCHIVE_SUBDIR / "_legal" / "foo_project")
    (private / ARCHIVE_SUBDIR / "_legal" / "output" / "reports").mkdir(parents=True)

    result = sync_private_project_links(repo, private, dry_run=True)

    assert result.created == ["projects/archive/_legal/foo_project"]
    assert "projects/archive/_legal/output" not in result.created


def test_prune_never_rmdirs_unmanaged_empty_category_dir(tmp_path: Path) -> None:
    """An unmanaged, user-created empty ``_``-prefixed real dir is never removed."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    unmanaged = _mirror(repo) / "_notes"
    unmanaged.mkdir()
    result = sync_private_project_links(repo, private)
    assert unmanaged.is_dir()
    assert "projects/active/_notes" not in result.removed


def test_prune_removes_category_dir_only_after_it_empties_from_pruning(tmp_path: Path) -> None:
    """A category dir IS removed once the prune itself empties it of managed links."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ARCHIVE_SUBDIR / "_legal" / "foo_project")
    sync_private_project_links(repo, private)
    category_dir = repo / "projects" / "archive" / "_legal"
    assert category_dir.is_dir()

    shutil.rmtree(private / ARCHIVE_SUBDIR / "_legal")
    result = sync_private_project_links(repo, private)

    assert result.removed == ["projects/archive/_legal/foo_project"]
    assert not category_dir.exists()  # emptied BY this prune — removed as tidy-up
