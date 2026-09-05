"""Accessible table-cell shape validation, physical token demand, and wrapped height."""

from __future__ import annotations

import math
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import (
    BODY_CHARACTERS_PER_LINE_20PT,
    LIST_CHARACTERS_PER_LINE_20PT,
    TABLE_INTERCOLUMN_GUTTER_CHARACTERS,
    TABLE_LIST_INDENT_WIDTH_UNITS,
    TABLE_MINIMUM_COLUMN_CHARACTERS,
    TABLE_TOKEN_SAFETY_CHARACTERS,
    density_error,
    proportional_text_width_units,
    tex_hyphen_segments,
    tex_math_width_units,
)
from infrastructure.rendering._slides_accessibility_table_structure import _table_group_layout, _table_row_groups
from infrastructure.rendering._slides_accessibility_text_geometry import (
    _block_contains,
    _inline_physical_tokens,
    _math_vertical_line_demand,
    _plain_text,
    _validate_math_geometry,
)

_BODY_CHARACTERS_PER_LINE_20PT = BODY_CHARACTERS_PER_LINE_20PT
_LIST_CHARACTERS_PER_LINE_20PT = LIST_CHARACTERS_PER_LINE_20PT
_TABLE_INTERCOLUMN_GUTTER_CHARACTERS = TABLE_INTERCOLUMN_GUTTER_CHARACTERS
_TABLE_LIST_INDENT_WIDTH_UNITS = TABLE_LIST_INDENT_WIDTH_UNITS
_TABLE_MINIMUM_COLUMN_CHARACTERS = TABLE_MINIMUM_COLUMN_CHARACTERS
_TABLE_TOKEN_SAFETY_CHARACTERS = TABLE_TOKEN_SAFETY_CHARACTERS


def _inline_unbreakable_tokens(value: object) -> list[tuple[str, int]]:
    """Return visible token labels and conservative body-character widths.

    Ordinary prose may break at whitespace and after an explicit ASCII hyphen;
    slashes and other punctuation remain part of the same indivisible token.
    Pandoc inline ``Code`` shorter than the downstream ``breaktt`` threshold is
    sized at the wider monospace face. Longer code is character-breakable after
    LaTeX post-processing, so it contributes one guarded monospace glyph rather
    than monopolizing a source column.
    """

    if isinstance(value, str):
        return _inline_physical_tokens(value)
    if isinstance(value, list):
        return [token for item in value for token in _inline_unbreakable_tokens(item)]
    if not isinstance(value, dict):
        return []
    tag = value.get("t")
    content = value.get("c")
    if tag == "CodeBlock" and isinstance(content, list) and len(content) == 2:
        source_text = content[1]
        if not isinstance(source_text, str):
            raise RenderingError("Accessible slide composition received a malformed Pandoc CodeBlock in a Table")
        # Pandoc writes table-cell CodeBlock nodes as FancyVerb. A physical
        # verbatim line has no TeX break opportunity—not even at an ASCII
        # hyphen or space—so price every expanded line in the monospace face.
        # This deliberately differs from long inline Code, which the later
        # breaktt pass can transform under its exact source/LaTeX predicate.
        return [
            (
                line,
                math.ceil(len(line.expandtabs(4)) * (_BODY_CHARACTERS_PER_LINE_20PT / _LIST_CHARACTERS_PER_LINE_20PT))
                + _TABLE_TOKEN_SAFETY_CHARACTERS,
            )
            for line in (source_text.splitlines() or [source_text])
            if line
        ]
    if tag in {"BulletList", "OrderedList"}:
        raw_items = content
        if tag == "OrderedList" and isinstance(content, list) and len(content) == 2:
            raw_items = content[1]
        if not isinstance(raw_items, list):
            raise RenderingError("Accessible slide composition received a malformed Pandoc list in a Table")
        tokens = [token for item in raw_items for token in _inline_unbreakable_tokens(item)]
        # The item marker and its following separation consume real horizontal
        # space inside Pandoc's table-cell minipage. The calibrated three-unit
        # debit accepts the last clean 40-glyph ordinary item and rejects the
        # observed overflowing 42-glyph boundary before LaTeX. Nested lists
        # accumulate the same debit recursively.
        return [(token, width + _TABLE_LIST_INDENT_WIDTH_UNITS) for token, width in tokens]
    return _inline_physical_tokens(value)


def _table_wrapping_text(value: object) -> str:
    """Return width-aligned text for table vertical wrapping estimates."""

    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_table_wrapping_text(item) for item in value)
    if not isinstance(value, dict):
        return ""
    tag = value.get("t")
    content = value.get("c")
    if tag in {"Space", "SoftBreak"}:
        return " "
    if tag == "LineBreak":
        return "\n"
    if tag == "Str" and isinstance(content, str):
        return content
    if tag == "Math" and isinstance(content, list) and content:
        source = str(content[-1])
        # Use the exact same calibrated math width as the horizontal minimum;
        # raw TeX command spelling is neither visible nor a legal wrap model.
        return "x" * tex_math_width_units(source)
    if tag == "Cite":
        return _plain_text(value)
    if tag in {"Code", "RawInline", "RawBlock"} and isinstance(content, list) and content:
        return str(content[-1])
    if tag in {"Link", "Image", "Quoted"} and isinstance(content, list) and len(content) >= 2:
        return _table_wrapping_text(content[1])
    if tag in {"Div", "Span"} and isinstance(content, list) and len(content) >= 2:
        return _table_wrapping_text(content[1])
    return _table_wrapping_text(content)


def _table_cell_minimum(blocks: list[Any]) -> tuple[int, str]:
    """Return the guarded width and source token for one table cell."""

    tokens = _inline_unbreakable_tokens(blocks)
    if not tokens:
        return _TABLE_MINIMUM_COLUMN_CHARACTERS, ""
    token, width = max(tokens, key=lambda item: item[1])
    return max(_TABLE_MINIMUM_COLUMN_CHARACTERS, width), token


def _table_cell_demand(blocks: list[Any]) -> float:
    """Return bounded explanatory demand without overpricing breakable code."""

    text = " ".join(_plain_text(blocks).split())
    minimum, _token = _table_cell_minimum(blocks)
    if not text:
        return float(minimum)
    # The square-root term gives explanatory cells more room without allowing
    # one paragraph to consume the frame. The source-node-aware minimum above
    # replaces the old raw longest-token term, which incorrectly treated long
    # Code spans as indivisible despite the later ``breaktt`` transformation.
    return float(max(minimum, min(32, math.ceil(math.sqrt(len(text)) * 2.5))))


def _validate_table_cell_block_shapes(
    content: list[Any],
    *,
    source: str,
    heading: str,
) -> None:
    """Reject rich cell blocks whose geometry is not explicitly modeled."""

    supported = {"Plain", "Para", "CodeBlock", "BulletList", "OrderedList", "Div"}

    def validate(block: object) -> None:
        if not isinstance(block, dict) or not isinstance(block.get("t"), str):
            raise RenderingError("Accessible slide composition received a malformed Pandoc block in a Table")
        tag = block["t"]
        content_value = block.get("c")
        _validate_math_geometry(block, source=source, heading=heading)
        if _block_contains(block, "Note"):
            raise density_error(
                "slides.density.unsupported-note",
                "Pandoc notes are not projected because Beamer footnotes violate the "
                "declared accessible font and geometry contract",
                source=source,
                heading=heading,
                block_type=tag,
            )
        if tag not in supported:
            raise density_error(
                "slides.density.unsupported-table-cell-block",
                "a rich table-cell block has no declared accessible projection geometry",
                source=source,
                heading=heading,
                block_type=tag,
            )
        if tag == "Div":
            if not isinstance(content_value, list) or len(content_value) < 2 or not isinstance(content_value[1], list):
                raise RenderingError("Accessible slide composition received a malformed Pandoc Div in a Table")
            for nested in content_value[1]:
                validate(nested)
            return
        if tag in {"BulletList", "OrderedList"}:
            raw_items = content_value
            if tag == "OrderedList" and isinstance(content_value, list) and len(content_value) == 2:
                raw_items = content_value[1]
            if not isinstance(raw_items, list) or any(not isinstance(item, list) for item in raw_items):
                raise RenderingError("Accessible slide composition received a malformed Pandoc list in a Table")
            for item in raw_items:
                for nested in item:
                    validate(nested)

    for rows in _table_row_groups(content):
        for placements in _table_group_layout(rows, len(content[2])):
            for _column_index, _row_span, _column_span, blocks in placements:
                for block in blocks:
                    validate(block)


def _wrapped_text_lines(text: str, capacity: int) -> int:
    """Estimate deterministic wrapping at whitespace and TeX hyphens."""

    words = text.split()
    if not words:
        return 1
    lines = 1
    used = 0
    for word in words:
        segments = tex_hyphen_segments(word)
        separator = 1 if used else 0
        for segment_index, segment in enumerate(segments):
            segment_length = proportional_text_width_units(segment)
            prefix = separator if segment_index == 0 else 0
            if used + prefix + segment_length <= capacity:
                used += prefix + segment_length
                continue
            if used:
                lines += 1
                used = 0
            # The minima pass prevents ordinary and short-Code segments from
            # entering this branch. Character-level wrapping remains valid for
            # long Code because the downstream ``breaktt`` pass adds precisely
            # those opportunities before LaTeX compilation.
            whole_lines, remainder = divmod(segment_length, capacity)
            if whole_lines:
                lines += whole_lines - int(remainder == 0)
            used = remainder or min(segment_length, capacity)
    return lines


def _table_cell_lines(blocks: list[Any], capacity: int) -> int:
    """Estimate the vertical line cost of one table cell."""

    if not blocks:
        return 1
    lines = 0
    for block in blocks:
        if not isinstance(block, dict):
            raise RenderingError("Accessible slide composition received a malformed Pandoc block in a Table")
        tag = block.get("t")
        content = block.get("c")
        if tag == "CodeBlock":
            if not isinstance(content, list) or len(content) != 2 or not isinstance(content[1], str):
                raise RenderingError("Accessible slide composition received a malformed Pandoc CodeBlock in a Table")
            # Width preflight has already proved that each FancyVerb physical
            # line fits. Preserve the source line structure for vertical cost.
            lines += max(1, len(content[1].splitlines()))
            continue
        if tag in {"BulletList", "OrderedList"}:
            raw_items = content
            if tag == "OrderedList" and isinstance(content, list) and len(content) == 2:
                raw_items = content[1]
            if not isinstance(raw_items, list) or any(not isinstance(item, list) for item in raw_items):
                raise RenderingError("Accessible slide composition received a malformed Pandoc list in a Table")
            item_capacity = max(1, capacity - _TABLE_LIST_INDENT_WIDTH_UNITS)
            lines += sum(max(1, _table_cell_lines(item, item_capacity)) for item in raw_items)
            continue
        if tag == "Div":
            if not isinstance(content, list) or len(content) < 2 or not isinstance(content[1], list):
                raise RenderingError("Accessible slide composition received a malformed Pandoc Div in a Table")
            lines += _table_cell_lines(content[1], capacity)
            continue
        physical_text = _table_wrapping_text(block)
        wrapped_lines = sum(
            _wrapped_text_lines(" ".join(segment.split()), capacity) for segment in physical_text.split("\n")
        )
        _math_source, math_lines = _math_vertical_line_demand(block)
        lines += max(wrapped_lines, math_lines)
    return max(1, lines)


def _table_rows_line_costs(rows: list[Any], capacities: list[int]) -> list[int]:
    """Return conservative per-row costs with physical row/column spans."""

    costs = [1] * len(rows)
    for row_index, placements in enumerate(_table_group_layout(rows, len(capacities))):
        for column_index, row_span, column_span, blocks in placements:
            capacity = sum(capacities[column_index : column_index + column_span])
            capacity += _TABLE_INTERCOLUMN_GUTTER_CHARACTERS * (column_span - 1)
            cell_lines = _table_cell_lines(blocks, max(1, capacity))
            # Equal ceiling allocation can overprice a spanning cell by fewer
            # than ``row_span`` lines, but it cannot underprice the projected
            # geometry. Every occupied row and physical column is accounted.
            per_row = math.ceil(cell_lines / row_span)
            for offset in range(row_span):
                costs[row_index + offset] = max(costs[row_index + offset], per_row)
    return costs


def _table_row_lines(row: Any, capacities: list[int]) -> int:
    """Return the wrapped height of one non-spanning row in body-line units."""

    return _table_rows_line_costs([row], capacities)[0]


def _table_rows_lines(rows: list[Any], capacities: list[int]) -> int:
    return sum(_table_rows_line_costs(rows, capacities))
