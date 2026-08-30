"""Pandoc table geometry and fail-closed bounded excerpts for accessible slides."""

from __future__ import annotations

import copy
import math
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_ast import (
    _frame_body_line_capacity,
    _plain_text,
)
from infrastructure.rendering._slides_accessibility_contracts import (
    BODY_CHARACTERS_PER_LINE_20PT,
    TABLE_INTERCOLUMN_GUTTER_CHARACTERS,
    TABLE_MINIMUM_COLUMN_CHARACTERS,
    TABLE_RULE_PADDING_LINES,
    AccessibleSlidePolicy,
    density_error,
)


_BODY_CHARACTERS_PER_LINE_20PT = BODY_CHARACTERS_PER_LINE_20PT
_TABLE_INTERCOLUMN_GUTTER_CHARACTERS = TABLE_INTERCOLUMN_GUTTER_CHARACTERS
_TABLE_MINIMUM_COLUMN_CHARACTERS = TABLE_MINIMUM_COLUMN_CHARACTERS
_TABLE_RULE_PADDING_LINES = TABLE_RULE_PADDING_LINES


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
    widths = _table_column_widths(content)
    capacities = _table_column_character_capacities(widths, policy)
    maximum_lines = _frame_body_line_capacity(header, continuation, policy)
    # Both projected surfaces already carry a persistent canonical-reader
    # link. Repeating that link as a table caption consumes scarce geometry
    # without adding a distinct accessible name.
    fixed_lines = _TABLE_RULE_PADDING_LINES
    global_header_lines = _table_rows_lines(head_rows, capacities)
    footer_lines = _table_rows_lines(foot_rows, capacities)
    consumed_lines = fixed_lines + global_header_lines + footer_lines
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

    if (original_rows > policy.max_table_rows or full_table_lines > maximum_lines) and any(
        has_row_span for _head_lines, _row_costs, has_row_span in body_metrics
    ):
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
    # The full source caption and every omitted row remain in the canonical
    # reader. The projected surfaces' persistent companion link preserves the
    # route to that material without squeezing a duplicate caption onto frame.
    content[1] = [None, []]
    return updated, excerpted
