"""Pandoc table geometry and fail-closed bounded excerpts for accessible slides."""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_ast import _frame_body_line_capacity
from infrastructure.rendering._slides_accessibility_text_geometry import (
    _block_contains,
    _inline_physical_tokens,
    _math_vertical_line_demand,
    _plain_text,
    _validate_math_geometry,
)
from infrastructure.rendering._slides_accessibility_contracts import (
    BODY_CHARACTERS_PER_LINE_20PT,
    LIST_CHARACTERS_PER_LINE_20PT,
    TABLE_INTERCOLUMN_GUTTER_CHARACTERS,
    TABLE_LIST_INDENT_WIDTH_UNITS,
    TABLE_MINIMUM_COLUMN_CHARACTERS,
    TABLE_RULE_PADDING_LINES,
    TABLE_TOKEN_SAFETY_CHARACTERS,
    AccessibleSlidePolicy,
    density_error,
    proportional_text_width_units,
    tex_math_width_units,
    tex_hyphen_segments,
)


_BODY_CHARACTERS_PER_LINE_20PT = BODY_CHARACTERS_PER_LINE_20PT
_LIST_CHARACTERS_PER_LINE_20PT = LIST_CHARACTERS_PER_LINE_20PT
_TABLE_INTERCOLUMN_GUTTER_CHARACTERS = TABLE_INTERCOLUMN_GUTTER_CHARACTERS
_TABLE_LIST_INDENT_WIDTH_UNITS = TABLE_LIST_INDENT_WIDTH_UNITS
_TABLE_MINIMUM_COLUMN_CHARACTERS = TABLE_MINIMUM_COLUMN_CHARACTERS
_TABLE_RULE_PADDING_LINES = TABLE_RULE_PADDING_LINES
_TABLE_TOKEN_SAFETY_CHARACTERS = TABLE_TOKEN_SAFETY_CHARACTERS


@dataclass(frozen=True)
class _TableWidthConstraint:
    """One active interval edge in the exact column-minimum solution."""

    start: int
    end: int
    required: int
    token: str


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


def _table_row_groups(content: list[Any]) -> list[list[Any]]:
    """Return row-span domains without allowing spans to cross table sections."""

    head_rows, _body_rows, foot_rows = _table_rows(content)
    groups = [head_rows]
    for body in content[4]:
        groups.append([*body[2], *body[3]])
    groups.append(foot_rows)
    return groups


def _table_group_layout(
    rows: list[Any],
    column_count: int,
) -> list[list[tuple[int, int, int, list[Any]]]]:
    """Place cells in physical columns while honoring active row spans."""

    active_until = [-1] * column_count
    layout: list[list[tuple[int, int, int, list[Any]]]] = []
    for row_index, row in enumerate(rows):
        placements: list[tuple[int, int, int, list[Any]]] = []
        search_start = 0
        for cell in _table_row_cells(row):
            row_span, column_span, blocks = _table_cell_parts(cell)
            if row_index + row_span > len(rows):
                raise RenderingError(
                    "Accessible slide composition received a Pandoc Table row span outside its row group"
                )
            while search_start + column_span <= column_count:
                candidate = range(search_start, search_start + column_span)
                if all(active_until[index] < row_index for index in candidate):
                    break
                search_start += 1
            else:
                raise RenderingError(
                    "Accessible slide composition received overlapping spans or a Table row wider than its column specs"
                )
            for index in range(search_start, search_start + column_span):
                active_until[index] = row_index + row_span - 1
            placements.append((search_start, row_span, column_span, blocks))
            search_start += column_span
        layout.append(placements)
    return layout


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


def _table_column_geometry(
    content: list[Any],
    column_count: int,
) -> tuple[list[int], list[str], tuple[_TableWidthConstraint, ...], list[int]]:
    """Solve contiguous cell-span width constraints over physical columns.

    Let ``S[j]`` be the prefix width through column ``j``. Every one-column
    minimum and colspan becomes a forward lower-bound edge
    ``S[end] >= S[start] + required``. The longest path through this acyclic
    graph is the minimum-total integer allocation satisfying every constraint.
    Unlike local deficit balancing, it lets overlapping spans share width in
    their common columns.
    """

    base_minima = [_TABLE_MINIMUM_COLUMN_CHARACTERS for _ in range(column_count)]
    source_tokens = ["" for _ in range(column_count)]
    span_constraints: list[_TableWidthConstraint] = []
    for rows in _table_row_groups(content):
        for placements in _table_group_layout(rows, column_count):
            for column_index, _row_span, column_span, blocks in placements:
                cell_minimum, token = _table_cell_minimum(blocks)
                end = column_index + column_span
                for index in range(column_index, end):
                    if token and not source_tokens[index]:
                        source_tokens[index] = token
                if column_span == 1:
                    if cell_minimum > base_minima[column_index]:
                        base_minima[column_index] = cell_minimum
                        if token:
                            source_tokens[column_index] = token
                    continue
                required = max(
                    0,
                    cell_minimum - _TABLE_INTERCOLUMN_GUTTER_CHARACTERS * (column_span - 1),
                )
                span_constraints.append(
                    _TableWidthConstraint(
                        start=column_index,
                        end=end,
                        required=required,
                        token=token,
                    )
                )

    by_end: list[list[_TableWidthConstraint]] = [[] for _ in range(column_count + 1)]
    for constraint in span_constraints:
        by_end[constraint.end].append(constraint)
    prefixes = [0 for _ in range(column_count + 1)]
    selected_tokens = ["" for _ in range(column_count)]
    predecessor: list[_TableWidthConstraint | None] = [None for _ in range(column_count + 1)]
    for end in range(1, column_count + 1):
        best = prefixes[end - 1] + base_minima[end - 1]
        best_token = source_tokens[end - 1]
        selected = _TableWidthConstraint(
            start=end - 1,
            end=end,
            required=base_minima[end - 1],
            token=best_token,
        )
        for constraint in by_end[end]:
            candidate = prefixes[constraint.start] + constraint.required
            if candidate > best:
                best = candidate
                best_token = constraint.token
                selected = constraint
        prefixes[end] = best
        predecessor[end] = selected
        selected_tokens[end - 1] = best_token
    minima = [prefixes[index + 1] - prefixes[index] for index in range(column_count)]
    for index, token in enumerate(selected_tokens):
        if token and minima[index] > base_minima[index]:
            source_tokens[index] = token
    active_constraints: list[_TableWidthConstraint] = []
    cursor = column_count
    while cursor > 0:
        active_constraint = predecessor[cursor]
        if active_constraint is None:
            break
        active_constraints.append(active_constraint)
        cursor = active_constraint.start
    active_constraints.reverse()
    return minima, source_tokens, tuple(active_constraints), base_minima


def _table_column_minima(content: list[Any], column_count: int) -> tuple[list[int], list[str]]:
    """Return exact minima and their source tokens for compatibility tests."""

    minima, source_tokens, _active_constraints, _base_minima = _table_column_geometry(content, column_count)
    return minima, source_tokens


def _table_available_character_capacity(column_count: int, policy: AccessibleSlidePolicy) -> int:
    """Return usable body-character width after conservative column gutters."""

    return max(
        column_count,
        math.floor(_BODY_CHARACTERS_PER_LINE_20PT * 20 / policy.body_font_pt)
        - _TABLE_INTERCOLUMN_GUTTER_CHARACTERS * max(0, column_count - 1),
    )


def _minimum_constrained_widths(weights: list[float], minima: list[int], total: int) -> list[float]:
    """Project desired proportions onto exact lower-width constraints."""

    desired_total = sum(weights)
    desired = [weight / desired_total for weight in weights]
    lower = [minimum / total for minimum in minima]
    resolved = [0.0 for _ in weights]
    remaining = set(range(len(weights)))
    remaining_fraction = 1.0
    while remaining:
        remaining_weight = sum(desired[index] for index in remaining)
        below = [
            index
            for index in sorted(remaining)
            if remaining_fraction * desired[index] / remaining_weight < lower[index] - 1e-12
        ]
        if not below:
            for index in remaining:
                resolved[index] = remaining_fraction * desired[index] / remaining_weight
            break
        for index in below:
            resolved[index] = lower[index]
            remaining_fraction -= lower[index]
            remaining.remove(index)
    return resolved


def _table_column_widths(
    content: list[Any],
    policy: AccessibleSlidePolicy,
    *,
    source: str,
    heading: str,
) -> tuple[list[float], list[int]]:
    """Resolve source widths and indivisible minima into slide widths."""

    colspecs = content[2]
    if not isinstance(colspecs, list) or not colspecs:
        raise RenderingError("Accessible slide composition requires at least one Pandoc Table column")
    column_count = len(colspecs)
    _validate_table_cell_block_shapes(content, source=source, heading=heading)
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

    minima, source_tokens, active_constraints, base_minima = _table_column_geometry(content, column_count)
    available_width_units = _table_available_character_capacity(column_count, policy)
    required_width_units = sum(minima)
    if required_width_units > available_width_units:
        cumulative = 0
        offending_column = column_count - 1
        for index, minimum in enumerate(minima):
            cumulative += minimum
            if cumulative > available_width_units:
                offending_column = index
                break
        individually_impossible_column = next(
            (index for index, minimum in enumerate(base_minima) if minimum > available_width_units),
            None,
        )
        offending_span = None
        if individually_impossible_column is not None:
            offending_column = individually_impossible_column
            offending_token = source_tokens[offending_column] or "(minimum column width)"
        else:
            offending_span = next(
                (constraint for constraint in reversed(active_constraints) if constraint.end - constraint.start > 1),
                None,
            )
        if offending_span is not None:
            offending_column = offending_span.start
            offending_token = offending_span.token or "(spanning cell minimum)"
        elif individually_impossible_column is None:
            offending_token = source_tokens[offending_column] or "(minimum column width)"
        raise density_error(
            "slides.density.indivisible-table-width",
            "table columns cannot contain their ordinary indivisible tokens at the declared font floor",
            source=source,
            heading=heading,
            column_count=column_count,
            body_font_pt=policy.body_font_pt,
            available_width_units=available_width_units,
            required_width_units=required_width_units,
            intercolumn_gutter_width_units=_TABLE_INTERCOLUMN_GUTTER_CHARACTERS * max(0, column_count - 1),
            column_minimum_width_units=minima,
            first_offending_column_index=offending_column + 1,
            first_offending_token=offending_token,
            first_offending_column_minimum_width_units=minima[offending_column],
            offending_span_start_column_index=(offending_span.start + 1 if offending_span is not None else None),
            offending_span_end_column_index=(offending_span.end if offending_span is not None else None),
            offending_span_required_width_units=(offending_span.required if offending_span is not None else None),
        )

    demand = [float(minimum) for minimum in minima]
    for rows in _table_row_groups(content):
        for placements in _table_group_layout(rows, column_count):
            for column_index, _row_span, column_span, blocks in placements:
                per_column_demand = _table_cell_demand(blocks) / column_span
                for index in range(column_index, column_index + column_span):
                    demand[index] = max(demand[index], per_column_demand)

    explicit_values = [width for width in explicit if width is not None]
    uniformly_explicit = (
        bool(explicit_values)
        and len(explicit_values) == len(explicit)
        and math.isclose(
            max(explicit_values),
            min(explicit_values),
            rel_tol=1e-9,
            abs_tol=1e-12,
        )
    )
    if all(width is None for width in explicit) or uniformly_explicit:
        # Pandoc serializes ordinary pipe tables as equal numeric widths in
        # some versions. Those values are writer defaults, not meaningful
        # author allocation. Recompute them from visible demand so short
        # symbol columns do not steal projection width from prose columns.
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
    normalized = _minimum_constrained_widths(weights, minima, available_width_units)
    # Give Pandoc explicit widths so the rendered table wraps according to the
    # same geometry the accessible composer validated. Archive rendering never
    # enters this opt-in transformation.
    rounded = [round(width, 6) for width in normalized[:-1]]
    rounded.append(round(1.0 - sum(rounded), 6))
    if rounded[-1] <= 0:
        rounded = normalized
    for colspec, resolved_width in zip(colspecs, rounded, strict=True):
        colspec[1] = {"t": "ColWidth", "c": resolved_width}
    return rounded, minima


def _table_column_character_capacities(
    widths: list[float],
    policy: AccessibleSlidePolicy,
    minima: list[int],
) -> list[int]:
    """Allocate conservative visible-character capacities across columns."""

    column_count = len(widths)
    if len(minima) != column_count:
        raise RenderingError("Accessible slide composition received inconsistent Table width minima")
    total = _table_available_character_capacity(column_count, policy)
    remaining = total - sum(minima)
    target_extra = [max(0.0, total * width - minimum) for width, minimum in zip(widths, minima, strict=True)]
    target_total = sum(target_extra)
    raw_extra = (
        [remaining * value / target_total for value in target_extra]
        if target_total > 0
        else [remaining * width for width in widths]
    )
    capacities = [minimum + math.floor(value) for minimum, value in zip(minima, raw_extra, strict=True)]
    undistributed = total - sum(capacities)
    order = sorted(range(column_count), key=lambda index: (raw_extra[index] % 1, -index), reverse=True)
    for index in order[:undistributed]:
        capacities[index] += 1
    return capacities


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


def _excerpt_table(
    block: dict[str, Any],
    policy: AccessibleSlidePolicy,
    *,
    header: dict[str, Any],
    continuation: int,
    source: str,
    heading: str,
) -> tuple[dict[str, Any], bool]:
    """Create a row-bounded table excerpt that fits accessible 16:9 geometry."""

    updated = copy.deepcopy(block)
    content = updated.get("c")
    if not isinstance(content, list) or len(content) != 6 or not isinstance(content[4], list):
        raise RenderingError("Accessible slide composition received a malformed Pandoc Table")
    head_rows, _all_body_rows, foot_rows = _table_rows(content)
    if any(body[2] and not body[3] for body in content[4]):
        raise density_error(
            "slides.density.header-only-table-body",
            "a table body header without data rows cannot form a meaningful projection excerpt",
            source=source,
            heading=heading,
        )
    widths, minima = _table_column_widths(
        content,
        policy,
        source=source,
        heading=heading,
    )
    capacities = _table_column_character_capacities(widths, policy, minima)
    maximum_lines = _frame_body_line_capacity(header, continuation, policy)
    # Both projected surfaces already carry a persistent canonical-reader
    # link. Repeating that link as a table caption consumes scarce geometry
    # without adding a distinct accessible name.
    fixed_lines = _TABLE_RULE_PADDING_LINES
    global_header_lines = _table_rows_lines(head_rows, capacities)
    source_footer_lines = _table_rows_lines(foot_rows, capacities)
    consumed_lines = fixed_lines + global_header_lines + source_footer_lines
    remaining_rows = policy.max_table_rows
    kept_rows = 0
    original_rows = _table_row_count(block)
    excerpted = False
    saw_first_body_row = False
    stop_excerpt = False

    body_metrics: list[tuple[int, list[int], bool]] = []
    full_table_lines = consumed_lines
    for body in content[4]:
        body_head_rows = body[2]
        rows = body[3]
        combined_rows = [*body_head_rows, *rows]
        combined_costs = _table_rows_line_costs(combined_rows, capacities)
        body_head_lines = sum(combined_costs[: len(body_head_rows)])
        row_line_costs = combined_costs[len(body_head_rows) :]
        has_row_span = any(
            row_span > 1
            for placements in _table_group_layout(combined_rows, len(capacities))
            for _column, row_span, _column_span, _blocks in placements
        )
        body_metrics.append((body_head_lines, row_line_costs, has_row_span))
        full_table_lines += body_head_lines + sum(row_line_costs)

    excerpt_required = original_rows > policy.max_table_rows or full_table_lines > maximum_lines
    full_table_lines_without_footer = full_table_lines - source_footer_lines
    row_excerpt_required = original_rows > policy.max_table_rows or full_table_lines_without_footer > maximum_lines
    if excerpt_required:
        # Once the full source table cannot fit, its complete-table footer is
        # omitted from projection. Recompute available geometry before choosing
        # a body-row prefix; the canonical reader retains the complete footer.
        consumed_lines -= source_footer_lines
        footer_lines = 0
        excerpted = True
    else:
        footer_lines = source_footer_lines

    if row_excerpt_required and any(has_row_span for _head_lines, _row_costs, has_row_span in body_metrics):
        raise density_error(
            "slides.density.indivisible-table",
            "a row-spanning table cannot be excerpted without fragmenting a semantic cell",
            source=source,
            heading=heading,
            column_count=len(widths),
            body_row_count=original_rows,
            available_lines=maximum_lines,
            fixed_lines=fixed_lines,
            footer_lines=footer_lines,
            title_font_pt=policy.title_font_pt,
            body_font_pt=policy.body_font_pt,
            maximum_body_rows=policy.max_table_rows,
            global_header_lines=global_header_lines,
            row_span_excerpt_blocked=True,
            resolved_widths=widths,
            column_character_capacities=capacities,
        )

    for body, (body_head_lines, row_line_costs, _has_row_span) in zip(content[4], body_metrics, strict=True):
        body_head_rows = body[2]
        rows = body[3]
        kept_in_body: list[Any] = []
        if not stop_excerpt:
            for row, row_lines in zip(rows, row_line_costs, strict=True):
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
        first_body_head_lines = 0
        first_row_lines = 0
        for body, (body_head_lines, row_line_costs, _has_row_span) in zip(block["c"][4], body_metrics, strict=True):
            if body[3]:
                first_body_head_lines = body_head_lines
                first_row_lines = row_line_costs[0]
                break
        raise density_error(
            "slides.density.indivisible-table",
            "one complete table row cannot fit the projection frame at the declared font floor",
            source=source,
            heading=heading,
            column_count=len(widths),
            body_row_count=original_rows,
            available_lines=maximum_lines,
            fixed_lines=fixed_lines,
            title_font_pt=policy.title_font_pt,
            body_font_pt=policy.body_font_pt,
            maximum_body_rows=policy.max_table_rows,
            global_header_lines=global_header_lines,
            footer_lines=footer_lines,
            first_body_header_lines=first_body_head_lines,
            first_row_lines=first_row_lines,
            resolved_widths=widths,
            column_character_capacities=capacities,
        )
    if not original_rows and consumed_lines > maximum_lines:
        raise density_error(
            "slides.density.indivisible-table",
            "the complete table header cannot fit the projection frame at the declared font floor",
            source=source,
            heading=heading,
            column_count=len(widths),
            body_row_count=0,
            available_lines=maximum_lines,
            fixed_lines=fixed_lines,
            title_font_pt=policy.title_font_pt,
            body_font_pt=policy.body_font_pt,
            maximum_body_rows=policy.max_table_rows,
            global_header_lines=global_header_lines,
            footer_lines=footer_lines,
            first_body_header_lines=0,
            first_row_lines=0,
            resolved_widths=widths,
            column_character_capacities=capacities,
        )
    excerpted = excerpted or kept_rows < original_rows or original_rows > policy.max_table_rows
    if excerpted:
        # A footer such as "Total 10" semantically summarizes the complete
        # table.  Retaining it below a five-row projection prefix would make a
        # partial excerpt look complete.  The canonical reader keeps the
        # source table and footer; projection removes only the misleading
        # footer rows while preserving the TableFoot attributes.
        foot = content[5]
        if not isinstance(foot, list) or len(foot) != 2:
            raise RenderingError("Accessible slide composition received a malformed Pandoc Table foot")
        foot[1] = []
    # The full source caption and every omitted row remain in the canonical
    # reader. The projected surfaces' persistent companion link preserves the
    # route to that material without squeezing a duplicate caption onto frame.
    content[1] = [None, []]
    return updated, excerpted
