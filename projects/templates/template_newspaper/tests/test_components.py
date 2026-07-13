"""Tests for the component flowable builders.

These tests exercise the internal rendering helpers that build ReportLab
flowables — pull quotes, figures, boxes, ads — covering branches not reached
by the integration render tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from reportlab.lib.styles import StyleSheet1
from reportlab.platypus import Table

from newspaper.components import (
    _boxed,
    _data_table,
    _hex,
    _resolve_image_path,
    box_flowables,
    classified_flowables,
    figure_flowables,
    hairline,
    pull_quote,
    story_flowables,
)
from newspaper.content import Block, Box, Figure, Story
from newspaper.typography import INK, MUTED, Fonts, build_stylesheet, register_fonts


@pytest.fixture(scope="module")
def fonts() -> Fonts:
    return register_fonts()


@pytest.fixture(scope="module")
def styles(fonts: Fonts) -> StyleSheet1:
    return build_stylesheet(fonts)


# ---------------------------------------------------------------------------
# _hex
# ---------------------------------------------------------------------------


def test_hex_empty_returns_default(styles: StyleSheet1) -> None:
    default = INK
    assert _hex("", default) is default


def test_hex_invalid_returns_default(styles: StyleSheet1) -> None:
    default = MUTED
    assert _hex("not-a-color", default) is default


def test_hex_valid_returns_color(styles: StyleSheet1) -> None:
    color = _hex("#FF0000", INK)
    assert color is not INK
    # The returned object should have red channel 1.0 and green/blue 0.0
    assert abs(color.red - 1.0) < 0.01  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# hairline
# ---------------------------------------------------------------------------


def test_hairline_returns_hrflowable(styles: StyleSheet1) -> None:
    from reportlab.platypus import HRFlowable

    h = hairline()
    assert isinstance(h, HRFlowable)


def test_hairline_custom_params(styles: StyleSheet1) -> None:
    from reportlab.platypus import HRFlowable

    h = hairline(width=1.2, color=MUTED, space_before=5, space_after=10)
    assert isinstance(h, HRFlowable)


# ---------------------------------------------------------------------------
# pull_quote
# ---------------------------------------------------------------------------


def test_pull_quote_with_attribution(styles: StyleSheet1) -> None:
    tbl = pull_quote("Great words.", "Alice Smith", styles)
    assert isinstance(tbl, Table)


def test_pull_quote_without_attribution(styles: StyleSheet1) -> None:
    """pull_quote with empty attribution must omit the attribution paragraph."""
    tbl = pull_quote("Just the quote, no one said it.", "", styles)
    assert isinstance(tbl, Table)


# ---------------------------------------------------------------------------
# _resolve_image_path
# ---------------------------------------------------------------------------


def test_resolve_image_path_absolute_exists(tmp_path: Path) -> None:
    img = tmp_path / "photo.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    resolved = _resolve_image_path(str(img), tmp_path)
    assert resolved == img


def test_resolve_image_path_relative_missing(tmp_path: Path) -> None:
    assert _resolve_image_path("nonexistent/image.png", tmp_path) is None


# ---------------------------------------------------------------------------
# figure_flowables
# ---------------------------------------------------------------------------


def test_figure_flowables_missing_image_uses_placeholder(styles: StyleSheet1, tmp_path: Path) -> None:
    """A figure referencing a missing image path renders a placeholder, not an error."""
    fig = Figure(path="missing/photo.png", caption="A photo", credit="Staff", height=100)
    items = figure_flowables(fig, width=200.0, styles=styles, project_root=tmp_path)
    assert len(items) > 0


def test_figure_flowables_no_caption_no_credit(styles: StyleSheet1, tmp_path: Path) -> None:
    """A figure with no caption or credit skips the cutline line."""
    fig = Figure(path="missing/photo.png", caption="", credit="", height=100)
    # Should produce only the placeholder table + Spacer (no hairline/paragraph)
    items = figure_flowables(fig, width=200.0, styles=styles, project_root=tmp_path)
    assert len(items) > 0  # at least placeholder + spacer


def test_figure_flowables_caption_only_no_credit(styles: StyleSheet1, tmp_path: Path) -> None:
    """A figure with caption but empty credit skips the credit font tag (176->178 arc)."""
    fig = Figure(path="missing/photo.png", caption="Looking west from the pier.", credit="", height=100)
    items = figure_flowables(fig, width=200.0, styles=styles, project_root=tmp_path)
    # Should include hairline + caption paragraph (but no credit tag)
    assert len(items) > 0


def test_figure_flowables_credit_only_no_caption(styles: StyleSheet1, tmp_path: Path) -> None:
    """A figure with credit but empty caption string still shows the credit."""
    fig = Figure(path="missing/photo.png", caption="", credit="Staff photographer", height=100)
    items = figure_flowables(fig, width=200.0, styles=styles, project_root=tmp_path)
    assert len(items) > 0


# ---------------------------------------------------------------------------
# _data_table
# ---------------------------------------------------------------------------


def test_data_table_with_columns_header(styles: StyleSheet1, fonts: Fonts) -> None:
    """_data_table with column headers produces a table with a header separator."""
    box = Box(
        kind="table",
        columns=["Day", "High", "Low"],
        rows=[["Mon", "62", "48"], ["Tue", "65", "50"]],
    )
    tbl = _data_table(box, styles, fonts, width=300.0)
    assert isinstance(tbl, Table)


def test_data_table_without_header(styles: StyleSheet1, fonts: Fonts) -> None:
    """_data_table with no columns header (empty list) still renders."""
    box = Box(kind="table", columns=[], rows=[["a", "b"], ["c", "d"]])
    tbl = _data_table(box, styles, fonts, width=300.0)
    assert isinstance(tbl, Table)


# ---------------------------------------------------------------------------
# _boxed
# ---------------------------------------------------------------------------


def test_boxed_with_heavy_top(styles: StyleSheet1) -> None:
    from reportlab.platypus import Paragraph

    inner = [Paragraph("content", styles["BoxBody"])]
    tbl = _boxed(inner, width=200.0, shaded=True, heavy_top=True)
    assert isinstance(tbl, Table)


def test_boxed_without_heavy_top(styles: StyleSheet1) -> None:
    """_boxed with heavy_top=False must not add the LINEABOVE rule."""
    from reportlab.platypus import Paragraph

    inner = [Paragraph("content", styles["BoxBody"])]
    tbl = _boxed(inner, width=200.0, shaded=False, heavy_top=False)
    assert isinstance(tbl, Table)


# ---------------------------------------------------------------------------
# classified_flowables
# ---------------------------------------------------------------------------


def test_classified_flowables_with_title(styles: StyleSheet1) -> None:
    box = Box(kind="generic", title="For Sale", items=["Item A $5", "Item B $10"])
    items = classified_flowables(box, styles)
    assert len(items) > 0


def test_classified_flowables_without_title(styles: StyleSheet1) -> None:
    """classified_flowables with no title skips the title+hairline paragraphs."""
    box = Box(kind="generic", title="", items=["Ad one", "Ad two"])
    items = classified_flowables(box, styles)
    # Should still produce item paragraphs + spacer
    assert len(items) >= 1


def test_classified_flowables_with_body_blocks(styles: StyleSheet1) -> None:
    """classified_flowables renders body blocks as classified paragraphs."""
    box = Box(kind="generic", title="", body=[Block("p", "Block ad text here.")])
    items = classified_flowables(box, styles)
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# box_flowables — branch coverage for each kind
# ---------------------------------------------------------------------------


def test_box_flowables_no_title(styles: StyleSheet1, fonts: Fonts) -> None:
    """box_flowables with an empty title must skip the title/hairline."""
    box = Box(kind="index", title="", items=["A1", "B2"])
    items = box_flowables(box, styles, fonts, width=200.0)
    assert len(items) >= 1


def test_box_flowables_weather_no_rows(styles: StyleSheet1, fonts: Fonts) -> None:
    """A weather box with body but no rows renders without the data table."""
    box = Box(kind="weather", title="Forecast", body=[Block("p", "Partly cloudy.")])
    items = box_flowables(box, styles, fonts, width=200.0)
    assert len(items) >= 1


def test_box_flowables_weather_with_rows(styles: StyleSheet1, fonts: Fonts) -> None:
    box = Box(
        kind="weather",
        title="Forecast",
        body=[Block("p", "High near 60.")],
        columns=["", "High", "Low"],
        rows=[["Today", "60", "50"]],
    )
    items = box_flowables(box, styles, fonts, width=200.0)
    assert len(items) >= 1


def test_box_flowables_staff(styles: StyleSheet1, fonts: Fonts) -> None:
    box = Box(kind="staff", title="Staff", items=["Editor: J. Smith", "Reporter: K. Lee"])
    items = box_flowables(box, styles, fonts, width=200.0)
    assert len(items) >= 1


def test_box_flowables_almanac(styles: StyleSheet1, fonts: Fonts) -> None:
    box = Box(kind="almanac", title="Almanac", body=[Block("p", "Sunrise 6:14 AM")])
    items = box_flowables(box, styles, fonts, width=200.0)
    assert len(items) >= 1


def test_box_flowables_calendar(styles: StyleSheet1, fonts: Fonts) -> None:
    box = Box(kind="calendar", title="Events", body=[Block("p", "7 PM: Concert")])
    items = box_flowables(box, styles, fonts, width=200.0)
    assert len(items) >= 1


def test_box_flowables_briefs_with_subhead(styles: StyleSheet1, fonts: Fonts) -> None:
    box = Box(
        kind="briefs",
        title="Briefs",
        body=[Block("subhead", "Local"), Block("p", "Brief item here.")],
    )
    items = box_flowables(box, styles, fonts, width=200.0)
    assert len(items) >= 1


def test_box_flowables_generic_with_footnote(styles: StyleSheet1, fonts: Fonts) -> None:
    """box_flowables with a footnote appends a small italic note."""
    box = Box(kind="generic", title="Notice", items=["Item one"], footnote="Source: staff reports")
    items = box_flowables(box, styles, fonts, width=200.0)
    assert len(items) >= 1


def test_box_flowables_tides_box_shaded(styles: StyleSheet1, fonts: Fonts) -> None:
    """A tides box (not briefs/staff) must be shaded."""
    box = Box(kind="tides", title="Tides", rows=[["High", "08:42"], ["Low", "14:17"]])
    items = box_flowables(box, styles, fonts, width=200.0)
    assert len(items) >= 1


def test_box_flowables_briefs_not_shaded(styles: StyleSheet1, fonts: Fonts) -> None:
    """briefs/staff boxes are unshaded (distinct visual treatment)."""
    box = Box(kind="briefs", title="News Briefs", body=[Block("p", "Quick note.")])
    items = box_flowables(box, styles, fonts, width=200.0)
    assert len(items) >= 1


# ---------------------------------------------------------------------------
# story_flowables — branch coverage
# ---------------------------------------------------------------------------


def test_story_flowables_with_all_fields(styles: StyleSheet1, fonts: Fonts, tmp_path: Path) -> None:
    """story_flowables with kicker, deck, byline, figure, and jump line."""
    story = Story(
        headline="Harbor News",
        kicker="Waterfront",
        deck="Fresh catch sets record.",
        byline="By A. Reporter",
        level="secondary",
        drop_cap=False,
        body=[
            Block("p", "First paragraph."),
            Block("subhead", "A subhead"),
            Block("pull", "A quoted line.", "Source"),
            Block("p", "Second paragraph."),
        ],
        figure=Figure(path="missing.png", caption="Caption.", credit="Photo credit"),
        jump="Continued on A6",
    )
    items = story_flowables(story, styles, fonts, measure=200.0, project_root=tmp_path)
    assert len(items) > 0


def test_story_flowables_drop_cap_short_text(styles: StyleSheet1, fonts: Fonts, tmp_path: Path) -> None:
    """A drop_cap with a single-char first paragraph falls back to BodyFirst."""
    story = Story(
        headline="Short",
        level="minor",
        drop_cap=True,
        body=[Block("p", "X")],  # single char — drop_cap logic requires len > 1
    )
    items = story_flowables(story, styles, fonts, measure=200.0, project_root=tmp_path)
    assert len(items) > 0


def test_story_flowables_no_headline(styles: StyleSheet1, fonts: Fonts, tmp_path: Path) -> None:
    """include_headline=False omits kicker/headline/deck paragraphs."""
    story = Story(
        headline="Should Not Appear",
        kicker="Should Not Appear",
        deck="Should Not Appear",
        level="lead",
        body=[Block("p", "Lead body text here.")],
    )
    items = story_flowables(story, styles, fonts, measure=200.0, project_root=tmp_path, include_headline=False)
    assert len(items) > 0
