"""Extended tests for ``newspaper.sections``."""

from newspaper.sections import (
    MANUSCRIPT_OPTIONAL_FILENAMES,
    SLICE_BY_STEM,
    all_tracked_manuscript_basenames,
    get_slice,
    manuscript_stems_ordered,
    slice_count,
    slice_stems,
)


def test_slice_count() -> None:
    assert slice_count() == 16


def test_get_slice_known() -> None:
    g = get_slice("01_front_page")
    assert g is not None
    assert g[0] == "01_front_page"
    assert g[1] == "Front Page"


def test_get_slice_unknown() -> None:
    assert get_slice("99_nope") is None


def test_manuscript_stems_ordered_matches_slice_stems() -> None:
    assert manuscript_stems_ordered() == slice_stems()


def test_slice_by_stem_covers_all_slices() -> None:
    assert len(SLICE_BY_STEM) == 16
    for stem in slice_stems():
        assert stem in SLICE_BY_STEM


def test_optional_filenames_listed() -> None:
    assert "S01_layout_and_pipeline.md" in MANUSCRIPT_OPTIONAL_FILENAMES
    assert "98_newspaper_and_pipeline_terms.md" in MANUSCRIPT_OPTIONAL_FILENAMES


def test_all_tracked_includes_core_and_optional() -> None:
    names = all_tracked_manuscript_basenames()
    assert names[0] == "01_front_page.md"
    assert "S01_layout_and_pipeline.md" in names
    assert len(names) == 16 + len(MANUSCRIPT_OPTIONAL_FILENAMES)
