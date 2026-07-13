"""Page furniture: everything drawn directly on the canvas, not flowed.

The nameplate, the flanking "ears", the motto, the folio lines, the per-section
banner, the hairline column rules and the spanning front-page lead headline are
all *drawn* at computed coordinates rather than poured into frames. Drawing them
here lets the column grid begin at a y-coordinate this module returns, so the
flowed body always clears the furniture above it.

Every public function takes the live ReportLab ``canvas`` and returns the
y-coordinate (in points, origin bottom-left) at which column content may begin,
or ``None`` for footer furniture that does not affect the body top.
"""

from __future__ import annotations

from reportlab.lib.colors import Color
from reportlab.lib.styles import StyleSheet1
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Frame, Paragraph

from .content import Edition, Page, Story
from .geometry import ColumnGrid, PageGeometry
from .typography import INK, MUTED, Fonts

FOLIO_HEIGHT = 26.0


def _rule(c: Canvas, x1: float, y: float, x2: float, width: float, color: Color = INK) -> None:
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.setLineCap(0)
    c.line(x1, y, x2, y)
    c.restoreState()


def _vrule(c: Canvas, x: float, y1: float, y2: float, width: float = 0.5, color: Color = MUTED) -> None:
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x, y1, x, y2)
    c.restoreState()


def _draw_top(c: Canvas, flowable: object, x: float, top_y: float, width: float) -> float:
    """Wrap a flowable to ``width`` and draw it with its top at ``top_y``.

    Returns the height consumed.
    """
    w, h = flowable.wrapOn(c, width, 100_000)  # type: ignore[attr-defined]
    flowable.drawOn(c, x, top_y - h)  # type: ignore[attr-defined]
    return float(h)


def draw_nameplate(
    c: Canvas, edition: Edition, geom: PageGeometry, styles: StyleSheet1, fonts: Fonts, spot: Color | None = None
) -> float:
    """Draw the front-page nameplate block; return the body-top y-coordinate.

    When ``spot`` is provided (``spot_color`` enabled), the nameplate and the
    heavy rule beneath it render in the spot color — a classic colored-flag look.
    """
    flag_ink = spot or INK
    left, right = geom.content_left, geom.content_right
    width = geom.content_width
    y = geom.content_top

    # ── Grand top double rule ─────────────────────────────────────────
    _rule(c, left, y, right, 1.8, flag_ink)
    y -= 3.5
    _rule(c, left, y, right, 0.6)
    y -= 16

    name = edition.nameplate
    font = styles["Nameplate"].fontName

    # Reserve compact boxed "ears" on each flank and fit the nameplate to the
    # clear zone strictly BETWEEN them, so the big letters never collide with
    # the ear text.
    ear_w = 1.22 * 72
    gap = 22.0
    name_zone = width - 2.0 * (ear_w + gap)
    size = 122.0
    measured = c.stringWidth(name, font, size)
    if measured > name_zone:
        size *= name_zone / measured
    size = min(size, 122.0)
    cap_h = size * 0.70  # Didot cap height fraction
    name_top = y
    baseline = name_top - cap_h
    cap_center_y = name_top - cap_h / 2.0

    # Grand nameplate (reliable centred draw).
    c.saveState()
    c.setFillColor(flag_ink)
    c.setFont(font, size)
    c.drawCentredString((left + right) / 2.0, baseline, name)
    c.restoreState()

    # Boxed ears, vertically centred on the cap band (Paragraph flowables).
    def _draw_ear(html: str, x: float) -> None:
        ear = Paragraph(html, styles["NameplateEar"])
        _, eh = ear.wrapOn(c, ear_w - 14, 160)
        box_h = eh + 14
        ear.drawOn(c, x + 7, cap_center_y - eh / 2.0)
        c.saveState()
        c.setStrokeColor(MUTED)
        c.setLineWidth(0.6)
        c.rect(x, cap_center_y - box_h / 2.0, ear_w, box_h, stroke=1, fill=0)
        c.restoreState()

    _draw_ear(
        f"<b>ESTABLISHED {edition.established}</b><br/>{edition.city}<br/>{edition.state}",
        left,
    )
    if edition.weather_strip:
        _draw_ear(edition.weather_strip.replace("\n", "<br/>"), right - ear_w)

    # Advance below the descenders with generous breathing room.
    y = baseline - size * 0.24 - 12
    if edition.motto:
        motto = Paragraph(edition.motto, styles["Motto"])
        y -= _draw_top(c, motto, left, y, width)
    y -= 9

    _rule(c, left, y, right, 2.6, flag_ink)
    y -= 12

    c.saveState()
    c.setFillColor(INK)
    c.setFont(fonts.sans, 8)
    folio_bits = []
    if edition.volume:
        folio_bits.append(f"VOL. {edition.volume}")
    if edition.number:
        folio_bits.append(f"NO. {edition.number}")
    c.drawString(left, y, "  •  ".join(folio_bits))
    center = f"{edition.city.upper()}, {edition.state.upper()}  •  {edition.date.upper()}"
    if edition.edition_label:
        center += f"  •  {edition.edition_label.upper()}"
    c.drawCentredString((left + right) / 2.0, y, center)
    if edition.price:
        c.drawRightString(right, y, edition.price.upper())
    c.restoreState()
    y -= 6

    _rule(c, left, y, right, 0.6)
    y -= 5
    return y


def draw_section_band(
    c: Canvas,
    page: Page,
    edition: Edition,
    geom: PageGeometry,
    styles: StyleSheet1,
    fonts: Fonts,
    spot: Color | None = None,
) -> float:
    """Draw the inside-page section banner; return the body-top y-coordinate.

    When ``spot`` is set, the section label and the heavy band rule take the
    spot color.
    """
    band_ink = spot or INK
    left, right = geom.content_left, geom.content_right
    y = geom.content_top

    c.saveState()
    c.setFillColor(MUTED)
    c.setFont(fonts.sans, 7.5)
    c.drawRightString(right, y - 8, f"{edition.nameplate.upper()}   |   {edition.date.upper()}")
    c.restoreState()

    label_style = styles["SectionLabel"].clone("SpotSection", textColor=spot) if spot else styles["SectionLabel"]
    label = Paragraph((page.department or "").upper(), label_style)
    lh = float(label.wrapOn(c, geom.content_width * 0.7, 40)[1])
    label.drawOn(c, left, y - lh)
    y -= max(lh, 14) + 3

    _rule(c, left, y, right, 2.0, band_ink)
    y -= 4
    _rule(c, left, y, right, 0.5)
    y -= 6
    return y


def draw_folio(c: Canvas, page: Page, edition: Edition, geom: PageGeometry, fonts: Fonts) -> None:
    """Draw the bottom folio line (page id, paper, date)."""
    left, right = geom.content_left, geom.content_right
    y = geom.content_bottom + FOLIO_HEIGHT
    _rule(c, left, y, right, 0.5)
    baseline = geom.content_bottom + 8
    c.saveState()
    c.setFillColor(INK)
    c.setFont(fonts.sans_bold, 8)
    c.drawString(left, baseline, f"{page.section}{page.number}")
    c.setFont(fonts.sans, 8)
    c.drawCentredString((left + right) / 2.0, baseline, edition.nameplate.upper())
    c.drawRightString(right, baseline, edition.date.upper())
    c.restoreState()


def draw_column_rules(c: Canvas, grid: ColumnGrid, top: float, bottom: float) -> None:
    """Draw hairline vertical rules down each interior gutter."""
    for x in grid.gutter_centers():
        _vrule(c, x, bottom, top, width=0.5, color=MUTED)


def draw_lead_headline(
    c: Canvas, story: Story, x: float, top_y: float, width: float, styles: StyleSheet1, fonts: Fonts
) -> float:
    """Draw the spanning lead kicker + headline + deck; return consumed height."""
    consumed = 0.0
    if story.kicker:
        kick = Paragraph(story.kicker.upper(), styles["Kicker"].clone("LeadKicker", fontSize=10, alignment=1))
        consumed += _draw_top(c, kick, x, top_y - consumed, width)
        consumed += 1
    head = Paragraph(
        story.headline,
        # leading=54 (fontSize 44 * ~1.23) — not 46 (~1.05): the display face
        # is a Didot-style serif with deep, thin descenders (comma tails,
        # "g"/"y"). At leading=46 a comma or descender on the headline's last
        # line sits almost on the baseline of the deck's first line, and at
        # typical render resolutions the two visually merge into what looks
        # like a stray glyph (see tests/test_furniture.py for the regression
        # guard on this gap).
        styles["HeadlineLead"].clone("LeadHead", alignment=1, leading=54),
    )
    consumed += _draw_top(c, head, x, top_y - consumed, width)
    consumed += 7
    if story.deck:
        deck = Paragraph(
            story.deck,
            styles["Deck"].clone("LeadDeck", alignment=1, fontSize=13.5, leading=19),
        )
        # centre the deck on a narrower measure for an elegant inverted pyramid
        deck_w = width * 0.82
        consumed += _draw_top(c, deck, x + (width - deck_w) / 2.0, top_y - consumed, deck_w)
    consumed += 4
    _rule(c, x, top_y - consumed, x + width, 0.5, MUTED)
    consumed += 6
    return consumed


def draw_draft_grid(c: Canvas, frames: list[Frame], color: Color = Color(0.85, 0.2, 0.2)) -> None:  # pragma: no cover
    """Debug overlay: outline each frame."""
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(0.4)
    for fr in frames:
        c.rect(fr.x1, fr.y1, fr.width, fr.height, stroke=1, fill=0)
    c.restoreState()


__all__ = [
    "FOLIO_HEIGHT",
    "draw_nameplate",
    "draw_section_band",
    "draw_folio",
    "draw_column_rules",
    "draw_lead_headline",
    "draw_draft_grid",
]
