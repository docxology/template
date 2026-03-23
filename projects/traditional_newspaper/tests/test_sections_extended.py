"""Extended tests for ``newspaper.sections``."""

from pathlib import Path

from newspaper.sections import (
    MANUSCRIPT_OPTIONAL_FILENAMES,
    OPTIONAL_MANUSCRIPT_STEM_TO_TITLE,
    SLICE_BY_STEM,
    all_tracked_manuscript_basenames,
    get_slice,
    manuscript_stems_ordered,
    section_banner_targets,
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
    assert "S02_typography_and_measure.md" in MANUSCRIPT_OPTIONAL_FILENAMES
    assert "S03_validation_and_outputs.md" in MANUSCRIPT_OPTIONAL_FILENAMES
    assert "98_newspaper_and_pipeline_terms.md" in MANUSCRIPT_OPTIONAL_FILENAMES


def test_all_tracked_includes_core_and_optional() -> None:
    names = all_tracked_manuscript_basenames()
    assert names[0] == "01_front_page.md"
    assert "S01_layout_and_pipeline.md" in names
    assert len(names) == 16 + len(MANUSCRIPT_OPTIONAL_FILENAMES)


def test_optional_stem_title_map_covers_optionals() -> None:
    for name in MANUSCRIPT_OPTIONAL_FILENAMES:
        stem = Path(name).stem
        assert stem in OPTIONAL_MANUSCRIPT_STEM_TO_TITLE


def test_section_banner_targets_order_core_then_optional() -> None:
    targets = section_banner_targets()
    assert targets[0] == ("02_national", "National")
    assert targets[14] == ("16_classifieds", "Classifieds")
    assert targets[15][0] == "S01_layout_and_pipeline"
