"""Pandoc table parsing and physical row/column span placement for accessible slides."""

from __future__ import annotations

from typing import Any

from infrastructure.core.exceptions import RenderingError


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
