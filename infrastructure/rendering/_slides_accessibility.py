"""Semantic composition and accessibility post-processing for slide decks.

The default ``archive`` slide profile deliberately retains the historical
Pandoc/Beamer path.  The opt-in ``accessible`` profile uses Pandoc's JSON AST
as a format-neutral boundary: both Beamer and Reveal.js consume the same
semantically grouped frames, and no renderer has to guess where a Markdown
paragraph, list, table, equation, code block, or figure ends.

This module does not compute manuscript results or rewrite the canonical
reader.  It composes a presentation derivative and links dense captions and
complete tables back to the HTML manuscript.
"""

from __future__ import annotations

import copy
import hashlib
import html
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._web_postprocess import (
    enhance_accessibility,
    normalize_figure_paths,
    write_if_changed,
)


_WORD_RE = re.compile(r"[\w]+(?:[-'][\w]+)*", flags=re.UNICODE)
_SLIDE_OPEN_RE = re.compile(
    r"(?P<open><section\b(?P<attrs>[^>]*)>)(?P<spacing>\s*)"
    r"(?P<heading><h(?P<level>[1-6])\b(?P<heading_attrs>[^>]*)>.*?</h(?P=level)>)",
    flags=re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_STANDALONE_HTML_RE = re.compile(r"(?:<!doctype\s+html\b|<html(?:\s|>))", flags=re.IGNORECASE)
_ACCESSIBLE_REVEAL_MARKERS = (
    "data-template-accessible-slides",
    'aria-label="Presentation companion"',
    'aria-label="Presentation slides"',
    'aria-roledescription="slide"',
    "overflow-x: hidden",
)

# Stable 16:9 projection geometry for the opt-in accessible profile.  The
# public policy's 80-word value is an absolute ceiling, not a promise that 80
# unusually long words fit on every frame.  These conservative line estimates
# let the semantic composer account for wrapping before the fail-closed TeX
# overflow check.  They were calibrated against the profile's 28/20/16-point
# native floors, not against a shrunken-font fallback.
_BASE_BODY_LINES_16_9 = 8
_BODY_CHARACTERS_PER_LINE_20PT = 43
_LIST_CHARACTERS_PER_LINE_20PT = 34
_TITLE_CHARACTERS_PER_LINE_28PT = 36
_BODY_LINES_PER_EXTRA_TITLE_LINE = 2
_CONTINUATION_TITLE_TARGET_CHARS = 48
_TABLE_INTERCOLUMN_GUTTER_CHARACTERS = 1
_TABLE_RULE_PADDING_LINES = 1
_TABLE_MINIMUM_COLUMN_CHARACTERS = 2
_SEMANTIC_BREAK_SUFFIXES = (".", "?", "!", ";", ":", "—")
_CLAUSE_COORDINATORS = {
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
_PRESENTATION_PAGE_BREAK_RE = re.compile(r"^\\(?:clearpage|newpage|pagebreak)\s*$")
_EQUATION_LABEL_RE = re.compile(r"^\{#(?:eq|def|prop|lem|thm):[^{}]+\}$")


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
    title: dict[str, Any]
    blocks: tuple[dict[str, Any], ...]
    kind: str
    continuation: int


def _density_error(
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


def _plain_text(value: object) -> str:
    """Extract human-readable text from a Pandoc JSON fragment."""

    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(part for item in value if (part := _plain_text(item)))
    if not isinstance(value, dict):
        return ""
    tag = value.get("t")
    content = value.get("c")
    if tag in {"Space", "SoftBreak", "LineBreak"}:
        return " "
    if tag == "Cite" and isinstance(content, list) and content:
        citations = content[0]
        count = len(citations) if isinstance(citations, list) else 1
        # Citation identifiers are much longer than their rendered author-year
        # form, but treating a whole cluster as one short token underestimates
        # the projected line cost.  A stable author-year placeholder per item
        # is conservative without depending on a particular CSL style.
        return " ".join("(Author, 0000)" for _ in range(max(1, count)))
    if tag == "Link" and isinstance(content, list) and len(content) >= 2:
        return _plain_text(content[1])
    if tag == "Note":
        return ""
    if tag in {"Code", "Math"} and isinstance(content, list) and content:
        return str(content[-1])
    return _plain_text(content)


def _word_count(block: dict[str, Any]) -> int:
    """Count visible prose words without treating markup as content."""

    return len(_WORD_RE.findall(_plain_text(block)))


def _normalized_text_length(value: object) -> int:
    """Return visible character length after collapsing source whitespace."""

    return len(" ".join(_plain_text(value).split()))


def _inline_code_character_count(value: object) -> int:
    """Count visible monospace characters inside a Pandoc fragment."""

    if isinstance(value, list):
        return sum(_inline_code_character_count(item) for item in value)
    if not isinstance(value, dict):
        return 0
    content = value.get("c")
    if value.get("t") == "Code" and isinstance(content, list) and content:
        return len(str(content[-1]))
    return _inline_code_character_count(content)


def _estimated_visible_characters(value: object) -> int:
    """Return proportional-width units with a conservative monospace debit."""

    visible = _normalized_text_length(value)
    code_characters = _inline_code_character_count(value)
    # At the 20-point floor, the projected monospace face fits about 34
    # characters where the sans-serif body fits 43. Preserve inline code as an
    # atomic Pandoc node and debit only the extra width it consumes.
    monospace_extra = math.ceil(
        code_characters * (_BODY_CHARACTERS_PER_LINE_20PT / _LIST_CHARACTERS_PER_LINE_20PT - 1)
    )
    return visible + monospace_extra


def _compact_continuation_title(title: str, continuation: int) -> str:
    """Return a bounded visible title while retaining the full first-frame title."""

    compact = title
    punctuation_prefix = re.split(r":|\s+[—–]\s+", title, maxsplit=1)[0].strip()
    if punctuation_prefix != title and 12 <= len(punctuation_prefix) <= _CONTINUATION_TITLE_TARGET_CHARS:
        compact = punctuation_prefix
    elif len(title) > _CONTINUATION_TITLE_TARGET_CHARS:
        words: list[str] = []
        for word in title.split():
            candidate = " ".join([*words, word])
            if words and len(candidate) > _CONTINUATION_TITLE_TARGET_CHARS - 1:
                break
            words.append(word)
        compact = " ".join(words).rstrip(".,;:") + "…"
    return f"{compact} (part {continuation})"


def _text_inlines(text: str) -> list[dict[str, Any]]:
    inlines: list[dict[str, Any]] = []
    for index, word in enumerate(text.split()):
        if index:
            inlines.append({"t": "Space"})
        inlines.append({"t": "Str", "c": word})
    return inlines


def _continuation_title_text(header: dict[str, Any], continuation: int) -> str:
    title = _header_text(header)
    return title if continuation == 1 else _compact_continuation_title(title, continuation)


def _frame_body_line_capacity(
    header: dict[str, Any],
    continuation: int,
    policy: AccessibleSlidePolicy,
) -> int:
    """Estimate safe body lines after the fixed title and footer regions."""

    title_chars_per_line = max(
        1,
        math.floor(_TITLE_CHARACTERS_PER_LINE_28PT * 28 / policy.title_font_pt),
    )
    title_lines = max(
        1,
        math.ceil(_normalized_text_length(_continuation_title_text(header, continuation)) / title_chars_per_line),
    )
    body_lines = math.floor(_BASE_BODY_LINES_16_9 * 20 / policy.body_font_pt)
    return max(1, body_lines - (title_lines - 1) * _BODY_LINES_PER_EXTRA_TITLE_LINE)


def _estimated_block_lines(block: dict[str, Any], policy: AccessibleSlidePolicy) -> int:
    """Estimate wrapped body lines without splitting a semantic block."""

    tag = block.get("t")
    body_chars_per_line = max(
        1,
        math.floor(_BODY_CHARACTERS_PER_LINE_20PT * 20 / policy.body_font_pt),
    )
    if tag in {"BulletList", "OrderedList"}:
        raw_items = block.get("c")
        if tag == "OrderedList" and isinstance(raw_items, list) and len(raw_items) == 2:
            raw_items = raw_items[1]
        if not isinstance(raw_items, list):
            return 1
        list_chars_per_line = max(
            1,
            math.floor(_LIST_CHARACTERS_PER_LINE_20PT * 20 / policy.body_font_pt),
        )
        return sum(
            max(1, math.ceil(_estimated_visible_characters(item) / list_chars_per_line))
            for item in raw_items
        )
    return max(1, math.ceil(_estimated_visible_characters(block) / body_chars_per_line))


def _trim_inline_spaces(inlines: list[Any]) -> list[Any]:
    """Drop boundary whitespace while preserving every semantic inline."""

    start = 0
    end = len(inlines)
    while start < end and isinstance(inlines[start], dict) and inlines[start].get("t") in {
        "Space",
        "SoftBreak",
        "LineBreak",
    }:
        start += 1
    while end > start and isinstance(inlines[end - 1], dict) and inlines[end - 1].get("t") in {
        "Space",
        "SoftBreak",
        "LineBreak",
    }:
        end -= 1
    return copy.deepcopy(inlines[start:end])


def _next_visible_str(inlines: list[Any], start: int) -> str | None:
    for inline in inlines[start:]:
        if not isinstance(inline, dict):
            continue
        if inline.get("t") in {"Space", "SoftBreak", "LineBreak"}:
            continue
        content = inline.get("c")
        if inline.get("t") == "Str" and isinstance(content, str):
            return content
        return None
    return None


def _is_semantic_inline_break(inlines: list[Any], index: int) -> bool:
    """Return whether an inline ends a sentence or strong written clause."""

    inline = inlines[index]
    if not isinstance(inline, dict) or inline.get("t") != "Str":
        return False
    content = inline.get("c")
    if not isinstance(content, str):
        return False
    stripped = content.rstrip()
    if stripped.endswith(_SEMANTIC_BREAK_SUFFIXES):
        return True
    # A comma is a written prosodic boundary and is therefore a permissible
    # last-resort split when a complete sentence cannot fit.  This never cuts
    # inside a Pandoc inline node.
    if stripped.endswith(","):
        return True
    return False


def _prose_block_slice(block: dict[str, Any], inlines: list[Any]) -> dict[str, Any]:
    updated = copy.deepcopy(block)
    updated["c"] = _trim_inline_spaces(inlines)
    return updated


def _split_prose_block_to_fit(
    block: dict[str, Any],
    *,
    policy: AccessibleSlidePolicy,
    maximum_lines: int,
    source: str,
    heading: str,
) -> list[dict[str, Any]]:
    """Split a paragraph only at sentence or strong-clause boundaries.

    Lists, code, equations, figures, and tables never enter this helper.  A
    paragraph with no safe written boundary fails closed instead of being cut
    by character count or rendered with smaller type.
    """

    words = _word_count(block)
    lines = _estimated_block_lines(block, policy)
    if words <= policy.max_prose_words and lines <= maximum_lines:
        return [copy.deepcopy(block)]
    tag = block.get("t")
    if tag not in {"Para", "Plain"} or not isinstance(block.get("c"), list):
        # Lists and raw theorem-like environments remain indivisible. Reject
        # an oversized one before TeX instead of splitting inside its semantic
        # structure or silently shrinking the profile's typography.
        requires_line_preflight = tag in {"BulletList", "OrderedList"}
        if words <= policy.max_prose_words and (not requires_line_preflight or lines <= maximum_lines):
            return [copy.deepcopy(block)]
        if tag in {"BulletList", "OrderedList"}:
            code = "slides.density.indivisible-list"
            noun = "list"
        elif tag == "RawBlock":
            code = "slides.density.indivisible-raw-block"
            noun = "raw theorem-like block"
        else:
            code = "slides.density.indivisible-prose"
            noun = "semantic prose block"
        raise _density_error(
            code,
            f"one {noun} cannot fit the projection frame without splitting inside its structure",
            source=source,
            heading=heading,
            block_type=str(tag),
            observed_words=words,
            maximum_words=policy.max_prose_words,
            estimated_lines=lines,
            maximum_lines=maximum_lines,
        )

    inlines = block["c"]
    segments: list[dict[str, Any]] = []
    start = 0
    while start < len(inlines):
        remainder = _prose_block_slice(block, inlines[start:])
        if (
            _word_count(remainder) <= policy.max_prose_words
            and _estimated_block_lines(remainder, policy) <= maximum_lines
        ):
            segments.append(remainder)
            break

        candidates: list[int] = []
        coordinator_candidates: list[int] = []
        for index in range(start, len(inlines)):
            written_boundary = _is_semantic_inline_break(inlines, index)
            next_word = _next_visible_str(inlines, index + 1)
            coordinator_boundary = (
                isinstance(inlines[index], dict)
                and inlines[index].get("t") == "Str"
                and next_word is not None
                and next_word.casefold().strip("'\"") in _CLAUSE_COORDINATORS
            )
            if not written_boundary and not coordinator_boundary:
                continue
            candidate = _prose_block_slice(block, inlines[start : index + 1])
            if (
                _word_count(candidate) <= policy.max_prose_words
                and _estimated_block_lines(candidate, policy) <= maximum_lines
            ):
                target = candidates if written_boundary else coordinator_candidates
                target.append(index + 1)
        usable_candidates = candidates or coordinator_candidates
        if not usable_candidates:
            raise _density_error(
                "slides.density.indivisible-prose",
                "one prose sentence or strong clause cannot fit the projection frame at the declared font floor",
                source=source,
                heading=heading,
                observed_words=_word_count(remainder),
                maximum_words=policy.max_prose_words,
                estimated_lines=_estimated_block_lines(remainder, policy),
                maximum_lines=maximum_lines,
                text_excerpt=" ".join(_plain_text(remainder).split())[:240],
            )
        cut = usable_candidates[-1]
        segments.append(_prose_block_slice(block, inlines[start:cut]))
        start = cut

    return [segment for segment in segments if segment.get("c")]


def _header_parts(block: dict[str, Any]) -> tuple[int, list[Any], list[dict[str, Any]]]:
    content = block.get("c")
    if block.get("t") != "Header" or not isinstance(content, list) or len(content) != 3:
        raise RenderingError("Accessible slide composition received a malformed Pandoc Header")
    level, attributes, inlines = content
    if not isinstance(level, int) or not isinstance(attributes, list) or not isinstance(inlines, list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Header")
    return level, attributes, inlines


def _header_text(block: dict[str, Any]) -> str:
    return " ".join(_plain_text(_header_parts(block)[2]).split()) or "Untitled slide"


def _header_with(
    source: dict[str, Any],
    *,
    level: int,
    continuation: int = 1,
    frame_kind: str | None = None,
    section_divider: bool = False,
) -> dict[str, Any]:
    """Return a frame-producing header without duplicating source identifiers."""

    _old_level, attributes, inlines = _header_parts(source)
    identifier = attributes[0] if continuation == 1 else ""
    classes = [str(value) for value in attributes[1]] if len(attributes) > 1 else []
    key_values = copy.deepcopy(attributes[2]) if len(attributes) > 2 else []
    if frame_kind and frame_kind not in classes:
        classes.append(frame_kind)
    if section_divider and "section-divider" not in classes:
        classes.append("section-divider")
    rendered_inlines = copy.deepcopy(inlines)
    if continuation > 1:
        full_title = " ".join(_plain_text(inlines).split()) or "Untitled slide"
        rendered_inlines = _text_inlines(_compact_continuation_title(full_title, continuation))
        key_values = [
            pair
            for pair in key_values
            if not (isinstance(pair, list) and pair and str(pair[0]).casefold() == "aria-label")
        ]
        key_values.append(["aria-label", f"{full_title}, part {continuation}"])
    return {"t": "Header", "c": [level, [identifier, classes, key_values], rendered_inlines]}


def _generated_header(title: str) -> dict[str, Any]:
    return {"t": "Header", "c": [2, ["", ["generated-slide-title"], []], _text_inlines(title)]}


def _block_contains(block: object, target: str) -> bool:
    if isinstance(block, dict):
        if block.get("t") == target:
            return True
        return _block_contains(block.get("c"), target)
    if isinstance(block, list):
        return any(_block_contains(item, target) for item in block)
    return False


def _is_presentation_page_break(block: dict[str, Any]) -> bool:
    """Return whether a raw pagination command has no slide content."""

    if block.get("t") != "RawBlock":
        return False
    content = block.get("c")
    return (
        isinstance(content, list)
        and len(content) == 2
        and str(content[0]).casefold() in {"latex", "tex"}
        and isinstance(content[1], str)
        and _PRESENTATION_PAGE_BREAK_RE.fullmatch(content[1].strip()) is not None
    )


def _is_display_equation_paragraph(block: dict[str, Any]) -> bool:
    """Recognize display math with an optional source-owned crossref suffix."""

    if block.get("t") not in {"Para", "Plain"} or not isinstance(block.get("c"), list):
        return False
    saw_display_math = False
    for inline in block["c"]:
        if not isinstance(inline, dict):
            return False
        tag = inline.get("t")
        if tag in {"Space", "SoftBreak", "LineBreak"}:
            continue
        if tag == "Math":
            content = inline.get("c")
            if (
                not isinstance(content, list)
                or len(content) != 2
                or not isinstance(content[0], dict)
                or content[0].get("t") != "DisplayMath"
            ):
                return False
            saw_display_math = True
            continue
        if tag == "Str" and isinstance(inline.get("c"), str) and _EQUATION_LABEL_RE.fullmatch(inline["c"]):
            continue
        return False
    return saw_display_math


def _block_kind(block: dict[str, Any]) -> str:
    tag = block.get("t")
    if tag == "Figure" or _block_contains(block, "Image"):
        return "figure-led"
    if tag == "Table":
        return "table-led"
    if tag in {"CodeBlock"}:
        return "code-led"
    if tag == "BlockQuote":
        return "evidence-slide"
    if tag == "Div":
        content = block.get("c")
        if isinstance(content, list) and content and isinstance(content[0], list):
            classes = content[0][1] if len(content[0]) > 1 else []
            if any(str(value) in {"evidence", "claim", "finding"} for value in classes):
                return "evidence-slide"
    if _is_display_equation_paragraph(block):
        return "equation-led"
    if tag == "RawBlock" and re.search(
        r"\\begin\{(?:equation\*?|align\*?|gather\*?|multline\*?)\}|^\s*\$\$",
        _plain_text(block),
    ):
        return "equation-led"
    return "prose-slide"


def _reader_link_block(policy: AccessibleSlidePolicy, noun: str) -> dict[str, Any]:
    label = f"Open the canonical HTML manuscript for the complete {noun}."
    inlines: list[dict[str, Any]] = []
    for index, word in enumerate(label.split()):
        if index:
            inlines.append({"t": "Space"})
        inlines.append({"t": "Str", "c": word})
    return {
        "t": "Para",
        "c": [
            {
                "t": "Link",
                "c": [["", ["slide-reader-link"], []], inlines, [policy.reader_href, "Canonical HTML manuscript"]],
            }
        ],
    }


def _allocate_figure_area(value: object, image_height_percent: int) -> None:
    """Reserve figure area while retaining space for its accessible label.

    The surrounding ``Figure`` block is the measured allocation. Fifteen
    percentage points are reserved for the 16-point companion-reader label and
    Beamer's figure/caption glue; the image occupies the title-adjusted
    remainder. This keeps the complete figure region at the configured floor
    without measuring against the global text height.
    """

    if isinstance(value, list):
        for item in value:
            _allocate_figure_area(item, image_height_percent)
        return
    if not isinstance(value, dict):
        return
    if value.get("t") == "Image":
        content = value.get("c")
        if not isinstance(content, list) or len(content) != 3 or not isinstance(content[0], list):
            raise RenderingError("Accessible slide composition received a malformed Pandoc Image")
        attributes = content[0]
        if len(attributes) != 3 or not isinstance(attributes[2], list):
            raise RenderingError("Accessible slide composition received malformed Pandoc Image attributes")
        key_values = [pair for pair in attributes[2] if not (isinstance(pair, list) and pair and pair[0] == "height")]
        key_values.append(["height", f"{image_height_percent}%"])
        attributes[2] = key_values
    _allocate_figure_area(value.get("c"), image_height_percent)


def _shorten_figure_caption(
    block: dict[str, Any],
    policy: AccessibleSlidePolicy,
    *,
    image_height_percent: int,
) -> dict[str, Any]:
    updated = copy.deepcopy(block)
    if updated.get("t") != "Figure":
        return updated
    content = updated.get("c")
    if not isinstance(content, list) or len(content) != 3:
        raise RenderingError("Accessible slide composition received a malformed Pandoc Figure")
    _allocate_figure_area(updated, image_height_percent)
    reader_link = _reader_link_block(policy, "caption, long description, and exact values")
    content[1] = [None, [{"t": "Plain", "c": reader_link["c"]}]]
    return updated


def _table_row_count(block: dict[str, Any]) -> int:
    content = block.get("c")
    if not isinstance(content, list) or len(content) < 5 or not isinstance(content[4], list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Table")
    total = 0
    for body in content[4]:
        if isinstance(body, list) and len(body) >= 4 and isinstance(body[3], list):
            total += len(body[3])
    return total


def _table_row_cells(row: object) -> list[Any]:
    """Return validated cells from one Pandoc table row."""

    if not isinstance(row, list) or len(row) != 2 or not isinstance(row[1], list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Table row")
    return row[1]


def _table_cell_parts(cell: object) -> tuple[int, int, list[Any]]:
    """Return row span, column span, and blocks from one Pandoc table cell."""

    if not isinstance(cell, list) or len(cell) != 5 or not isinstance(cell[4], list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Table cell")
    row_span = cell[2]
    column_span = cell[3]
    if (
        isinstance(row_span, bool)
        or not isinstance(row_span, int)
        or row_span < 1
        or isinstance(column_span, bool)
        or not isinstance(column_span, int)
        or column_span < 1
    ):
        raise RenderingError("Accessible slide composition received invalid Pandoc Table cell spans")
    return row_span, column_span, cell[4]


def _table_rows(content: list[Any]) -> tuple[list[Any], list[Any], list[Any]]:
    """Return global header, body, and footer rows from a validated table."""

    if len(content) != 6 or not isinstance(content[3], list) or not isinstance(content[4], list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Table")
    table_head = content[3]
    table_foot = content[5]
    if len(table_head) != 2 or not isinstance(table_head[1], list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Table head")
    if not isinstance(table_foot, list) or len(table_foot) != 2 or not isinstance(table_foot[1], list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Table foot")
    body_rows: list[Any] = []
    for body in content[4]:
        if (
            not isinstance(body, list)
            or len(body) != 4
            or not isinstance(body[2], list)
            or not isinstance(body[3], list)
        ):
            raise RenderingError("Accessible slide composition received a malformed Pandoc Table body")
        body_rows.extend(body[2])
        body_rows.extend(body[3])
    return table_head[1], body_rows, table_foot[1]


def _table_cell_demand(blocks: list[Any]) -> float:
    """Return a bounded relative width demand for one table cell."""

    text = " ".join(_plain_text(blocks).split())
    if not text:
        return float(_TABLE_MINIMUM_COLUMN_CHARACTERS)
    longest_token = max(len(token) for token in text.split())
    # Longest-token width prevents compact identifiers from being assigned a
    # column that cannot display them; the square-root term gives explanatory
    # cells more room without allowing one paragraph to consume the frame.
    return float(
        max(
            _TABLE_MINIMUM_COLUMN_CHARACTERS,
            longest_token,
            min(32, math.ceil(math.sqrt(len(text)) * 2.5)),
        )
    )


def _table_column_widths(content: list[Any]) -> list[float]:
    """Resolve source widths and content demand into normalized slide widths."""

    colspecs = content[2]
    if not isinstance(colspecs, list) or not colspecs:
        raise RenderingError("Accessible slide composition requires at least one Pandoc Table column")
    column_count = len(colspecs)
    explicit: list[float | None] = []
    for colspec in colspecs:
        if not isinstance(colspec, list) or len(colspec) != 2 or not isinstance(colspec[1], dict):
            raise RenderingError("Accessible slide composition received malformed Pandoc Table column specs")
        width_spec = colspec[1]
        if width_spec.get("t") == "ColWidthDefault":
            explicit.append(None)
            continue
        if width_spec.get("t") != "ColWidth" or isinstance(width_spec.get("c"), bool):
            raise RenderingError("Accessible slide composition received malformed Pandoc Table column width")
        try:
            numeric_width = float(width_spec["c"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RenderingError("Accessible slide composition received malformed Pandoc Table column width") from exc
        if not math.isfinite(numeric_width) or numeric_width <= 0:
            raise RenderingError("Accessible slide composition received non-positive Pandoc Table column width")
        explicit.append(numeric_width)

    demand = [float(_TABLE_MINIMUM_COLUMN_CHARACTERS) for _ in range(column_count)]
    head_rows, body_rows, foot_rows = _table_rows(content)
    for row in [*head_rows, *body_rows, *foot_rows]:
        column_index = 0
        for cell in _table_row_cells(row):
            _row_span, column_span, blocks = _table_cell_parts(cell)
            if column_index + column_span > column_count:
                raise RenderingError("Accessible slide composition received a Table row wider than its column specs")
            per_column_demand = _table_cell_demand(blocks) / column_span
            for index in range(column_index, column_index + column_span):
                demand[index] = max(demand[index], per_column_demand)
            column_index += column_span

    if all(width is None for width in explicit):
        weights = demand
    else:
        explicit_total = sum(width for width in explicit if width is not None)
        default_indices = [index for index, width in enumerate(explicit) if width is None]
        if not default_indices:
            weights = [float(width) for width in explicit if width is not None]
        else:
            # Respect declared source proportions and allocate the remaining
            # width among default columns by measured content demand. If the
            # declared columns already consume the canvas, retain a small
            # positive share for defaults and normalize the complete vector.
            default_total = sum(demand[index] for index in default_indices)
            remaining_fraction = max(0.05 * len(default_indices), 1.0 - explicit_total)
            weights = []
            for index, resolved_width in enumerate(explicit):
                if resolved_width is not None:
                    weights.append(resolved_width)
                else:
                    weights.append(remaining_fraction * demand[index] / default_total)

    total = sum(weights)
    if not math.isfinite(total) or total <= 0:
        raise RenderingError("Accessible slide composition could not resolve Pandoc Table column widths")
    normalized = [weight / total for weight in weights]
    # Give Pandoc explicit widths so the rendered table wraps according to the
    # same geometry the accessible composer validated. Archive rendering never
    # enters this opt-in transformation.
    rounded = [round(width, 6) for width in normalized[:-1]]
    rounded.append(round(1.0 - sum(rounded), 6))
    if rounded[-1] <= 0:
        rounded = normalized
    for colspec, resolved_width in zip(colspecs, rounded, strict=True):
        colspec[1] = {"t": "ColWidth", "c": resolved_width}
    return rounded


def _table_column_character_capacities(widths: list[float], policy: AccessibleSlidePolicy) -> list[int]:
    """Allocate conservative visible-character capacities across columns."""

    column_count = len(widths)
    total = max(
        column_count,
        math.floor(_BODY_CHARACTERS_PER_LINE_20PT * 20 / policy.body_font_pt)
        - _TABLE_INTERCOLUMN_GUTTER_CHARACTERS * column_count,
    )
    minimum = _TABLE_MINIMUM_COLUMN_CHARACTERS if total >= _TABLE_MINIMUM_COLUMN_CHARACTERS * column_count else 1
    remaining = total - minimum * column_count
    raw_extra = [remaining * width for width in widths]
    capacities = [minimum + math.floor(value) for value in raw_extra]
    undistributed = total - sum(capacities)
    order = sorted(range(column_count), key=lambda index: (raw_extra[index] % 1, -index), reverse=True)
    for index in order[:undistributed]:
        capacities[index] += 1
    return capacities


def _wrapped_text_lines(text: str, capacity: int) -> int:
    """Estimate line count using deterministic word wrapping."""

    words = text.split()
    if not words:
        return 1
    lines = 1
    used = 0
    for word in words:
        word_length = len(word)
        if used and used + 1 + word_length <= capacity:
            used += 1 + word_length
            continue
        if used:
            lines += 1
        whole_lines, remainder = divmod(word_length, capacity)
        if whole_lines:
            lines += whole_lines - int(remainder == 0)
        used = remainder or min(word_length, capacity)
    return lines


def _table_cell_lines(blocks: list[Any], capacity: int) -> int:
    """Estimate the vertical line cost of one table cell."""

    if not blocks:
        return 1
    lines = 0
    for block in blocks:
        text = " ".join(_plain_text(block).split())
        lines += _wrapped_text_lines(text, capacity)
    return max(1, lines)


def _table_row_lines(row: Any, capacities: list[int]) -> int:
    """Return the wrapped height of one row in body-line units."""

    column_count = len(capacities)
    column_index = 0
    lines = 1
    for cell in _table_row_cells(row):
        row_span, column_span, blocks = _table_cell_parts(cell)
        if column_index + column_span > column_count:
            raise RenderingError("Accessible slide composition received a Table row wider than its column specs")
        capacity = sum(capacities[column_index : column_index + column_span])
        capacity += _TABLE_INTERCOLUMN_GUTTER_CHARACTERS * (column_span - 1)
        cell_lines = math.ceil(_table_cell_lines(blocks, max(1, capacity)) / row_span)
        lines = max(lines, cell_lines)
        column_index += column_span
    return lines


def _table_rows_lines(rows: list[Any], capacities: list[int]) -> int:
    return sum(_table_row_lines(row, capacities) for row in rows)


def _table_reader_link_lines(policy: AccessibleSlidePolicy) -> int:
    label = _plain_text(_reader_link_block(policy, "table and caption"))
    capacity = max(1, math.floor(_BODY_CHARACTERS_PER_LINE_20PT * 20 / policy.body_font_pt))
    return _wrapped_text_lines(" ".join(label.split()), capacity)


def _table_reader_fallback(
    block: dict[str, Any],
    policy: AccessibleSlidePolicy,
    *,
    column_count: int,
    row_count: int,
    available_lines: int,
    fixed_lines: int,
    header_lines: int,
    first_row_lines: int,
) -> dict[str, Any]:
    """Return an explicit reader-only projection when no whole row fits.

    The complete table is not shrunk, split, or silently dropped. It remains
    in the canonical HTML manuscript; the projected frame names the geometry
    decision and links to that complete reader surface.
    """

    content = block.get("c")
    attributes = copy.deepcopy(content[0]) if isinstance(content, list) and content else ["", [], []]
    if not isinstance(attributes, list) or len(attributes) != 3:
        attributes = ["", [], []]
    classes = attributes[1] if isinstance(attributes[1], list) else []
    key_values = attributes[2] if isinstance(attributes[2], list) else []
    if "table-reader-fallback" not in classes:
        classes.append("table-reader-fallback")
    key_values = [
        pair
        for pair in key_values
        if not (
            isinstance(pair, list)
            and pair
            and str(pair[0]).casefold()
            in {
                "data-diagnostic-code",
                "data-columns",
                "data-body-rows",
                "data-available-lines",
                "data-fixed-lines",
                "data-header-lines",
                "data-first-row-lines",
            }
        )
    ]
    key_values.extend(
        [
            ["data-diagnostic-code", "slides.density.table-reader-fallback"],
            ["data-columns", str(column_count)],
            ["data-body-rows", str(row_count)],
            ["data-available-lines", str(available_lines)],
            ["data-fixed-lines", str(fixed_lines)],
            ["data-header-lines", str(header_lines)],
            ["data-first-row-lines", str(first_row_lines)],
        ]
    )
    attributes[1] = classes
    attributes[2] = key_values
    prefix = _text_inlines(
        f"Projection-safe table summary: {column_count} columns and {row_count} body rows exceed the complete "
        "20-point frame geometry."
    )
    link = _reader_link_block(policy, "table, caption, and exact values")["c"]
    return {
        "t": "Div",
        "c": [
            attributes,
            [
                {
                    "t": "Para",
                    "c": [*prefix, {"t": "Space"}, *copy.deepcopy(link)],
                }
            ],
        ],
    }


def _excerpt_table(
    block: dict[str, Any],
    policy: AccessibleSlidePolicy,
    *,
    header: dict[str, Any],
    continuation: int,
) -> tuple[dict[str, Any], bool]:
    """Create a row-bounded table excerpt that fits accessible 16:9 geometry."""

    updated = copy.deepcopy(block)
    content = updated.get("c")
    if not isinstance(content, list) or len(content) != 6 or not isinstance(content[4], list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Table")
    widths = _table_column_widths(content)
    capacities = _table_column_character_capacities(widths, policy)
    head_rows, _all_body_rows, foot_rows = _table_rows(content)
    maximum_lines = _frame_body_line_capacity(header, continuation, policy)
    link_lines = _table_reader_link_lines(policy)
    fixed_lines = _TABLE_RULE_PADDING_LINES + link_lines
    global_header_lines = _table_rows_lines(head_rows, capacities)
    footer_lines = _table_rows_lines(foot_rows, capacities)
    consumed_lines = fixed_lines + global_header_lines + footer_lines
    remaining_rows = policy.max_table_rows
    kept_rows = 0
    original_rows = _table_row_count(block)
    excerpted = False
    saw_first_body_row = False
    stop_excerpt = False

    for body in content[4]:
        body_head_rows = body[2]
        rows = body[3]
        kept_in_body: list[Any] = []
        body_head_lines = _table_rows_lines(body_head_rows, capacities)
        if not stop_excerpt:
            for row in rows:
                row_lines = _table_row_lines(row, capacities)
                proposed = consumed_lines + row_lines + (body_head_lines if not kept_in_body else 0)
                if remaining_rows <= 0 or proposed > maximum_lines:
                    excerpted = True
                    stop_excerpt = True
                    break
                consumed_lines = proposed
                kept_in_body.append(row)
                kept_rows += 1
                remaining_rows -= 1
                saw_first_body_row = True
        if len(kept_in_body) < len(rows):
            excerpted = True
        body[3] = kept_in_body
        if not kept_in_body:
            # A body header with no visible body row has no projected meaning.
            body[2] = []

    if original_rows and not saw_first_body_row:
        first_row: Any | None = None
        first_body_head_lines = 0
        for body in block["c"][4]:
            if body[3]:
                first_row = body[3][0]
                first_body_head_lines = _table_rows_lines(body[2], capacities)
                break
        first_row_lines = _table_row_lines(first_row, capacities) if first_row is not None else 0
        return (
            _table_reader_fallback(
                block,
                policy,
                column_count=len(widths),
                row_count=original_rows,
                available_lines=maximum_lines,
                fixed_lines=fixed_lines,
                header_lines=global_header_lines + first_body_head_lines,
                first_row_lines=first_row_lines,
            ),
            True,
        )
    if not original_rows and consumed_lines > maximum_lines:
        return (
            _table_reader_fallback(
                block,
                policy,
                column_count=len(widths),
                row_count=0,
                available_lines=maximum_lines,
                fixed_lines=fixed_lines,
                header_lines=global_header_lines,
                first_row_lines=0,
            ),
            True,
        )
    excerpted = excerpted or kept_rows < original_rows or original_rows > policy.max_table_rows
    # The full source caption and every omitted row remain in the canonical
    # reader. The short contextual link preserves the table identifier and
    # cross-reference target without squeezing the complete table onto a frame.
    content[1] = [None, [{"t": "Plain", "c": _reader_link_block(policy, "table and caption")["c"]}]]
    return updated, excerpted


def _flush_prose_frames(
    frames: list[_Frame],
    title: dict[str, Any],
    pending: list[dict[str, Any]],
    *,
    continuation: int,
) -> int:
    if not pending:
        return continuation
    frames.append(_Frame(title=title, blocks=tuple(pending), kind="prose-slide", continuation=continuation))
    pending.clear()
    return continuation + 1


def _compose_segment(
    header: dict[str, Any],
    blocks: list[dict[str, Any]],
    *,
    policy: AccessibleSlidePolicy,
    source: str,
) -> tuple[list[_Frame], int]:
    frames: list[_Frame] = []
    pending: list[dict[str, Any]] = []
    pending_words = 0
    pending_lines = 0
    continuation = 1
    excerpted_tables = 0
    heading = _header_text(header)

    # A title that consumes three or more projected lines leaves at most four
    # body lines.  Preserve that full title as an explicit divider, then use
    # the bounded, fully aria-labelled continuation title for content frames.
    # This avoids either shrinking the title or forcing one clause into an
    # unsafely shallow first frame.
    if blocks and _frame_body_line_capacity(header, continuation, policy) <= 4:
        frames.append(
            _Frame(
                title=header,
                blocks=(),
                kind="section-divider",
                continuation=continuation,
            )
        )
        continuation += 1

    for block in blocks:
        if block.get("t") == "HorizontalRule" or _is_presentation_page_break(block):
            continuation = _flush_prose_frames(
                frames,
                header,
                pending,
                continuation=continuation,
            )
            pending_words = 0
            pending_lines = 0
            continue

        kind = _block_kind(block)
        words = _word_count(block)
        if kind == "prose-slide":
            queue = [copy.deepcopy(block)]
            while queue:
                maximum_lines = _frame_body_line_capacity(header, continuation, policy)
                current = queue.pop(0)
                split_blocks = _split_prose_block_to_fit(
                    current,
                    policy=policy,
                    maximum_lines=maximum_lines,
                    source=source,
                    heading=heading,
                )
                if len(split_blocks) > 1:
                    queue = split_blocks + queue
                    continue
                current = split_blocks[0]
                current_words = _word_count(current)
                current_lines = _estimated_block_lines(current, policy)
                combined_lines = pending_lines + (1 if pending else 0) + current_lines
                if pending and (
                    pending_words + current_words > policy.max_prose_words
                    or combined_lines > maximum_lines
                ):
                    continuation = _flush_prose_frames(
                        frames,
                        header,
                        pending,
                        continuation=continuation,
                    )
                    pending_words = 0
                    pending_lines = 0
                    queue.insert(0, current)
                    continue
                pending.append(current)
                pending_words += current_words
                pending_lines = combined_lines
            continue

        continuation = _flush_prose_frames(
            frames,
            header,
            pending,
            continuation=continuation,
        )
        pending_words = 0
        pending_lines = 0
        isolated_blocks: list[dict[str, Any]]
        if kind == "figure-led":
            maximum_lines = _frame_body_line_capacity(header, continuation, policy)
            base_lines = max(1, math.floor(_BASE_BODY_LINES_16_9 * 20 / policy.body_font_pt))
            # Fifteen percentage points of the declared figure-led region are
            # reserved for the 16/19-point reader link and Beamer figure glue.
            # Scale the image against the title-adjusted usable body, never
            # against the global text height.
            image_height_percent = max(
                1,
                math.floor(maximum_lines / base_lines * (policy.min_figure_area_percent - 15)),
            )
            isolated_blocks = [
                _shorten_figure_caption(
                    block,
                    policy,
                    image_height_percent=image_height_percent,
                )
            ]
        elif kind == "table-led":
            table, excerpted = _excerpt_table(
                block,
                policy,
                header=header,
                continuation=continuation,
            )
            excerpted_tables += int(excerpted)
            isolated_blocks = [table]
        else:
            maximum_lines = _frame_body_line_capacity(header, continuation, policy)
            if kind == "evidence-slide" and (
                words > policy.max_prose_words or _estimated_block_lines(block, policy) > maximum_lines
            ):
                raise _density_error(
                    "slides.density.indivisible-evidence",
                    "one evidence block cannot fit the projection frame at the declared font floor",
                    source=source,
                    heading=heading,
                    observed_words=words,
                    maximum_words=policy.max_prose_words,
                    estimated_lines=_estimated_block_lines(block, policy),
                    maximum_lines=maximum_lines,
                )
            isolated_blocks = [copy.deepcopy(block)]
        frames.append(
            _Frame(
                title=header,
                blocks=tuple(isolated_blocks),
                kind=kind,
                continuation=continuation,
            )
        )
        continuation += 1

    _flush_prose_frames(frames, header, pending, continuation=continuation)
    return frames, excerpted_tables


def compose_accessible_pandoc_document(
    document: dict[str, Any],
    *,
    policy: AccessibleSlidePolicy,
    source: str,
) -> AccessibleSlideComposition:
    """Compose one Pandoc JSON document into bounded semantic slide frames."""

    if not isinstance(document, dict) or not isinstance(document.get("blocks"), list):
        raise RenderingError(
            "Accessible slide composition requires a Pandoc JSON document",
            context={"source": source, "diagnostic_code": "slides.schema.pandoc-json"},
        )
    original_blocks = document["blocks"]
    segments: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    current_header: dict[str, Any] | None = None
    current_blocks: list[dict[str, Any]] = []

    def flush_segment() -> None:
        nonlocal current_header, current_blocks
        if current_header is None and not current_blocks:
            return
        segments.append((current_header or _generated_header("Overview"), current_blocks))
        current_header = None
        current_blocks = []

    for raw in original_blocks:
        if not isinstance(raw, dict) or not isinstance(raw.get("t"), str):
            raise RenderingError(
                "Accessible slide composition received a malformed Pandoc block",
                context={"source": source, "diagnostic_code": "slides.schema.pandoc-block"},
            )
        if raw.get("t") == "Header":
            flush_segment()
            current_header = raw
        else:
            current_blocks.append(raw)
    flush_segment()

    output_blocks: list[dict[str, Any]] = []
    frame_count = 0
    section_dividers = 0
    excerpted_tables = 0
    figure_frames = 0
    for index, (header, blocks) in enumerate(segments):
        level, attributes, _inlines = _header_parts(header)
        classes = {str(value) for value in (attributes[1] if len(attributes) > 1 else [])}
        next_level = _header_parts(segments[index + 1][0])[0] if index + 1 < len(segments) else None
        explicit_divider = (
            level == 1 or "section-divider" in classes or (not blocks and next_level is not None and next_level > level)
        )
        if not blocks:
            if not explicit_divider:
                raise _density_error(
                    "slides.structure.title-only",
                    "a title-only frame is not an explicit section divider",
                    source=source,
                    heading=_header_text(header),
                )
            output_blocks.append(_header_with(header, level=1, section_divider=True))
            section_dividers += 1
            frame_count += 1
            continue

        if level == 1:
            output_blocks.append(_header_with(header, level=1, section_divider=True))
            section_dividers += 1
            frame_count += 1
            content_header = _header_with(header, level=2, continuation=2, frame_kind="section-overview")
            # The section header already owns the source identifier.  The
            # overview frame is a continuation and therefore intentionally has
            # no duplicate identifier.
            content_header["c"][2] = copy.deepcopy(_header_parts(header)[2])
        else:
            content_header = _header_with(header, level=2)

        frames, excerpted = _compose_segment(content_header, blocks, policy=policy, source=source)
        excerpted_tables += excerpted
        for frame in frames:
            output_blocks.append(
                _header_with(
                    frame.title,
                    level=2,
                    continuation=frame.continuation,
                    frame_kind=frame.kind,
                )
            )
            output_blocks.extend(copy.deepcopy(frame.blocks))
            frame_count += 1
            section_dividers += int(frame.kind == "section-divider")
            figure_frames += int(frame.kind == "figure-led")

    updated = copy.deepcopy(document)
    updated["blocks"] = output_blocks
    return AccessibleSlideComposition(
        document=updated,
        frame_count=frame_count,
        section_divider_count=section_dividers,
        excerpted_table_count=excerpted_tables,
        figure_frame_count=figure_frames,
    )


def load_and_compose_pandoc_json(
    path: Path,
    *,
    policy: AccessibleSlidePolicy,
    source: str,
) -> AccessibleSlideComposition:
    """Load a Pandoc JSON file and compose it through the accessible policy."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RenderingError(
            f"Could not read Pandoc JSON for accessible slides: {exc}",
            context={"source": source, "diagnostic_code": "slides.schema.pandoc-json"},
        ) from exc
    return compose_accessible_pandoc_document(payload, policy=policy, source=source)


def _set_html_attribute(tag: str, name: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    pattern = re.compile(
        rf"(?<!\S){re.escape(name)}\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)",
        flags=re.IGNORECASE,
    )
    if pattern.search(tag):
        return pattern.sub(lambda _match: f'{name}="{escaped}"', tag, count=1)
    return tag[:-1].rstrip() + f' {name}="{escaped}">' if tag.endswith(">") else tag


def _reveal_semantics(content: str) -> str:
    """Name every Reveal slide from its first heading and add slide roles."""

    def replace(match: re.Match[str]) -> str:
        heading_tag = match.group("heading")
        identifier_match = re.search(
            r'(?<!\S)id\s*=\s*["\'](?P<id>[^"\']+)',
            match.group("heading_attrs"),
        )
        if identifier_match is None:
            heading_text = html.unescape(_TAG_RE.sub("", heading_tag)).strip()
            heading_id = "slide-heading-" + hashlib.sha256(heading_text.encode("utf-8")).hexdigest()[:12]
            updated_heading = _set_html_attribute(heading_tag, "id", heading_id)
        else:
            heading_id = identifier_match.group("id")
            updated_heading = heading_tag
        open_tag = _set_html_attribute(match.group("open"), "role", "group")
        open_tag = _set_html_attribute(open_tag, "aria-roledescription", "slide")
        open_tag = _set_html_attribute(open_tag, "aria-labelledby", heading_id)
        return f"{open_tag}{match.group('spacing')}{updated_heading}"

    updated = _SLIDE_OPEN_RE.sub(replace, content)
    unnamed_slide = re.search(
        r"<section\b(?=[^>]*(?<!\S)class\s*=\s*[\"'][^\"']*\bslide\b)[^>]*>"
        r"(?!\s*<h[1-6]\b)",
        updated,
        flags=re.IGNORECASE,
    )
    if unnamed_slide is not None:
        raise RenderingError(
            "[slides.structure.heading] Reveal slide has no semantic heading",
            context={"diagnostic_code": "slides.structure.heading"},
        )
    return updated


def _accessible_reveal_css(policy: AccessibleSlidePolicy) -> str:
    body_px = policy.body_font_pt * (4 / 3)
    title_px = policy.title_font_pt * (4 / 3)
    label_px = policy.figure_label_font_pt * (4 / 3)
    return f"""<style data-template-accessible-slides>
:root {{ --r-background-color: #ffffff; --r-main-color: #111111; --r-link-color: #004b87; }}
html, body {{ max-width: 100%; overflow-x: hidden; }}
.reveal {{ color: #111111; background: #ffffff; font-size: {body_px:.2f}px; }}
.reveal .slides section {{
  max-width: 100%; min-width: 0; overflow-wrap: anywhere;
  text-align: left; line-height: 1.35;
}}
.reveal h1, .reveal h2, .reveal h3 {{ color: #111111; font-size: {title_px:.2f}px; line-height: 1.15; }}
.reveal a {{ color: #004b87; text-decoration: underline; text-decoration-thickness: 0.11em; }}
.reveal a:focus-visible, .reveal button:focus-visible {{ outline: 4px solid #b34d00; outline-offset: 4px; }}
.reveal .table-scroll {{
  max-width: 100%; overflow-x: auto;
  overscroll-behavior-inline: contain; scrollbar-gutter: stable;
}}
.reveal .table-scroll:focus-visible {{ outline: 4px solid #b34d00; outline-offset: 4px; }}
.reveal table {{ max-width: 100%; min-width: 100%; width: max-content; font-size: inherit; border-collapse: collapse; }}
.reveal th, .reveal td {{ border: 2px solid #404040; padding: 0.25em 0.4em; }}
.reveal section.figure-led figure {{
  min-height: {policy.min_figure_area_percent}vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}}
.reveal section.figure-led img {{
  display: block;
  width: 100% !important;
  height: calc({policy.min_figure_area_percent}vh - 5.5rem) !important;
  max-height: calc({policy.min_figure_area_percent}vh - 5.5rem);
  max-width: 100%;
  object-fit: contain;
  margin-inline: auto;
}}
.reveal figcaption, .reveal .slide-reader-link {{ font-size: {label_px:.2f}px; line-height: 1.3; }}
.slide-reader-nav {{
  position: fixed;
  inset-inline-end: 0.75rem;
  inset-block-start: 0.5rem;
  z-index: 30;
  background: #ffffff;
  border: 2px solid #111111;
  padding: 0.3rem 0.55rem;
}}
.skip-link {{
  position: fixed;
  inset-inline-start: 0.5rem;
  inset-block-start: -8rem;
  z-index: 100;
  background: #ffffff;
  color: #111111;
  border: 3px solid #111111;
  padding: 0.5rem;
}}
.skip-link:focus {{ inset-block-start: 0.5rem; }}
.figure-long-description {{
  font-size: {label_px:.2f}px; max-height: 35vh; max-width: 100%;
  overflow: auto; overflow-wrap: anywhere;
}}
.figure-exact-values {{ font-size: {label_px:.2f}px; max-width: 100%; overflow-wrap: anywhere; }}
@media (prefers-reduced-motion: reduce) {{ .reveal .slides section {{ transition: none !important; }} }}
@media (forced-colors: active) {{ .reveal th, .reveal td, .slide-reader-nav {{ border: 2px solid CanvasText; }} }}
</style>"""


def enhance_accessible_reveal(
    html_file: Path,
    *,
    policy: AccessibleSlidePolicy,
    registry_path: Path | None,
    language: str = "en",
) -> None:
    """Apply deterministic semantic, navigation, and visual-accessibility hooks."""

    # Reveal uses ``data-src`` for lazy loading while the shared publication
    # postprocessor intentionally matches ordinary HTML ``src`` attributes.
    # Accessible mode favors predictable native image semantics over lazy
    # loading and normalizes the attribute before applying the shared registry.
    initial = html_file.read_text(encoding="utf-8")
    initial = re.sub(r"(?<!\S)data-src\s*=", "src=", initial, flags=re.IGNORECASE)
    initial = normalize_figure_paths(initial)
    write_if_changed(html_file, initial)
    enhance_accessibility(html_file, language=language, registry_path=registry_path)
    content = html_file.read_text(encoding="utf-8")
    content = _reveal_semantics(content)
    if "data-template-accessible-slides" not in content:
        content = content.replace("</head>", _accessible_reveal_css(policy) + "\n</head>", 1)
    if '<nav class="slide-reader-nav"' not in content:
        reader_href = html.escape(policy.reader_href, quote=True)
        nav = (
            '<nav class="slide-reader-nav" aria-label="Presentation companion">'
            f'<a href="{reader_href}">Open canonical HTML manuscript</a></nav>'
        )
        content = re.sub(r"(<body\b[^>]*>)", rf"\1\n{nav}", content, count=1, flags=re.IGNORECASE)
    content = content.replace(
        '<div class="slides">',
        '<div class="slides" role="region" aria-label="Presentation slides">',
        1,
    )
    if not re.search(r"\bkeyboard\s*:\s*true\b", content):
        raise RenderingError(
            "[slides.accessibility.keyboard] Reveal.js keyboard navigation is not enabled",
            context={"source": str(html_file), "diagnostic_code": "slides.accessibility.keyboard"},
        )
    write_if_changed(html_file, content)


def accessible_reveal_output_issues(html_file: Path) -> tuple[str, ...]:
    """Return structural issues for one accessibility-enhanced Reveal deck."""

    try:
        if not html_file.is_file() or html_file.stat().st_size == 0:
            return ("file is missing or empty",)
        content = html_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return (f"file is not readable UTF-8: {exc}",)

    issues: list[str] = []
    if _STANDALONE_HTML_RE.search(content) is None:
        issues.append("document is not standalone HTML")
    issues.extend(
        f"missing accessible Reveal marker: {marker}" for marker in _ACCESSIBLE_REVEAL_MARKERS if marker not in content
    )
    if re.search(r"\bkeyboard\s*:\s*true\b", content) is None:
        issues.append("Reveal keyboard navigation is not enabled")
    return tuple(issues)


__all__ = [
    "AccessibleSlideComposition",
    "AccessibleSlidePolicy",
    "accessible_reveal_output_issues",
    "compose_accessible_pandoc_document",
    "enhance_accessible_reveal",
    "load_and_compose_pandoc_json",
]
