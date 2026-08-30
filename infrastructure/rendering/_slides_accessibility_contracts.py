"""Shared contracts and geometry constants for accessible slide rendering.

Keeping policy objects and stable diagnostic construction in this dependency
leaf lets the AST, table, composition, and Reveal helpers remain cohesive
without importing one another cyclically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from infrastructure.core.exceptions import RenderingError


# Stable 16:9 projection geometry for the opt-in accessible profile. The
# public policy's 80-word value is an absolute ceiling, not a promise that 80
# unusually long words fit on every frame. These conservative estimates are
# calibrated against the profile's 28/20/16-point native floors.
BASE_BODY_LINES_16_9 = 8
BODY_CHARACTERS_PER_LINE_20PT = 43
LIST_CHARACTERS_PER_LINE_20PT = 34
TITLE_CHARACTERS_PER_LINE_28PT = 36
BODY_LINES_PER_EXTRA_TITLE_LINE = 2
# One-line title capacity at the 28-point floor. The continuation compactor
# subtracts the complete `` (part N)`` suffix before selecting visible words.
# The authored heading remains the frame's accessible name.
CONTINUATION_TITLE_TARGET_CHARS = TITLE_CHARACTERS_PER_LINE_28PT
TABLE_INTERCOLUMN_GUTTER_CHARACTERS = 1
TABLE_RULE_PADDING_LINES = 1
TABLE_MINIMUM_COLUMN_CHARACTERS = 2
SEMANTIC_BREAK_SUFFIXES = (".", "?", "!", ";", ":", "—")
CROSS_REFERENCE_LABELS = {
    "alg": "alg.",
    "cor": "cor.",
    "def": "def.",
    "eq": "eq.",
    "ex": "ex.",
    "fig": "fig.",
    "lem": "lem.",
    "lst": "lst.",
    "prop": "prop.",
    "rem": "rem.",
    "sec": "sec.",
    "subsec": "sec.",
    "tbl": "tbl.",
    "thm": "thm.",
}
CLAUSE_COORDINATORS = {
    "although",
    "and",
    "because",
    "but",
    "so",
    "whereas",
    "while",
    "which",
    "yet",
}


@dataclass(frozen=True)
class AccessibleSlidePolicy:
    """Fail-closed density and typography policy for presentation derivatives."""

    max_prose_words: int = 80
    max_table_rows: int = 8
    min_figure_area_percent: int = 70
    title_font_pt: int = 28
    body_font_pt: int = 20
    figure_label_font_pt: int = 16
    reader_href: str = "../web/index.html"


@dataclass(frozen=True)
class AccessibleSlideComposition:
    """One deterministic AST composition result and its review counts."""

    document: dict[str, Any]
    frame_count: int
    section_divider_count: int
    excerpted_table_count: int
    figure_frame_count: int


@dataclass(frozen=True)
class _Frame:
    """One internal semantic frame before Pandoc block serialization."""

    title: dict[str, Any]
    blocks: tuple[dict[str, Any], ...]
    kind: str
    continuation: int


def density_error(
    code: str,
    message: str,
    *,
    source: str,
    heading: str,
    **context: object,
) -> RenderingError:
    """Return one actionable, stable accessible-slide density diagnostic."""

    return RenderingError(
        f"[{code}] {message}",
        context={"source": source, "heading": heading, "diagnostic_code": code, **context},
        suggestions=[
            "Add a semantic subheading or split the indivisible source block.",
            "Keep the complete material in the canonical HTML manuscript and present a bounded excerpt.",
        ],
    )


__all__ = ["AccessibleSlideComposition", "AccessibleSlidePolicy"]
