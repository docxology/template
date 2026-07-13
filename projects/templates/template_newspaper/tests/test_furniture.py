"""Tests for the canvas-drawn page furniture.

These tests exercise furniture.py paths not reached by the integration render
tests: draw_lead_headline without a kicker, without a deck, and the nameplate
font-size scaling triggered by a long paper name.
"""

from __future__ import annotations


from newspaper.config import NewspaperConfig
from newspaper.content import Block, Edition, Page, Story
from newspaper.engine import render_edition
from newspaper.typography import Fonts


def _base14() -> Fonts:
    """Base-14 Fonts record (always available, no macOS system fonts needed)."""
    return Fonts(
        display="Times-Roman",
        display_bold="Times-Bold",
        body="Times-Roman",
        body_bold="Times-Bold",
        body_italic="Times-Italic",
        body_bolditalic="Times-BoldItalic",
        sans="Helvetica",
        sans_bold="Helvetica-Bold",
    )


# ---------------------------------------------------------------------------
# draw_lead_headline — kicker/deck branch coverage
# ---------------------------------------------------------------------------


def test_front_page_lead_without_kicker_and_deck(tmp_path) -> None:
    """A lead story with no kicker and no deck must still render without error.

    This covers the 216->220 (kicker branch is False) and 226->234 (deck branch
    is False) arcs in furniture.draw_lead_headline.
    """
    lead = Story(
        headline="Harbor Opens After Storm",
        kicker="",  # explicitly empty — kicker branch should be skipped
        deck="",  # explicitly empty — deck branch should be skipped
        level="lead",
        body=[Block("p", "The harbor reopened Wednesday after three days of closure.")],
    )
    page = Page(number=1, template="front", columns=3, lead=lead, main_items=[])
    edition = Edition(nameplate="T", city="C", state="S", date="D", pages=[page])
    out = tmp_path / "no_kicker_deck.pdf"
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=out, fonts=_base14())
    assert result.page_count == 1
    assert out.exists()


def test_front_page_lead_with_kicker_only(tmp_path) -> None:
    """A lead story with kicker but no deck covers the kicker-True/deck-False arcs."""
    lead = Story(
        headline="Crabbers Report Bumper Season",
        kicker="Fishing",
        deck="",  # no deck — 226->234 branch is False
        level="lead",
        body=[Block("p", "Local crabbers report a record haul this season.")],
    )
    page = Page(number=1, template="front", columns=3, lead=lead, main_items=[])
    edition = Edition(nameplate="T", city="C", state="S", date="D", pages=[page])
    out = tmp_path / "kicker_no_deck.pdf"
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=out, fonts=_base14())
    assert result.page_count == 1
    assert out.exists()


def test_front_page_lead_with_deck_only(tmp_path) -> None:
    """A lead story with deck but no kicker covers the kicker-False/deck-True arcs."""
    lead = Story(
        headline="City Council Approves Budget",
        kicker="",  # no kicker — 216->220 branch is False
        deck="New spending plan passes 4-1 after marathon session.",
        level="lead",
        body=[Block("p", "The council voted late Tuesday to approve the 2025 budget.")],
    )
    page = Page(number=1, template="front", columns=3, lead=lead, main_items=[])
    edition = Edition(nameplate="T", city="C", state="S", date="D", pages=[page])
    out = tmp_path / "no_kicker_with_deck.pdf"
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=out, fonts=_base14())
    assert result.page_count == 1
    assert out.exists()


# ---------------------------------------------------------------------------
# draw_nameplate — font-size scaling for long nameplate names
# ---------------------------------------------------------------------------


def test_nameplate_long_name_scales_font(tmp_path) -> None:
    """A very long nameplate name triggers the font-size scaling path in
    draw_nameplate (line 85: measured > name_zone → rescale).

    We use a string long enough that its width at 122pt exceeds the zone
    between the ears, so the engine must scale the font down.
    """
    long_name = "The Very Long Newspaper Name Of Crescent City"
    lead = Story(
        headline="Test Story",
        kicker="",
        deck="",
        level="lead",
        body=[Block("p", "Body text for the lead.")],
    )
    page = Page(number=1, template="front", columns=3, lead=lead, main_items=[])
    edition = Edition(
        nameplate=long_name,
        city="Crescent City",
        state="CA",
        date="June 25, 2026",
        established="1873",
        pages=[page],
    )
    out = tmp_path / "long_nameplate.pdf"
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=out, fonts=_base14())
    assert result.page_count == 1
    assert out.exists()


# ---------------------------------------------------------------------------
# draw_section_band — spot color and no-department variants
# ---------------------------------------------------------------------------


def test_inside_page_with_spot_color(tmp_path) -> None:
    """Section band with spot_color=True must render without error."""
    from dataclasses import replace

    from newspaper.config import NewspaperConfig

    page = Page(
        number=2,
        template="standard",
        department="Local News",
        columns=4,
        main_items=[
            Story(
                headline="Community Event This Weekend",
                level="secondary",
                body=[Block("p", "The annual festival returns Saturday.")],
            )
        ],
    )
    edition = Edition(nameplate="T", city="C", state="S", date="D", pages=[page])
    cfg = replace(NewspaperConfig(), spot_color=True, spot_hex="#9E1B32")
    out = tmp_path / "spot_color.pdf"
    result = render_edition(edition, cfg, project_root=tmp_path, output_path=out, fonts=_base14())
    assert result.page_count == 1
    assert out.exists()


def test_inside_page_no_department(tmp_path) -> None:
    """Section band with an empty department string renders without error."""
    page = Page(
        number=2,
        template="opinion",
        department="",  # empty — the label will be a blank paragraph
        columns=3,
        main_items=[Story(headline="An Editorial View", level="secondary", body=[Block("p", "Opinion piece.")])],
    )
    edition = Edition(nameplate="T", city="C", state="S", date="D", pages=[page])
    out = tmp_path / "no_department.pdf"
    result = render_edition(edition, NewspaperConfig(), project_root=tmp_path, output_path=out, fonts=_base14())
    assert result.page_count == 1
    assert out.exists()
