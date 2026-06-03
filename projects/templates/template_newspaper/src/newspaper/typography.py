"""Typography for the newspaper: font registration and the paragraph stylesheet.

A newspaper's voice is its type. We register, when available, the elegant macOS
text faces a real paper would license — **Didot** for the nameplate and display
headlines, **Georgia** for body text, **Helvetica/Arial** for sans kickers and
labels — and fall back gracefully to ReportLab's always-present base-14 fonts
(Times, Helvetica) when a face is missing. Registration is therefore *best
effort and never fatal*: a checkout on a Linux CI box renders with Times and
still produces a structurally identical paper.

The :class:`Fonts` record names the four logical roles the rest of the engine
references, so no other module hard-codes a font name. :func:`build_stylesheet`
returns a :class:`~reportlab.lib.styles.StyleSheet1` with every newspaper style
the components need.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Ink that is not quite pure black reads as newsprint rather than laser toner.
INK = Color(0.08, 0.08, 0.09)
RULE_INK = Color(0.0, 0.0, 0.0)
MUTED = Color(0.32, 0.32, 0.34)

# Candidate macOS font files for each logical role. Each entry is
# (registered_name, path, subfont_index). The first that loads wins.
# NOTE on .ttc subfont indices: macOS Didot.ttc is [0]=Regular, [1]=Italic,
# [2]=Bold. Index 0 (Regular) is reliable across the candidate faces; the bold
# index is face-specific, so only Didot (whose order we have verified) is offered
# for the bold role — everything else falls back to Times-Bold.
_DISPLAY_CANDIDATES = [
    ("NP-Display", "/System/Library/Fonts/Supplemental/Didot.ttc", 0),
    ("NP-Display", "/System/Library/Fonts/Supplemental/Baskerville.ttc", 0),
    ("NP-Display", "/System/Library/Fonts/Supplemental/Hoefler Text.ttc", 0),
]
_DISPLAY_BOLD_CANDIDATES = [
    ("NP-DisplayBold", "/System/Library/Fonts/Supplemental/Didot.ttc", 2),
]
_BODY_CANDIDATES = [("NP-Body", "/System/Library/Fonts/Supplemental/Georgia.ttf", 0)]
_BODY_BOLD_CANDIDATES = [("NP-BodyBold", "/System/Library/Fonts/Supplemental/Georgia Bold.ttf", 0)]
_BODY_ITALIC_CANDIDATES = [("NP-BodyItalic", "/System/Library/Fonts/Supplemental/Georgia Italic.ttf", 0)]
_BODY_BOLDITALIC_CANDIDATES = [("NP-BodyBoldItalic", "/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf", 0)]
# A real sans TTF for kickers/labels/folios. Registering it EMBEDS the sans face
# (base-14 Helvetica is not embedded and fails to rasterise under some PDF
# renderers); Arial is metric-compatible and ships on macOS.
_SANS_CANDIDATES = [("NP-Sans", "/System/Library/Fonts/Supplemental/Arial.ttf", 0)]
_SANS_BOLD_CANDIDATES = [("NP-SansBold", "/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0)]


@dataclass(frozen=True)
class Fonts:
    """Resolved font names for each logical role used across the engine."""

    display: str
    display_bold: str
    body: str
    body_bold: str
    body_italic: str
    body_bolditalic: str
    sans: str
    sans_bold: str


def _try_register(candidates: list[tuple[str, str, int]]) -> str | None:
    """Register the first candidate font that exists; return its name or None."""
    for name, path, subfont in candidates:
        if not os.path.exists(path):
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont))
            return name
        except Exception:  # pragma: no cover - font file present but unparsable
            continue
    return None


def register_fonts() -> Fonts:
    """Register newspaper fonts, returning the resolved logical role names.

    Always succeeds: any role that cannot be satisfied from disk falls back to a
    ReportLab base-14 font so rendering never depends on a particular machine.
    """
    display = _try_register(_DISPLAY_CANDIDATES) or "Times-Roman"
    display_bold = _try_register(_DISPLAY_BOLD_CANDIDATES) or "Times-Bold"
    body = _try_register(_BODY_CANDIDATES) or "Times-Roman"
    body_bold = _try_register(_BODY_BOLD_CANDIDATES) or "Times-Bold"
    body_italic = _try_register(_BODY_ITALIC_CANDIDATES) or "Times-Italic"
    body_bolditalic = _try_register(_BODY_BOLDITALIC_CANDIDATES) or "Times-BoldItalic"

    # Register a bold/italic family map so inline <b>/<i> markup resolves to the
    # matching face instead of synthesising a slant.
    if body.startswith("NP-"):
        try:
            pdfmetrics.registerFontFamily(
                body,
                normal=body,
                bold=body_bold,
                italic=body_italic,
                boldItalic=body_bolditalic,
            )
        except Exception:  # pragma: no cover
            pass

    sans = _try_register(_SANS_CANDIDATES) or "Helvetica"
    sans_bold = _try_register(_SANS_BOLD_CANDIDATES) or "Helvetica-Bold"

    return Fonts(
        display=display,
        display_bold=display_bold,
        body=body,
        body_bold=body_bold,
        body_italic=body_italic,
        body_bolditalic=body_bolditalic,
        sans=sans,
        sans_bold=sans_bold,
    )


def build_stylesheet(fonts: Fonts) -> StyleSheet1:
    """Build the complete newspaper paragraph stylesheet."""
    ss = StyleSheet1()

    # --- Nameplate & folio -------------------------------------------------
    ss.add(
        ParagraphStyle(
            "Nameplate",
            fontName=fonts.display_bold,
            fontSize=78,
            leading=78,
            alignment=TA_CENTER,
            textColor=INK,
        )
    )
    ss.add(
        ParagraphStyle(
            "NameplateEar",
            fontName=fonts.sans,
            fontSize=7.2,
            leading=9,
            alignment=TA_CENTER,
            textColor=INK,
        )
    )
    ss.add(
        ParagraphStyle(
            "Folio",
            fontName=fonts.sans,
            fontSize=7.5,
            leading=9,
            alignment=TA_LEFT,
            textColor=INK,
        )
    )
    ss.add(
        ParagraphStyle(
            "Motto",
            fontName=fonts.body_italic,
            fontSize=8.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=MUTED,
        )
    )

    # --- Section furniture -------------------------------------------------
    ss.add(
        ParagraphStyle(
            "SectionLabel",
            fontName=fonts.sans_bold,
            fontSize=13,
            leading=14,
            alignment=TA_LEFT,
            textColor=INK,
        )
    )
    ss.add(
        ParagraphStyle(
            "RunningHead",
            fontName=fonts.sans,
            fontSize=7.5,
            leading=9,
            textColor=MUTED,
        )
    )

    # --- Headlines ---------------------------------------------------------
    ss.add(
        ParagraphStyle(
            "Kicker",
            fontName=fonts.sans_bold,
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            textColor=MUTED,
            spaceAfter=2,
        )
    )
    ss.add(
        ParagraphStyle(
            "HeadlineLead",
            fontName=fonts.display_bold,
            fontSize=44,
            leading=44,
            alignment=TA_LEFT,
            textColor=INK,
            spaceAfter=4,
            splitLongWords=0,
        )
    )
    ss.add(
        ParagraphStyle(
            "HeadlinePrimary",
            fontName=fonts.display_bold,
            fontSize=23,
            leading=24,
            alignment=TA_LEFT,
            textColor=INK,
            spaceBefore=4,
            spaceAfter=3,
            splitLongWords=0,
        )
    )
    ss.add(
        ParagraphStyle(
            "HeadlineSecondary",
            fontName=fonts.display_bold,
            fontSize=17,
            leading=18,
            alignment=TA_LEFT,
            textColor=INK,
            spaceBefore=4,
            spaceAfter=2,
            splitLongWords=0,
        )
    )
    ss.add(
        ParagraphStyle(
            "HeadlineMinor",
            fontName=fonts.body_bold,
            fontSize=12.5,
            leading=14,
            alignment=TA_LEFT,
            textColor=INK,
            spaceBefore=3,
            spaceAfter=1,
            splitLongWords=0,
        )
    )
    ss.add(
        ParagraphStyle(
            "Deck",
            fontName=fonts.body_italic,
            fontSize=12.5,
            leading=15.5,
            alignment=TA_LEFT,
            textColor=MUTED,
            spaceAfter=4,
        )
    )

    # --- Bylines & datelines ----------------------------------------------
    ss.add(
        ParagraphStyle(
            "Byline",
            fontName=fonts.sans_bold,
            fontSize=8.5,
            leading=10.5,
            alignment=TA_LEFT,
            textColor=INK,
            spaceBefore=2,
        )
    )
    ss.add(
        ParagraphStyle(
            "Bio",
            fontName=fonts.sans,
            fontSize=7.5,
            leading=9.5,
            alignment=TA_LEFT,
            textColor=MUTED,
            spaceAfter=3,
        )
    )

    # --- Body --------------------------------------------------------------
    ss.add(
        ParagraphStyle(
            "Body",
            fontName=fonts.body,
            fontSize=9.6,
            leading=12.4,
            alignment=TA_JUSTIFY,
            textColor=INK,
            firstLineIndent=11,
            hyphenationLang="en_US",
            embeddedHyphenation=1,
            spaceAfter=0,
        )
    )
    ss.add(
        ParagraphStyle(
            "BodyFirst",
            parent=ss["Body"],
            firstLineIndent=0,
        )
    )
    ss.add(
        ParagraphStyle(
            "Subhead",
            fontName=fonts.sans_bold,
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT,
            textColor=INK,
            spaceBefore=5,
            spaceAfter=1,
        )
    )

    # --- Pull quotes & boxes ----------------------------------------------
    ss.add(
        ParagraphStyle(
            "PullQuote",
            fontName=fonts.display,
            fontSize=16,
            leading=19,
            alignment=TA_LEFT,
            textColor=INK,
        )
    )
    ss.add(
        ParagraphStyle(
            "PullAttribution",
            fontName=fonts.sans_bold,
            fontSize=8,
            leading=10,
            alignment=TA_LEFT,
            textColor=MUTED,
            spaceBefore=3,
        )
    )
    ss.add(
        ParagraphStyle(
            "BoxTitle",
            fontName=fonts.sans_bold,
            fontSize=10.5,
            leading=12,
            alignment=TA_LEFT,
            textColor=INK,
            spaceAfter=2,
        )
    )
    ss.add(
        ParagraphStyle(
            "BoxBody",
            fontName=fonts.body,
            fontSize=8.6,
            leading=11,
            alignment=TA_LEFT,
            textColor=INK,
        )
    )
    ss.add(
        ParagraphStyle(
            "Caption",
            fontName=fonts.sans,
            fontSize=7.6,
            leading=9.4,
            alignment=TA_LEFT,
            textColor=MUTED,
            spaceBefore=2,
        )
    )
    ss.add(
        ParagraphStyle(
            "CaptionCredit",
            fontName=fonts.sans_bold,
            fontSize=6.6,
            leading=8,
            alignment=TA_LEFT,
            textColor=MUTED,
        )
    )

    # --- Index / classifieds ----------------------------------------------
    ss.add(
        ParagraphStyle(
            "IndexItem",
            fontName=fonts.body,
            fontSize=8.4,
            leading=11.5,
            alignment=TA_LEFT,
            textColor=INK,
        )
    )
    ss.add(
        ParagraphStyle(
            "ClassifiedCat",
            fontName=fonts.sans_bold,
            fontSize=8.5,
            leading=10,
            alignment=TA_LEFT,
            textColor=INK,
            spaceBefore=4,
            spaceAfter=1,
        )
    )
    ss.add(
        ParagraphStyle(
            "Classified",
            fontName=fonts.body,
            fontSize=7.8,
            leading=9.3,
            alignment=TA_LEFT,
            textColor=INK,
        )
    )
    ss.add(
        ParagraphStyle(
            "Tabular",
            fontName=fonts.body,
            fontSize=8.0,
            leading=10,
            alignment=TA_LEFT,
            textColor=INK,
        )
    )
    return ss


__all__ = ["Fonts", "INK", "RULE_INK", "MUTED", "register_fonts", "build_stylesheet"]
