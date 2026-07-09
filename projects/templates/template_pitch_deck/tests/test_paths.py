"""No-mocks tests for src/paths.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from paths import locate_repo_root, project_root


def test_locate_repo_root_finds_real_repo_from_this_project():
    root = locate_repo_root(project_root())
    assert (root / "infrastructure").is_dir()
    assert (root / "pyproject.toml").is_file()


def test_locate_repo_root_sibling_fallback(tmp_path: Path):
    # `locate_repo_root` falls back to checking parents[2] / "template" — the
    # standalone-checkout convention where a project's own repo (e.g. a
    # `template_pitch_deck` standalone clone) sits as a sibling of the
    # monorepo checkout (named "template") under a common parent directory.
    # No infrastructure/ exists anywhere upward from `start` itself; only the
    # sibling "template" directory has one.
    fake_monorepo = tmp_path / "template"
    (fake_monorepo / "infrastructure").mkdir(parents=True)
    start = tmp_path / "standalone_checkout" / "a" / "b"
    start.mkdir(parents=True)

    found = locate_repo_root(start)
    assert found == fake_monorepo.resolve()


def test_locate_repo_root_raises_when_nothing_found(tmp_path: Path):
    isolated = tmp_path / "nowhere" / "near" / "a" / "repo"
    isolated.mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        locate_repo_root(isolated)


def test_locate_repo_root_raises_cleanly_on_shallow_path_with_few_parents():
    """A path shallow enough that `parents[2]` would raise IndexError must
    still surface the intended FileNotFoundError, not an IndexError."""
    with pytest.raises(FileNotFoundError):
        locate_repo_root(Path("/"))


def test_project_root_returns_template_pitch_deck_directory():
    # The standalone GitHub repo is legitimately named `template-pitch-deck`
    # (hyphenated, matching every other exemplar's repo-slug convention),
    # while the monorepo checkout uses `template_pitch_deck` (underscored,
    # matching the Python package name) — accept either so this test is
    # true from both deployment contexts, not just the monorepo one.
    root = project_root()
    assert root.name in ("template_pitch_deck", "template-pitch-deck")
    assert (root / "src").is_dir()
    assert (root / "manuscript").is_dir()
