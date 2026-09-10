"""unmanaged_project_mirror_entries mirror-shape guard tests (formerly part of test_linking.py)."""

from __future__ import annotations

from pathlib import Path


from infrastructure.project.linking import (
    ARCHIVE_SUBDIR,
    ENV_VAR,
    PROTECTED_NAMES,
    WORKING_SUBDIR,
    sync_private_project_links,
    unmanaged_project_mirror_entries,
)

from ._linking_helpers import _make_project, _make_private, _make_repo, _mirror


def test_mirror_guard_clean_after_sync(tmp_path: Path) -> None:
    """A freshly synced mirror has no unmanaged entries."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / WORKING_SUBDIR / "alpha")
    _make_project(private / ARCHIVE_SUBDIR / "omega")
    sync_private_project_links(repo, private)

    assert unmanaged_project_mirror_entries(repo, private) == []


def test_mirror_guard_flags_real_directory(tmp_path: Path) -> None:
    """A real project directory in the mirror is the leak the syncer cannot see."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    sync_private_project_links(repo, private)
    _make_project(_mirror(repo, WORKING_SUBDIR) / "smuggled")

    offenders = unmanaged_project_mirror_entries(repo, private)
    assert [item.path for item in offenders] == ["projects/working/smuggled"]
    assert "real directory" in offenders[0].reason

    # ...and the syncer really is blind to it, which is why the guard exists.
    sync_private_project_links(repo, private)
    assert (repo / "projects" / WORKING_SUBDIR / "smuggled").is_dir()


def test_mirror_guard_flags_regular_file(tmp_path: Path) -> None:
    """Mirror dirs hold symlinks only; a stray file is reported."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    sync_private_project_links(repo, private)
    (_mirror(repo, WORKING_SUBDIR) / "NOTES.md").write_text("private\n", encoding="utf-8")

    offenders = unmanaged_project_mirror_entries(repo, private)
    assert [item.path for item in offenders] == ["projects/working/NOTES.md"]
    assert "regular file" in offenders[0].reason


def test_mirror_guard_flags_foreign_symlink(tmp_path: Path) -> None:
    """A link out of the private lifecycle subtree is not a managed link."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    sync_private_project_links(repo, private)
    elsewhere = _make_project(tmp_path / "elsewhere" / "rogue")
    (_mirror(repo, WORKING_SUBDIR) / "rogue").symlink_to(elsewhere)

    offenders = unmanaged_project_mirror_entries(repo, private)
    assert [item.path for item in offenders] == ["projects/working/rogue"]
    assert "outside its private lifecycle subtree" in offenders[0].reason


def test_mirror_guard_recurses_into_category_groups(tmp_path: Path) -> None:
    """``_Category/`` dirs are containers: they pass, their contents are checked."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    _make_project(private / ARCHIVE_SUBDIR / "_Group" / "linked")
    sync_private_project_links(repo, private)
    assert unmanaged_project_mirror_entries(repo, private) == []

    _make_project(repo / "projects" / ARCHIVE_SUBDIR / "_Group" / "smuggled")
    offenders = unmanaged_project_mirror_entries(repo, private)
    assert [item.path for item in offenders] == ["projects/archive/_Group/smuggled"]


def test_mirror_guard_ignores_output_and_dotfiles(tmp_path: Path) -> None:
    """Generated ``output/`` and dot-entries are not confidentiality findings."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    sync_private_project_links(repo, private)
    mirror = _mirror(repo, WORKING_SUBDIR)
    (mirror / "output").mkdir()
    (mirror / ".DS_Store").write_text("", encoding="utf-8")

    assert unmanaged_project_mirror_entries(repo, private) == []


def test_mirror_guard_noop_without_private_root(tmp_path: Path, monkeypatch) -> None:
    """A clean public clone has no mirror to police, so the guard is a no-op."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    repo = _make_repo(tmp_path)
    _make_project(repo / "projects" / WORKING_SUBDIR / "smuggled")

    assert unmanaged_project_mirror_entries(repo) == []


def test_mirror_guard_skips_protected_exemplars(tmp_path: Path) -> None:
    """Public canonical exemplars are repo content, not mirror entries."""
    repo = _make_repo(tmp_path)
    private = _make_private(tmp_path, name="priv")
    sync_private_project_links(repo, private)
    exemplar = sorted(PROTECTED_NAMES)[0]
    _make_project(_mirror(repo, WORKING_SUBDIR) / exemplar)

    assert unmanaged_project_mirror_entries(repo, private) == []
