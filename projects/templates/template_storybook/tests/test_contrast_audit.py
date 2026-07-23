"""Raster contrast audit for direct text overlays on storybook pages.

Renders real storybook pages (no mocks), opens the PNGs with PIL, samples the
text-overlay regions, and checks that the rendered text achieves sufficient
contrast against its local background per the WCAG 2.1 contrast-ratio formula.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from storybook import render_story_number


# ---------------------------------------------------------------------------
# WCAG 2.1 relative-luminance and contrast helpers (real pixel math, no mocks).
# ---------------------------------------------------------------------------


def _srgb_to_linear(value: float) -> float:
    """Convert a single sRGB channel value [0, 255] to linear light."""
    v = value / 255.0
    if v <= 0.03928:
        return v / 12.92
    return ((v + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG 2.1 relative luminance for an RGB triple."""
    r, g, b = (_srgb_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    """WCAG 2.1 contrast ratio between two RGB colors.

    Always >= 1.0.  WCAG AA text requires >= 4.5.
    """
    l_fg = relative_luminance(fg)
    l_bg = relative_luminance(bg)
    lighter, darker = (l_fg, l_bg) if l_fg >= l_bg else (l_bg, l_fg)
    return (lighter + 0.05) / (darker + 0.05)


def _band_pixels(band: Image.Image) -> list[tuple[int, int, int]]:
    """Extract RGB pixel tuples from a cropped band without deprecated getdata()."""
    raw = band.tobytes()
    return [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]


def _median_rgb(pixels: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    """Return the per-channel median RGB of a pixel list."""
    if not pixels:
        raise ValueError("Cannot take median of empty pixel list")
    r = sorted(c[0] for c in pixels)
    g = sorted(c[1] for c in pixels)
    b = sorted(c[2] for c in pixels)
    mid = len(r) // 2
    return (r[mid], g[mid], b[mid])


# ---------------------------------------------------------------------------
# Helpers for overlay-box pages.
# ---------------------------------------------------------------------------

# Page 2 ("square_house") has overlay_box=True and caption_position="bottom".
# draw_page_text() computes the text box at the bottom of the page:
#   margin = 86, line gap 12, title_height = 68*lines, body_height = 48*lines,
#   box_height = title+body+72, top = height - box_height - 88.
# The rounded-rectangle box spans (margin-28, top-30) .. (width-margin+28, top+box_height)
# and is filled with (255, 250, 240, 224) — a light cream.  Text ink is (24, 28, 42, 255).
_OVERLAY_TEXT_RGB = (24, 28, 42)
_OVERLAY_BOX_RGB_APPROX = (255, 250, 240)  # composited over illustration; close enough

# Page 3 ("pointed_house") has overlay_box=False.
# Text is drawn light (255, 250, 240, 255) with a dark shadow (12, 14, 24, 210) offset +4.
_NOVERLAY_TEXT_RGB = (255, 250, 240)
_NOVERLAY_SHADOW_RGB = (12, 14, 24)


def test_overlay_box_text_meets_wcag_aa(isolated_project: Path) -> None:
    """An overlay-box page (square_house) must have dark text on a light box.

    The cream box provides a near-uniform light background; the dark ink
    (24, 28, 42) should achieve WCAG AA (>= 4.5:1) or better against it.
    """
    page_path = render_story_number(isolated_project, 2)
    image = Image.open(page_path).convert("RGB")
    width, height = image.size
    assert (width, height) == (1275, 1650)

    # Sample the bottom caption band where the overlay box lives.
    # The box bottom is near height-88; sample a wide band just above it.
    band = image.crop((58, height - 520, width - 58, height - 96))
    band_pixels = _band_pixels(band)

    # Dark pixels = text ink; light pixels = box background.
    text_pixels = [px for px in band_pixels if sum(px) < 240]
    bg_pixels = [px for px in band_pixels if sum(px) > 720]

    assert text_pixels, "Expected dark text-ink pixels in the overlay band"
    assert bg_pixels, "Expected light box-background pixels in the overlay band"

    text_color = _median_rgb(text_pixels)
    bg_color = _median_rgb(bg_pixels)

    ratio = contrast_ratio(text_color, bg_color)
    assert ratio >= 4.5, (
        f"Overlay-box text contrast {ratio:.2f}:1 is below WCAG AA (4.5). text={text_color} bg={bg_color}"
    )


def test_non_overlay_text_has_dark_shadow_for_contrast(isolated_project: Path) -> None:
    """A non-overlay page (pointed_house) draws light text with a dark shadow.

    The shadow (12, 14, 24) offset behind the light text (255, 250, 240)
    must provide sufficient contrast for legibility. We verify two things:
    1. Dark shadow pixels exist in the text region (the shadow is actually drawn).
    2. The contrast between light text and dark shadow >= 4.5:1.
    """
    page_path = render_story_number(isolated_project, 3)
    image = Image.open(page_path).convert("RGB")
    width, height = image.size

    # Caption is at the bottom (default caption_position). Sample the band.
    band = image.crop((58, height - 520, width - 58, height - 96))
    band_pixels = _band_pixels(band)

    # Light pixels = text; very dark pixels = shadow.
    text_pixels = [px for px in band_pixels if sum(px) > 735]
    shadow_pixels = [px for px in band_pixels if sum(px) < 120]

    assert text_pixels, "Expected light text pixels in non-overlay caption band"
    assert shadow_pixels, "Expected dark shadow pixels behind non-overlay text"

    text_color = _median_rgb(text_pixels)
    shadow_color = _median_rgb(shadow_pixels)

    ratio = contrast_ratio(text_color, shadow_color)
    assert ratio >= 4.5, (
        f"Non-overlay text/shadow contrast {ratio:.2f}:1 is below WCAG AA (4.5). "
        f"text={text_color} shadow={shadow_color}"
    )


def test_overlay_text_ink_matches_expected_palette(isolated_project: Path) -> None:
    """The overlay text ink should be close to the hardcoded dark navy (24, 28, 42).

    This guards against accidental palette drift that would erode contrast.
    """
    page_path = render_story_number(isolated_project, 2)
    image = Image.open(page_path).convert("RGB")
    width, height = image.size

    band = image.crop((58, height - 520, width - 58, height - 96))
    text_pixels = [px for px in _band_pixels(band) if sum(px) < 240]
    assert text_pixels, "Expected dark text pixels"

    text_color = _median_rgb(text_pixels)
    # Allow slack for anti-aliasing; each channel within 40 of the ink value.
    for actual, expected in zip(text_color, _OVERLAY_TEXT_RGB):
        assert abs(actual - expected) <= 40, (
            f"Text ink channel drifted: got {text_color}, expected near {_OVERLAY_TEXT_RGB}"
        )


def test_all_overlay_pages_pass_contrast_audit(isolated_project: Path) -> None:
    """Every overlay_box page in the default story must meet WCAG AA contrast.

    This is the comprehensive gate: render each overlay-box page and check that
    dark text on the light box achieves >= 4.5:1 in the caption band.
    """
    # Pages with overlay_box=True that use the standard draw_page_text() layout.
    # Page 1 (publication_information) is excluded: it uses draw_publication_text(),
    # a full-page panel layout, not the bottom/top caption overlay.
    overlay_page_numbers = [2, 4, 6, 7, 9, 11, 12]

    ratios: list[tuple[int, float]] = []
    for number in overlay_page_numbers:
        page_path = render_story_number(isolated_project, number)
        image = Image.open(page_path).convert("RGB")
        width, height = image.size

        # For caption_position="bottom" (default) the box sits near the bottom;
        # for "top" (mega_symbol, page 12) it sits near the top.
        if number == 12:
            band = image.crop((58, 80, width - 58, 560))
        else:
            band = image.crop((58, height - 520, width - 58, height - 96))

        band_pixels = _band_pixels(band)
        text_pixels = [px for px in band_pixels if sum(px) < 240]
        bg_pixels = [px for px in band_pixels if sum(px) > 720]

        assert text_pixels, f"Page {number}: no dark text pixels found in caption band"
        assert bg_pixels, f"Page {number}: no light box pixels found in caption band"

        text_color = _median_rgb(text_pixels)
        bg_color = _median_rgb(bg_pixels)
        ratio = contrast_ratio(text_color, bg_color)
        ratios.append((number, ratio))

        assert ratio >= 4.5, (
            f"Page {number} overlay contrast {ratio:.2f}:1 below WCAG AA (4.5). text={text_color} bg={bg_color}"
        )

    # Sanity: at least one page should exceed AA Large (3.0) comfortably.
    assert all(r >= 4.5 for _, r in ratios)
    # Report the minimum for visibility on failure.
    min_page, min_ratio = min(ratios, key=lambda item: item[1])
    assert min_ratio >= 4.5, f"Lowest contrast was page {min_page} at {min_ratio:.2f}:1"
