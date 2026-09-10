"""sync_private_project_links prune-safety tests (formerly part of test_linking.py).

The safety-critical guarantee under test: pruning only ever removes lifecycle
links the syncer itself manages and never a real directory, an unmanaged
symlink, or a protected exemplar.
"""

from __future__ import annotations

import os
from pathlib import Path

from infrastructure.project.linking import (
    ACTIVE_SUBDIR,
    ARCHIVE_SUBDIR,
    WORKING_SUBDIR,
    sync_private_project_links,
)

from ._linking_helpers import _make_project, _make_private, _make_repo, _mirror


def test_prune_removes_stale_managed_link(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)
    # alpha leaves active/ (e.g. moved to working/)
    (private / ACTIVE_SUBDIR / "alpha").rename(private / WORKING_SUBDIR / "alpha")
    result = sync_private_project_links(repo, private)
    assert result.removed == ["projects/active/alpha"]
    assert not (repo / "projects" / "active" / "alpha").exists()
    assert not (repo / "projects" / "active" / "alpha").is_symlink()
    assert (repo / "projects" / "working" / "alpha").is_symlink()


def test_prune_leaves_unmanaged_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A symlink to somewhere OUTSIDE the private root must never be pruned.
    outside = tmp_path / "outside_target"
    outside.mkdir()
    foreign = _mirror(repo) / "foreign"
    foreign.symlink_to(outside)
    result = sync_private_project_links(repo, private)
    assert "projects/active/foreign" not in result.removed
    assert foreign.is_symlink()


def test_prune_never_touches_real_directory(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A real directory under the active mirror (e.g. a native project).
    real = repo / "projects" / "active" / "native_proj"
    _make_project(real)
    sync_private_project_links(repo, private)
    assert real.is_dir() and not real.is_symlink()
    assert (real / "src" / "calc.py").exists()


def test_no_prune_keeps_stale_link(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    sync_private_project_links(repo, private)
    (private / ACTIVE_SUBDIR / "alpha").rename(private / ARCHIVE_SUBDIR / "alpha")
    result = sync_private_project_links(repo, private, prune=False)
    assert result.removed == []
    # The now-broken symlink survives (prune disabled).
    assert (repo / "projects" / "active" / "alpha").is_symlink()
    assert (repo / "projects" / "archive" / "alpha").is_symlink()


def test_repoint_managed_stale_symlink(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    # A MANAGED link (points into active/) but at a stale/missing target.
    link = _mirror(repo) / "alpha"
    link.symlink_to(private / ACTIVE_SUBDIR / "ghost")
    result = sync_private_project_links(repo, private)
    assert result.updated == ["projects/active/alpha"]
    assert link.resolve() == (private / ACTIVE_SUBDIR / "alpha").resolve()


def test_source_symlink_uses_lifecycle_entry_and_prunes(tmp_path: Path) -> None:
    """Self-versioned source repos still get lifecycle-managed links."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    external = tmp_path / "external_notes"
    _make_project(external)
    lifecycle_entry = private / WORKING_SUBDIR / "notes"
    lifecycle_entry.symlink_to(external)

    result = sync_private_project_links(repo, private)
    link = repo / "projects" / "working" / "notes"

    assert result.created == ["projects/working/notes"]
    assert Path(os.readlink(link)) == lifecycle_entry
    assert link.resolve() == external.resolve()

    lifecycle_entry.unlink()
    second = sync_private_project_links(repo, private)
    assert second.removed == ["projects/working/notes"]
    assert not link.is_symlink()


def test_old_direct_self_versioned_link_is_repointed_to_lifecycle_entry(tmp_path: Path) -> None:
    """Links made by the old resolved-target behavior are normalized."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    external = tmp_path / "external_alpha"
    _make_project(external)
    lifecycle_entry = private / ACTIVE_SUBDIR / "alpha"
    lifecycle_entry.symlink_to(external)
    old_link = _mirror(repo) / "alpha"
    old_link.symlink_to(external)

    result = sync_private_project_links(repo, private)

    assert result.updated == ["projects/active/alpha"]
    assert Path(os.readlink(old_link)) == lifecycle_entry
    assert old_link.resolve() == external.resolve()


def test_unmanaged_symlink_collision_not_clobbered(tmp_path: Path) -> None:
    """Forge finding #3: a foreign same-named symlink must not be repointed."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    external = tmp_path / "external_alpha"
    _make_project(external)
    link = _mirror(repo) / "alpha"
    link.symlink_to(external)  # points OUTSIDE the private root
    result = sync_private_project_links(repo, private)
    assert any("alpha" in s and "unmanaged" in s for s in result.skipped)
    assert link.resolve() == external.resolve()  # left untouched


def test_link_into_other_lifecycle_not_pruned(tmp_path: Path) -> None:
    """Forge finding #2: a user link into the wrong mirror is unmanaged, never pruned."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    _make_project(private / WORKING_SUBDIR / "notes")
    # A user link sitting in the active mirror but pointing at a working source
    # is a lifecycle mismatch — unmanaged, so it is never pruned.
    userlink = _mirror(repo) / "notes"
    userlink.symlink_to(private / WORKING_SUBDIR / "notes")
    result = sync_private_project_links(repo, private)
    assert "projects/active/notes" not in result.removed
    assert userlink.is_symlink()
    assert (repo / "projects" / "working" / "notes").is_symlink()


def test_broken_link_outside_active_not_pruned(tmp_path: Path) -> None:
    """A broken symlink whose target was OUTSIDE active/ must never be pruned."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    gone = tmp_path / "gone_external"  # never existed under active/
    broken = _mirror(repo) / "orphan"
    broken.symlink_to(gone)  # broken link pointing outside the private root
    result = sync_private_project_links(repo, private)
    assert "projects/active/orphan" not in result.removed
    assert broken.is_symlink()  # left intact


def test_symlink_loop_does_not_crash(tmp_path: Path) -> None:
    """Forge finding #1: a symlink loop under projects/ must not crash the sync."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, active=["alpha"], name="priv")
    mirror = _mirror(repo)
    loop_a = mirror / "loop_a"
    loop_b = mirror / "loop_b"
    loop_a.symlink_to(loop_b)
    loop_b.symlink_to(loop_a)
    # Must not raise RuntimeError("Symlink loop") — and still link alpha.
    result = sync_private_project_links(repo, private)
    assert "projects/active/alpha" in result.created
    assert "projects/active/loop_a" not in result.removed
    assert "projects/active/loop_b" not in result.removed
