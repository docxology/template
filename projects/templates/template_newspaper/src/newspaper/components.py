"""Flowable builders: the typographic vocabulary of the page.

Everything that flows *inside* a column — a story's headline and body, a drop
cap, a boxed weather table, a pull quote, a photo with its cutline — is built
here as ReportLab flowables. The :mod:`newspaper.layout` module then pours these
into column frames. Furniture that is *drawn* rather than flowed (the nameplate,
section bands, folios, the spanning lead headline) lives in
:mod:`newspaper.furniture`.

Boxes are realised as single-cell tables so a real ruled border travels with the
content; a missing figure degrades to a clearly-labelled placeholder rather than
crashing the render.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    Image,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .content import Ad, Box, Figure, Story
from .typography import INK, MUTED, Fonts

_BOX_BG = Color(0.945, 0.94, 0.93)
_PLACEHOLDER_BG = Color(0.86, 0.86, 0.87)


def _hex(value: str, default: Color) -> Color:
    """Parse a ``#RRGGBB`` string to a ReportLab Color, falling back on default.

    An empty string or any unparseable value returns ``default`` unchanged so
    callers never need to guard against bad hex in YAML content.
    """
    if not value:
        return default
    try:
        return HexColor(value)
    except Exception:  # noqa: BLE001 - final handler: broad by design so any parse/IO/asset failure falls back gracefully; narrowing would create silent gaps
        return default


def hairline(width: float = 0.6, color: Color = INK, space_before: float = 2, space_after: float = 3) -> HRFlowable:
    """A thin horizontal rule that spans the current frame width."""
    return HRFlowable(
        width="100%",
        thickness=width,
        color=color,
        spaceBefore=space_before,
        spaceAfter=space_after,
        lineCap="butt",
    )


# Author markup we deliberately allow through to ReportLab's mini-HTML parser.
_ALLOWED_TAGS = re.compile(r"</?(?:b|i|u|strong|em|sub|sup)>|<br\s*/?>|</?font\b[^>]*>", re.IGNORECASE)
# A bare '&' that is NOT already the start of a character/entity reference.
_BARE_AMP = re.compile(r"&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)")


def _escape_text(segment: str) -> str:
    """Escape `&`, `<`, `>` in a non-markup text segment, preserving entities."""
    segment = _BARE_AMP.sub("&amp;", segment)
    return segment.replace("<", "&lt;").replace(">", "&gt;")


def _esc(text: str) -> str:
    """Escape plain text for ReportLab mini-HTML, preserving an allowlist of tags.

    Stray ``&``/``<``/``>`` (``AT&T``, ``5 < 10``) are escaped so they render
    literally instead of silently corrupting the paragraph or aborting the
    render, while intentional ``<b>``/``<i>``/``<br/>``/``<font …>`` markup and
    existing entities (``&amp;``) pass through unchanged.
    """
    out: list[str] = []
    last = 0
    for m in _ALLOWED_TAGS.finditer(text):
        out.append(_escape_text(text[last : m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(_escape_text(text[last:]))
    return "".join(out)


def _drop_cap(text: str, styles: StyleSheet1, fonts: Fonts) -> Table:
    """Render the first paragraph with a raised initial capital."""
    initial = text[0]
    rest = text[1:].lstrip()
    cap_style = styles["HeadlineSecondary"].clone(
        "DropCapInitial", fontName=fonts.display_bold, fontSize=33, leading=27, textColor=INK
    )
    cap = Paragraph(html.escape(initial), cap_style)
    para = Paragraph(_esc(rest), styles["BodyFirst"])
    tbl = Table([[cap, para]], colWidths=[24, None])
    tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (0, 0), "TOP"),
                ("VALIGN", (1, 0), (1, 0), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 4),
                ("RIGHTPADDING", (1, 0), (1, 0), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return tbl


def pull_quote(quote: str, attribution: str, styles: StyleSheet1) -> Table:
    """A ruled pull quote that interrupts the column."""
    inner: list[Flowable] = [Paragraph(f"“{_esc(quote)}”", styles["PullQuote"])]
    if attribution:
        inner.append(Paragraph(f"— {_esc(attribution)}", styles["PullAttribution"]))
    tbl = Table([[inner]], colWidths=["100%"])
    tbl.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, 0), 1.4, INK),
                ("LINEBELOW", (0, -1), (-1, -1), 1.4, INK),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return tbl


def _resolve_image_path(path: str, project_root: Path) -> Path | None:
    """Resolve a figure or ad graphic path relative to ``project_root``.

    Absolute paths are used as-is; relative paths are joined to ``project_root``
    (e.g. ``output/figures/harbor.png``). Returns ``None`` if the resolved path
    does not exist on disk so callers degrade gracefully to a placeholder.
    """
    candidate = (project_root / path) if not Path(path).is_absolute() else Path(path)
    return candidate if candidate.exists() else None


def figure_flowables(fig: Figure, width: float, styles: StyleSheet1, project_root: Path) -> list[Flowable]:
    """Build a photo/illustration block with cutline, scaled to ``width``."""
    out: list[Flowable] = []
    resolved = _resolve_image_path(fig.path, project_root)
    if resolved is not None:
        try:
            img = Image(str(resolved))
            scale = width / float(img.imageWidth)
            img.drawWidth = width
            img.drawHeight = float(img.imageHeight) * scale
            out.append(img)
        except (
            Exception
        ):  # pragma: no cover - corrupt image  # noqa: BLE001 - defensive: corrupt/unreadable asset, skip gracefully
            resolved = None
    if resolved is None:
        placeholder = Table([[Paragraph("photo", styles["Caption"])]], colWidths=[width], rowHeights=[fig.height])
        placeholder.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), _PLACEHOLDER_BG),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("BOX", (0, 0), (-1, -1), 0.5, MUTED),
                ]
            )
        )
        out.append(placeholder)
    if fig.caption or fig.credit:
        cut = fig.caption
        if fig.credit:
            cut += f'  <font name="{styles["CaptionCredit"].fontName}">/ {fig.credit}</font>'
        out.append(hairline(0.4, MUTED, space_before=2, space_after=1))
        out.append(Paragraph(_esc(cut), styles["Caption"]))
    out.append(Spacer(1, 6))
    return out


_HEADLINE_BY_LEVEL = {
    "lead": "HeadlineLead",
    "primary": "HeadlinePrimary",
    "secondary": "HeadlineSecondary",
    "minor": "HeadlineMinor",
}


def _body_flowables(story: Story, styles: StyleSheet1, fonts: Fonts) -> list[Flowable]:
    out: list[Flowable] = []
    first_para_done = False
    for block in story.body:
        if block.kind == "subhead":
            out.append(Paragraph(_esc(block.text), styles["Subhead"]))
        elif block.kind == "pull":
            out.append(pull_quote(block.text, block.attribution, styles))
        else:  # paragraph
            if not first_para_done:
                if story.drop_cap and len(block.text) > 1:
                    out.append(_drop_cap(block.text, styles, fonts))
                else:
                    out.append(Paragraph(_esc(block.text), styles["BodyFirst"]))
                first_para_done = True
            else:
                out.append(Paragraph(_esc(block.text), styles["Body"]))
    return out


def story_flowables(
    story: Story,
    styles: StyleSheet1,
    fonts: Fonts,
    *,
    measure: float,
    project_root: Path,
    include_headline: bool = True,
) -> list[Flowable]:
    """Build the full flowable sequence for a story.

    When ``include_headline`` is False the headline/kicker/deck are omitted —
    used for the front-page lead, whose display headline is drawn as spanning
    furniture above the columns.
    """
    out: list[Flowable] = []
    if include_headline:
        if story.kicker:
            out.append(Paragraph(html.escape(story.kicker.upper()), styles["Kicker"]))
        style_name = _HEADLINE_BY_LEVEL.get(story.level, "HeadlineSecondary")
        out.append(Paragraph(_esc(story.headline), styles[style_name]))
        if story.deck:
            out.append(Paragraph(_esc(story.deck), styles["Deck"]))
    if story.figure is not None:
        out.extend(figure_flowables(story.figure, measure, styles, project_root))
    if story.byline:
        out.append(Paragraph(html.escape(story.byline), styles["Byline"]))
        out.append(hairline(0.4, MUTED, space_before=1, space_after=3))
    out.extend(_body_flowables(story, styles, fonts))
    if story.jump:
        out.append(Paragraph(f"<i>{_esc(story.jump)}</i>", styles["Bio"]))
    out.append(Spacer(1, 7))
    return out


# ---------------------------------------------------------------------------
# Boxed modules
# ---------------------------------------------------------------------------


def _boxed(inner: list[Flowable], width: float, *, shaded: bool = True, heavy_top: bool = True) -> Table:
    tbl = Table([[inner]], colWidths=[width])
    style: list[tuple[Any, ...]] = [
        ("BOX", (0, 0), (-1, -1), 0.75, INK),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    if shaded:
        style.append(("BACKGROUND", (0, 0), (-1, -1), _BOX_BG))
    if heavy_top:
        style.append(("LINEABOVE", (0, 0), (-1, 0), 2.2, INK))
    tbl.setStyle(TableStyle(style))
    return tbl


def _data_table(box: Box, styles: StyleSheet1, fonts: Fonts, width: float) -> Table:
    """Render a box's tabular rows with an optional header row."""
    head = box.columns
    body_rows = box.rows
    data: list[list[object]] = []
    if head:
        data.append([Paragraph(f"<b>{html.escape(c)}</b>", styles["Tabular"]) for c in head])
    for row in body_rows:
        data.append([Paragraph(_esc(c), styles["Tabular"]) for c in row])
    ncols = max((len(r) for r in data), default=1)
    col_w = width / ncols
    tbl = Table(data, colWidths=[col_w] * ncols)
    ts: list[tuple[Any, ...]] = [
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    if head:
        ts.append(("LINEBELOW", (0, 0), (-1, 0), 0.6, INK))
        ts.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [None, Color(0.95, 0.95, 0.94)]))
    tbl.setStyle(TableStyle(ts))
    return tbl


def classified_flowables(box: Box, styles: StyleSheet1) -> list[Flowable]:
    """Render a classified category as dense, unboxed, splittable copy.

    Unlike :func:`box_flowables`, this packs a category title plus many short
    ads into the column flow so a long classifieds section fills and splits
    naturally across narrow columns — the way a real classified page reads.
    """
    out: list[Flowable] = []
    if box.title:
        out.append(Paragraph(html.escape(box.title.upper()), styles["ClassifiedCat"]))
        out.append(hairline(0.5, INK, space_before=0, space_after=2))
    for item in box.items:
        out.append(Paragraph(_esc(item), styles["Classified"]))
    for blk in box.body:
        out.append(Paragraph(_esc(blk.text), styles["Classified"]))
    out.append(Spacer(1, 5))
    return out


def box_flowables(box: Box, styles: StyleSheet1, fonts: Fonts, *, width: float) -> list[Flowable]:
    """Build a boxed module appropriate to ``box.kind``."""
    inner: list[Flowable] = []
    if box.title:
        inner.append(Paragraph(html.escape(box.title.upper()), styles["BoxTitle"]))
        inner.append(hairline(0.6, INK, space_before=1, space_after=4))

    inner_width = width - 14  # account for box padding

    if box.kind == "index":
        for item in box.items:
            inner.append(Paragraph(_esc(item), styles["IndexItem"]))
    elif box.kind in {"weather", "tides", "table", "almanac", "calendar"}:
        if box.body:
            for blk in box.body:
                inner.append(Paragraph(_esc(blk.text), styles["BoxBody"]))
            inner.append(Spacer(1, 3))
        if box.rows:
            inner.append(_data_table(box, styles, fonts, inner_width))
    elif box.kind == "staff":
        for item in box.items:
            inner.append(Paragraph(_esc(item), styles["BoxBody"]))
    elif box.kind == "briefs":
        for blk in box.body:
            if blk.kind == "subhead":
                inner.append(Paragraph(html.escape(blk.text), styles["HeadlineMinor"]))
            else:
                inner.append(Paragraph(_esc(blk.text), styles["BoxBody"]))
                inner.append(Spacer(1, 2))
    else:  # generic
        for blk in box.body:
            inner.append(Paragraph(_esc(blk.text), styles["BoxBody"]))
        for item in box.items:
            inner.append(Paragraph(_esc(item), styles["BoxBody"]))

    if box.footnote:
        inner.append(Spacer(1, 2))
        inner.append(Paragraph(f"<i>{_esc(box.footnote)}</i>", styles["CaptionCredit"]))

    shaded = box.kind not in {"briefs", "staff"}
    boxed = _boxed(inner, width, shaded=shaded)
    # Return the box as a single non-splitting flowable. If it does not fit the
    # current column it moves whole to the next; if it fits no column it is left
    # unplaced and counted as over-set — never silently shrunk below legibility.
    return [boxed, Spacer(1, 7)]


def ad_flowables(ad: Ad, styles: StyleSheet1, fonts: Fonts, *, width: float, project_root: Path) -> list[Flowable]:
    """Build a color-capable display advertisement.

    Supports a background tint, an accent (border + sponsor) color, an optional
    color graphic, and centered ad copy — so the template demonstrates real
    color display advertising amid the monochrome news. Like boxes, an ad is a
    non-splitting flowable, so an over-tall ad is reported as over-set rather
    than silently shrunk.
    """
    accent = _hex(ad.accent, INK)
    bg = _hex(ad.background, white)
    double = ad.border == "double"
    inner_width = (width - 10) if double else width
    pad_w = inner_width - 16  # content width inside cell padding

    inner: list[Flowable] = [
        Paragraph(
            "ADVERTISEMENT",
            ParagraphStyle(
                "AdLabel",
                fontName=fonts.sans,
                fontSize=5.6,
                leading=7,
                alignment=TA_CENTER,
                textColor=MUTED,
                spaceAfter=3,
            ),
        )
    ]

    if ad.graphic:
        resolved = _resolve_image_path(ad.graphic, project_root)
        if resolved is not None:
            try:
                img = Image(str(resolved))
                aspect = float(img.imageHeight) / float(img.imageWidth)
                gw = min(pad_w, ad.graphic_height / aspect)
                img.drawWidth = gw
                img.drawHeight = gw * aspect
                img.hAlign = "CENTER"
                inner.append(img)
                inner.append(Spacer(1, 4))
            except (OSError, TypeError, ValueError, ZeroDivisionError):
                pass

    inner.append(
        Paragraph(
            _esc(ad.sponsor),
            ParagraphStyle(
                "AdSponsor",
                fontName=fonts.display_bold,
                fontSize=17,
                leading=19,
                alignment=TA_CENTER,
                textColor=accent,
                spaceAfter=2,
            ),
        )
    )
    if ad.tagline:
        inner.append(
            Paragraph(
                _esc(ad.tagline),
                ParagraphStyle(
                    "AdTag",
                    fontName=fonts.body_italic,
                    fontSize=9.5,
                    leading=11.5,
                    alignment=TA_CENTER,
                    textColor=INK,
                    spaceAfter=3,
                ),
            )
        )
    body_style = ParagraphStyle(
        "AdBody", fontName=fonts.body, fontSize=8.4, leading=10.4, alignment=TA_CENTER, textColor=INK, spaceAfter=2
    )
    for blk in ad.body:
        inner.append(Paragraph(_esc(blk.text), body_style))
    if ad.contact:
        inner.append(Spacer(1, 2))
        inner.append(
            Paragraph(
                _esc(ad.contact),
                ParagraphStyle(
                    "AdContact",
                    fontName=fonts.sans_bold,
                    fontSize=8.5,
                    leading=10.5,
                    alignment=TA_CENTER,
                    textColor=accent,
                ),
            )
        )

    cell = Table([[inner]], colWidths=[inner_width], rowHeights=[ad.height] if ad.height > 0 else None)
    style: list[tuple[Any, ...]] = [
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), bg),
    ]
    if ad.border != "none":
        weight = {"box": 1.0, "double": 1.0, "thick": 3.0}[ad.border]
        style.append(("BOX", (0, 0), (-1, -1), weight, accent))
    cell.setStyle(TableStyle(style))

    out_flowable: Flowable = cell
    if double:
        outer = Table([[cell]], colWidths=[width])
        outer.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1.0, accent),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        out_flowable = outer

    return [out_flowable, Spacer(1, 8)]


__all__ = [
    "hairline",
    "pull_quote",
    "figure_flowables",
    "story_flowables",
    "box_flowables",
    "classified_flowables",
    "ad_flowables",
]
