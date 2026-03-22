"""Tests for ``newspaper.sections``."""

from pathlib import Path

import pytest

from newspaper.sections import (
    PAGE_SLICES,
    manuscript_filenames,
    slice_stems,
    validate_inventory,
)


def test_page_slices_length_and_order() -> None:
    assert len(PAGE_SLICES) == 16
    assert PAGE_SLICES[0][0] == "01_front_page"
    assert PAGE_SLICES[-1][0] == "16_classifieds"


def test_slice_stems_matches_first_last() -> None:
    stems = slice_stems()
    assert len(stems) == 16
    assert stems[0] == "01_front_page"
    assert stems[-1] == "16_classifieds"


def test_manuscript_filenames_suffix() -> None:
    names = manuscript_filenames()
    assert all(n.endswith(".md") for n in names)
    assert names[0] == "01_front_page.md"


def test_validate_inventory_complete(tmp_path: Path) -> None:
    for n in manuscript_filenames():
        (tmp_path / n).write_text("# x\n", encoding="utf-8")
    assert validate_inventory(tmp_path) == []


def test_validate_inventory_missing(tmp_path: Path) -> None:
    missing = validate_inventory(tmp_path)
    assert len(missing) == 16


def test_validate_inventory_partial(tmp_path: Path) -> None:
    (tmp_path / "01_front_page.md").write_text("# x\n", encoding="utf-8")
    m = validate_inventory(tmp_path)
    assert "01_front_page.md" not in m
    assert len(m) == 15


@pytest.fixture
def manuscript_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "manuscript"


def test_repo_manuscript_inventory_complete(manuscript_dir: Path) -> None:
    assert manuscript_dir.is_dir()
    assert validate_inventory(manuscript_dir) == []
