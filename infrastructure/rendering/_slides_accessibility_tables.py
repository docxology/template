"""Fail-closed accessible table excerpts over shared parsing and geometry helpers.

Existing private helper imports remain available through this module.
"""

from __future__ import annotations

import copy
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_ast import _frame_body_line_capacity
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
)
from infrastructure.rendering._slides_accessibility_table_cells import (
    _inline_unbreakable_tokens as _inline_unbreakable_tokens,
    _table_cell_demand as _table_cell_demand,
    _table_cell_lines as _table_cell_lines,
    _table_cell_minimum as _table_cell_minimum,
    _table_row_lines as _table_row_lines,
    _table_rows_line_costs as _table_rows_line_costs,
    _table_rows_lines as _table_rows_lines,
    _table_wrapping_text as _table_wrapping_text,
    _validate_table_cell_block_shapes as _validate_table_cell_block_shapes,
    _wrapped_text_lines as _wrapped_text_lines,
)
from infrastructure.rendering._slides_accessibility_table_structure import (
    _table_cell_parts as _table_cell_parts,
    _table_group_layout as _table_group_layout,
    _table_row_cells as _table_row_cells,
    _table_row_count as _table_row_count,
    _table_row_groups as _table_row_groups,
    _table_rows as _table_rows,
)
from infrastructure.rendering._slides_accessibility_table_widths import (
    _minimum_constrained_widths as _minimum_constrained_widths,
    _table_available_character_capacity as _table_available_character_capacity,
    _table_column_character_capacities as _table_column_character_capacities,
    _table_column_geometry as _table_column_geometry,
    _table_column_minima as _table_column_minima,
    _table_column_widths as _table_column_widths,
    _TableWidthConstraint as _TableWidthConstraint,
)

_BODY_CHARACTERS_PER_LINE_20PT = BODY_CHARACTERS_PER_LINE_20PT
_LIST_CHARACTERS_PER_LINE_20PT = LIST_CHARACTERS_PER_LINE_20PT
_TABLE_INTERCOLUMN_GUTTER_CHARACTERS = TABLE_INTERCOLUMN_GUTTER_CHARACTERS
_TABLE_LIST_INDENT_WIDTH_UNITS = TABLE_LIST_INDENT_WIDTH_UNITS
_TABLE_MINIMUM_COLUMN_CHARACTERS = TABLE_MINIMUM_COLUMN_CHARACTERS
_TABLE_RULE_PADDING_LINES = TABLE_RULE_PADDING_LINES
_TABLE_TOKEN_SAFETY_CHARACTERS = TABLE_TOKEN_SAFETY_CHARACTERS


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
