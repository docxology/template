"""Newspaper layout helpers for the traditional_newspaper exemplar project."""

from newspaper.content import FIXTURE_SENTENCES, fixture_copy, fixture_paragraph
from newspaper.layout_figure import render_layout_schematic_png
from newspaper.layout_spec import LAYOUT, NewspaperLayout, column_count_valid
from newspaper.masthead import render_masthead_png
from newspaper.sections import (
    MANUSCRIPT_OPTIONAL_FILENAMES,
    PAGE_SLICES,
    SLICE_BY_STEM,
    all_tracked_manuscript_basenames,
    get_slice,
    manuscript_filenames,
    manuscript_stems_ordered,
    slice_count,
    slice_stems,
    validate_inventory,
)
from newspaper.snippets import (
    byline,
    classified_line,
    dateline,
    headline,
    multicol_begin,
    multicol_end,
    pull_quote,
    rule_line,
    section_label,
)

__all__ = [
    "FIXTURE_SENTENCES",
    "LAYOUT",
    "MANUSCRIPT_OPTIONAL_FILENAMES",
    "NewspaperLayout",
    "PAGE_SLICES",
    "SLICE_BY_STEM",
    "all_tracked_manuscript_basenames",
    "byline",
    "classified_line",
    "column_count_valid",
    "dateline",
    "fixture_copy",
    "fixture_paragraph",
    "get_slice",
    "headline",
    "manuscript_filenames",
    "manuscript_stems_ordered",
    "multicol_begin",
    "multicol_end",
    "pull_quote",
    "render_layout_schematic_png",
    "render_masthead_png",
    "rule_line",
    "section_label",
    "slice_count",
    "slice_stems",
    "validate_inventory",
]
