"""Robustness tests — the silent-failure modes surfaced by cross-vendor audit.

These bind the fixes for: over-tall boxes (must be detected, not shrunk),
unescaped author markup (must not corrupt or crash), and the strict-loader
contract for figures and pull blocks.
"""

from __future__ import annotations

import pytest

from newspaper.components import _esc, ad_flowables
from newspaper.config import NewspaperConfig
from newspaper.content import Ad, Block, Box, Edition, Figure, Page, Story, _parse_block, _parse_figure
from newspaper.engine import render_edition
from newspaper.typography import build_stylesheet, register_fonts


# --- C1: over-tall boxes are detected, not silently shrunk -------------------


def test_over_tall_box_is_detected_as_overset(tmp_path) -> None:
    tall = Box(kind="generic", title="Huge", items=[f"line {i}" for i in range(400)])
    page = Page(number=1, template="standard", columns=2, main_items=[tall])
    edition = Edition(nameplate="T", city="C", state="S", date="D", pages=[page])
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=tmp_path / "o.pdf")
    assert not result.all_pages_fit
    assert result.oversets.get(1, 0) > 0


# --- H1: author markup is escaped, not corrupted ----------------------------


def test_esc_escapes_bare_ampersand() -> None:
    assert _esc("AT&T merger") == "AT&amp;T merger"


def test_esc_escapes_angle_brackets() -> None:
    assert _esc("5 < 10 and x > y") == "5 &lt; 10 and x &gt; y"


def test_esc_preserves_allowed_markup() -> None:
    assert _esc("keep <b>bold</b> and <i>italic</i><br/>") == "keep <b>bold</b> and <i>italic</i><br/>"


def test_esc_does_not_double_escape_entities() -> None:
    assert _esc("Local &amp; Region") == "Local &amp; Region"


def test_esc_preserves_font_tag() -> None:
    s = 'caption <font name="NP-Body">/ credit</font>'
    assert _esc(s) == s


def test_render_with_ampersand_content_does_not_crash(tmp_path) -> None:
    story = Story(headline="AT&T & R&D < gains", body=[Block("p", "Revenue rose 5% as A&B and X<Y resolved.")])
    page = Page(number=1, template="standard", columns=2, main_items=[story])
    edition = Edition(nameplate="T&T", city="C", state="S", date="D", pages=[page])
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=tmp_path / "amp.pdf")
    assert result.page_count == 1


# --- M1/M2/M3: strict-loader contract ---------------------------------------


def test_figure_requires_path() -> None:
    with pytest.raises(ValueError):
        Figure(path="")
    with pytest.raises(ValueError) as exc:
        _parse_figure({"caption": "no path"})
    assert "path" in str(exc.value)


def test_figure_rejects_nonpositive_height() -> None:
    with pytest.raises(ValueError):
        Figure(path="x.png", height=0)
    with pytest.raises(ValueError):
        _parse_figure({"path": "x.png", "height": "tall"})


def test_pull_block_as_list_raises_named_error() -> None:
    with pytest.raises(ValueError):
        _parse_block({"pull": ["not", "a", "mapping"]})


# --- A1: ad_flowables branch coverage ---------------------------------------


def test_ad_flowables_minimal(tmp_path) -> None:
    """ad_flowables with no graphic, no tagline, no contact covers the skipped
    branches at lines 420->435 (no tagline) and 440->456 (no contact)."""
    fonts = register_fonts()
    styles = build_stylesheet(fonts)
    ad = Ad(sponsor="Minimal Ad", tagline="", contact="", border="box")
    items = ad_flowables(ad, styles, fonts, width=200.0, project_root=tmp_path)
    assert len(items) >= 1


def test_ad_flowables_with_missing_graphic(tmp_path) -> None:
    """An ad referencing a non-existent graphic path skips the image silently
    (covers the 393->406 branch where _resolve returns None)."""
    fonts = register_fonts()
    styles = build_stylesheet(fonts)
    ad = Ad(
        sponsor="Harbor Inn",
        tagline="Rest easy by the sea",
        graphic="missing/logo.png",
        contact="555-0001",
        border="box",
    )
    items = ad_flowables(ad, styles, fonts, width=200.0, project_root=tmp_path)
    assert len(items) >= 1


def test_ad_flowables_with_real_graphic(tmp_path) -> None:
    """An ad with a real image that can be loaded exercises the image-placed path."""
    from PIL import Image as PILImage

    # Create a tiny valid PNG for the ad graphic.
    img = PILImage.new("RGB", (80, 40), color=(200, 180, 140))
    graphic_path = tmp_path / "logo.png"
    img.save(str(graphic_path))

    fonts = register_fonts()
    styles = build_stylesheet(fonts)
    ad = Ad(
        sponsor="Sunny Bakery",
        tagline="Fresh every morning",
        graphic=str(graphic_path),
        graphic_height=40.0,
        contact="Main St.",
        border="double",
    )
    items = ad_flowables(ad, styles, fonts, width=200.0, project_root=tmp_path)
    assert len(items) >= 1


def test_ad_flowables_with_corrupt_graphic(tmp_path) -> None:
    """An ad graphic that exists but fails to load is silently skipped (403-404).

    The ad renders without the image rather than crashing.
    """
    corrupt_path = tmp_path / "corrupt.png"
    corrupt_path.write_bytes(b"NOT A VALID IMAGE FILE AT ALL")

    fonts = register_fonts()
    styles = build_stylesheet(fonts)
    ad = Ad(
        sponsor="Harbor Inn",
        tagline="Cozy rooms",
        graphic=str(corrupt_path),  # exists but unreadable as image
        graphic_height=50.0,
        contact="555-0099",
        border="box",
    )
    # Must not raise — falls back gracefully.
    items = ad_flowables(ad, styles, fonts, width=200.0, project_root=tmp_path)
    assert len(items) >= 1
