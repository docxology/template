"""Tests for fonds discovery and confidentiality guards.

All tests use real tmp_path directories — no mocks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.fonds.public_scope import PUBLIC_FOND_NAMES


# =============================================================================
# Helpers
# =============================================================================


def _make_fond(path: Path) -> Path:
    """A minimal valid fond (fonds.yaml + data/)."""
    (path / "data").mkdir(parents=True)
    yaml_content = (
        "type: bibliography\n"
        "description: Test bibliography fond\n"
        "version: '1.0'\n"
    )
    (path / "fonds.yaml").write_text(yaml_content, encoding="utf-8")
    (path / "data" / "references.bib").write_text("", encoding="utf-8")
    return path


# =============================================================================
# PUBLIC_FOND_NAMES
# =============================================================================


def test_public_fond_names_is_tuple() -> None:
    """PUBLIC_FOND_NAMES must be a tuple (not a list or set)."""
    assert isinstance(PUBLIC_FOND_NAMES, tuple)


def test_public_fond_names_contains_only_strings() -> None:
    """Every entry in PUBLIC_FOND_NAMES must be a non-empty string."""
    for name in PUBLIC_FOND_NAMES:
        assert isinstance(name, str)
        assert name, "PUBLIC_FOND_NAMES must not contain empty strings"


def test_public_fond_names_no_path_separators() -> None:
    """Fond names in the roster follow the qualified-name convention.

    Entries may be bare (``bibliography``) or qualified with a subfolder
    (``templates/template_bibliography``), matching the convention used by
    ``infrastructure.project.public_scope.PUBLIC_PROJECT_NAMES``. What they
    must NOT be is absolute paths (starting with ``/``) or dotted relative paths
    (``../``).
    """
    for name in PUBLIC_FOND_NAMES:
        assert not name.startswith("/"), (
            f"PUBLIC_FOND_NAMES entry {name!r} must not be an absolute path"
        )
        assert not name.startswith(".."), (
            f"PUBLIC_FOND_NAMES entry {name!r} must not start with '..'"
        )
        assert "\\" not in name, (
            f"PUBLIC_FOND_NAMES entry {name!r} must not contain backslashes"
        )


# =============================================================================
# _make_fond helper
# =============================================================================


def test_make_fond_creates_required_structure(tmp_path: Path) -> None:
    """_make_fond produces a directory with fonds.yaml and data/."""
    fond_dir = tmp_path / "test_fond"
    _make_fond(fond_dir)

    assert fond_dir.is_dir()
    assert (fond_dir / "fonds.yaml").is_file()
    assert (fond_dir / "data").is_dir()
    assert (fond_dir / "data" / "references.bib").is_file()


def test_make_fond_yaml_content(tmp_path: Path) -> None:
    """fonds.yaml written by _make_fond contains the expected fields."""
    fond_dir = tmp_path / "yaml_test"
    _make_fond(fond_dir)

    content = (fond_dir / "fonds.yaml").read_text(encoding="utf-8")
    assert "type:" in content
    assert "description:" in content
    assert "version:" in content


def test_make_fond_returns_path(tmp_path: Path) -> None:
    """_make_fond returns the fond directory path."""
    fond_dir = tmp_path / "return_test"
    result = _make_fond(fond_dir)
    assert result == fond_dir


# =============================================================================
# fonds.yaml structure
# =============================================================================


def test_fond_missing_yaml_is_invalid(tmp_path: Path) -> None:
    """A directory without fonds.yaml is not a valid fond."""
    fond_dir = tmp_path / "no_yaml"
    fond_dir.mkdir()
    (fond_dir / "data").mkdir()

    assert not (fond_dir / "fonds.yaml").exists()


def test_fond_missing_data_dir(tmp_path: Path) -> None:
    """A fond directory without data/ is missing its required data pool."""
    fond_dir = tmp_path / "no_data"
    fond_dir.mkdir()
    (fond_dir / "fonds.yaml").write_text(
        "type: contacts\ndescription: Missing data dir\nversion: '1.0'\n",
        encoding="utf-8",
    )

    assert not (fond_dir / "data").is_dir()


def test_fond_can_have_multiple_data_files(tmp_path: Path) -> None:
    """A fond may contain multiple files under data/."""
    fond_dir = tmp_path / "multi_data"
    _make_fond(fond_dir)
    (fond_dir / "data" / "extra.bib").write_text("", encoding="utf-8")
    (fond_dir / "data" / "notes.txt").write_text("notes\n", encoding="utf-8")

    data_files = list((fond_dir / "data").iterdir())
    assert len(data_files) >= 2


# =============================================================================
# offending_tracked_fonds — unit tests over the logic (no real git repo needed)
# =============================================================================


def test_offending_tracked_fonds_imports() -> None:
    """offending_tracked_fonds must be importable from infrastructure.project.git_guards."""
    from infrastructure.project.git_guards import offending_tracked_fonds  # noqa: F401


def test_allowed_fonds_toplevel_files_is_frozenset() -> None:
    """ALLOWED_FONDS_TOPLEVEL_FILES must be a frozenset of strings."""
    from infrastructure.project.git_guards import ALLOWED_FONDS_TOPLEVEL_FILES

    assert isinstance(ALLOWED_FONDS_TOPLEVEL_FILES, frozenset)
    for item in ALLOWED_FONDS_TOPLEVEL_FILES:
        assert isinstance(item, str)


def test_allowed_fonds_toplevel_files_contains_expected_entries() -> None:
    """The standard navigation docs must be in ALLOWED_FONDS_TOPLEVEL_FILES."""
    from infrastructure.project.git_guards import ALLOWED_FONDS_TOPLEVEL_FILES

    assert "fonds/README.md" in ALLOWED_FONDS_TOPLEVEL_FILES
    assert "fonds/AGENTS.md" in ALLOWED_FONDS_TOPLEVEL_FILES


def test_allowed_fond_dirs_is_tuple() -> None:
    """ALLOWED_FOND_DIRS must be a tuple of path prefix strings."""
    from infrastructure.project.git_guards import ALLOWED_FOND_DIRS

    assert isinstance(ALLOWED_FOND_DIRS, tuple)
    for item in ALLOWED_FOND_DIRS:
        assert isinstance(item, str)
        assert item.startswith("fonds/"), f"Expected 'fonds/' prefix, got {item!r}"
        assert item.endswith("/"), f"Expected trailing slash, got {item!r}"


def test_allowed_fond_dirs_derived_from_public_fond_names() -> None:
    """ALLOWED_FOND_DIRS entries must correspond to PUBLIC_FOND_NAMES."""
    from infrastructure.project.git_guards import ALLOWED_FOND_DIRS

    expected = tuple(f"fonds/{name}/" for name in PUBLIC_FOND_NAMES)
    assert ALLOWED_FOND_DIRS == expected


def test_offending_tracked_fonds_logic_allows_toplevel_docs(tmp_path: Path) -> None:
    """Paths in ALLOWED_FONDS_TOPLEVEL_FILES are never reported as offenders."""
    from infrastructure.project.git_guards import (
        ALLOWED_FOND_DIRS,
        ALLOWED_FONDS_TOPLEVEL_FILES,
    )

    # Simulate the classification logic directly (without git)
    paths_to_check = list(ALLOWED_FONDS_TOPLEVEL_FILES) + [
        "fonds/secret_data/raw.csv",
        "fonds/private_bibliography/fonds.yaml",
    ]

    offenders: list[str] = []
    for path in paths_to_check:
        normalized = path.replace("\\", "/")
        if normalized in ALLOWED_FONDS_TOPLEVEL_FILES:
            continue
        if any(normalized.startswith(prefix) for prefix in ALLOWED_FOND_DIRS):
            continue
        offenders.append(normalized)

    # The toplevel docs must NOT be offenders
    for doc in ALLOWED_FONDS_TOPLEVEL_FILES:
        assert doc not in offenders

    # Any path not in the allowlist that isn't under a public fond dir IS an offender
    assert "fonds/secret_data/raw.csv" in offenders
    assert "fonds/private_bibliography/fonds.yaml" in offenders


def test_offending_tracked_fonds_allows_public_fond_dirs(tmp_path: Path) -> None:
    """Paths under ALLOWED_FOND_DIRS are never reported as offenders."""
    from infrastructure.project.git_guards import (
        ALLOWED_FOND_DIRS,
        ALLOWED_FONDS_TOPLEVEL_FILES,
    )

    # Only meaningful when there are public fonds
    if not ALLOWED_FOND_DIRS:
        pytest.skip("No public fonds registered in PUBLIC_FOND_NAMES; skip path-prefix test")

    allowed_paths = [f"{prefix}fonds.yaml" for prefix in ALLOWED_FOND_DIRS]

    offenders: list[str] = []
    for path in allowed_paths:
        normalized = path.replace("\\", "/")
        if normalized in ALLOWED_FONDS_TOPLEVEL_FILES:
            continue
        if any(normalized.startswith(prefix) for prefix in ALLOWED_FOND_DIRS):
            continue
        offenders.append(normalized)

    assert not offenders, f"Allowed fond paths incorrectly flagged: {offenders}"


def test_offending_tracked_fonds_runs_against_real_repo() -> None:
    """offending_tracked_fonds runs against the real repo root without crashing.

    This test requires git. It verifies the function is callable and returns a
    list — it does NOT assert that the list is empty (the repo may have WIP
    fonds tracked during development).
    """
    import subprocess

    # Locate repo root — skip if git is unavailable
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            check=True,
        )
        repo_root = Path(result.stdout.decode().strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("git not available or not inside a git repo")

    from infrastructure.project.git_guards import offending_tracked_fonds

    offenders = offending_tracked_fonds(repo_root)
    assert isinstance(offenders, list)
    for item in offenders:
        assert isinstance(item, str)
