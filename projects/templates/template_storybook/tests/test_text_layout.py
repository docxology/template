from __future__ import annotations

import pytest
from PIL import Image, ImageDraw

from storybook.models import PageSpec
from storybook.text_layout import (
    contrast_ratio,
    load_font,
    pixel_wrapped_lines,
    text_height,
    text_width,
    validate_text_contrast,
    wrapped_lines,
)


def test_contrast_ratio_known_extremes() -> None:
    assert contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0)
    assert contrast_ratio((128, 128, 128), (128, 128, 128)) == pytest.approx(1.0)


def test_validate_text_contrast_meets_accessibility_floor() -> None:
    assert validate_text_contrast() >= 4.5


def test_wrapped_lines_respects_word_boundaries() -> None:
    lines = wrapped_lines("the shape between pages", 12)
    assert lines
    assert all(len(line) <= 12 for line in lines)
    assert " ".join(lines).split() == ["the", "shape", "between", "pages"]


def test_pixel_wrapped_lines_bounds_width() -> None:
    image = Image.new("RGB", (200, 80), "white")
    draw = ImageDraw.Draw(image)
    font = load_font(12)
    lines = pixel_wrapped_lines(draw, "a fairly long storybook caption line", font, 160)
    assert lines
    for line in lines:
        assert text_width(draw, line, font) <= 160


def test_load_font_measures_positive_text() -> None:
    image = Image.new("RGB", (100, 40), "white")
    draw = ImageDraw.Draw(image)
    font = load_font(14)
    assert text_width(draw, "storybook", font) > 0
    assert text_height(draw, "storybook", font) > 0


def _page() -> PageSpec:
    return PageSpec(
        number=1,
        slug="cover",
        title="Cover",
        scene="scene",
        text="cover text",
        overlay_box=False,
        palette=("#111111", "#eeeeee", "#222222", "#dddddd"),
    )


def test_text_layout_imports_surface_is_complete() -> None:
    # The module's fixed palette constants back the render path; pin them so an
    # accidental palette change fails loudly instead of shifting published art.
    from storybook import text_layout

    assert text_layout.PANEL_TEXT_RGB == (24, 28, 42)
    assert text_layout.PANEL_BACKGROUND_RGB == (255, 250, 240)
    assert _page().slug == "cover"
