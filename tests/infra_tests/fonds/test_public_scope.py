"""Tests for public template fond scoping."""

from __future__ import annotations

from pathlib import Path

from infrastructure.fonds.discovery import discover_fonds
from infrastructure.fonds.public_scope import (
    PUBLIC_FOND_NAMES,
    _format_paths,
    public_fond_data_paths,
    public_fond_infos,
    public_fond_names,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_public_fond_names_constant_contains_bibliography() -> None:
    """PUBLIC_FOND_NAMES is the canonical roster and includes the bibliography fond."""
    assert "templates/template_bibliography" in PUBLIC_FOND_NAMES
    assert "templates/template_contacts" in PUBLIC_FOND_NAMES
    assert "templates/template_datasets" in PUBLIC_FOND_NAMES


def test_public_fond_infos_filters_to_public_roster() -> None:
    """public_fond_infos returns only fonds in PUBLIC_FOND_NAMES."""
    infos = public_fond_infos(REPO_ROOT)
    allowed = set(PUBLIC_FOND_NAMES)
    for info in infos:
        assert info.qualified_name in allowed
    # All three public fonds should be discoverable in the real repo.
    assert len(infos) == len(PUBLIC_FOND_NAMES)


def test_public_fond_infos_excludes_non_public(tmp_path: Path) -> None:
    """A fond outside PUBLIC_FOND_NAMES is excluded from public_fond_infos."""
    # Create a public exemplar fond structure.
    _scaffold_fond(tmp_path, "templates/template_bibliography")
    # Create a non-public fond that discovery will find.
    _scaffold_fond(tmp_path, "working/private_fond")

    infos = public_fond_infos(tmp_path)
    names = [info.qualified_name for info in infos]
    assert "working/private_fond" not in names
    assert "templates/template_bibliography" in names


def test_public_fond_names_returns_sorted_list() -> None:
    """public_fond_names returns a sorted list of qualified names."""
    names = public_fond_names(REPO_ROOT)
    assert names == sorted(names)
    assert "templates/template_bibliography" in names


def test_public_fond_data_paths_returns_repo_relative_paths() -> None:
    """public_fond_data_paths returns repo-relative data/ paths for public fonds."""
    paths = public_fond_data_paths(REPO_ROOT)
    # Each path is repo-relative and ends with /data
    for path in paths:
        assert path.as_posix().startswith("fonds/templates/")
        assert path.as_posix().endswith("/data")
    # All three public fonds should have data directories in the real repo.
    assert len(paths) == len(PUBLIC_FOND_NAMES)


def test_public_fond_data_paths_skips_missing_dirs(tmp_path: Path) -> None:
    """public_fond_data_paths only returns paths for data/ dirs that exist on disk."""
    # Only create one fond's data directory.
    (tmp_path / "fonds" / "templates" / "template_bibliography" / "data").mkdir(parents=True)

    paths = public_fond_data_paths(tmp_path)
    assert len(paths) == 1
    assert paths[0] == Path("fonds/templates/template_bibliography/data")


def test_format_paths_joins_with_spaces() -> None:
    """_format_paths joins paths with spaces using POSIX separators."""
    paths = [Path("a/b"), Path("c/d/e")]
    result = _format_paths(paths)
    assert result == "a/b c/d/e"


def test_format_paths_empty_sequence() -> None:
    """_format_paths returns empty string for empty input."""
    assert _format_paths([]) == ""


def test_discover_fonds_sees_more_than_public_in_real_repo() -> None:
    """In the real repo, discover_fonds may see private fonds, but public scope filters them."""
    all_fonds = discover_fonds(REPO_ROOT)
    public_infos = public_fond_infos(REPO_ROOT)
    public_names = {info.qualified_name for info in public_infos}
    # All public infos are a subset of all discovered fonds.
    assert public_names <= {fond.qualified_name for fond in all_fonds}


def _scaffold_fond(root: Path, qualified_name: str) -> Path:
    """Create a minimum-valid fond directory with fonds.yaml and data/."""
    fond_dir = root / "fonds" / qualified_name
    fond_dir.mkdir(parents=True, exist_ok=True)
    (fond_dir / "fonds.yaml").write_text("type: generic\n", encoding="utf-8")
    (fond_dir / "data").mkdir(exist_ok=True)
    return fond_dir
