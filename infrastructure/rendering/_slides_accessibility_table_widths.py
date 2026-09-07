"""Exact column-span constraints and proportional width allocation for accessible tables."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility_contracts import (
    BODY_CHARACTERS_PER_LINE_20PT,
    TABLE_INTERCOLUMN_GUTTER_CHARACTERS,
    TABLE_MINIMUM_COLUMN_CHARACTERS,
    AccessibleSlidePolicy,
    density_error,
)
from infrastructure.rendering._slides_accessibility_table_cells import (
    _table_cell_demand,
    _table_cell_minimum,
    _validate_table_cell_block_shapes,
)
from infrastructure.rendering._slides_accessibility_table_structure import _table_group_layout, _table_row_groups

_BODY_CHARACTERS_PER_LINE_20PT = BODY_CHARACTERS_PER_LINE_20PT
_TABLE_INTERCOLUMN_GUTTER_CHARACTERS = TABLE_INTERCOLUMN_GUTTER_CHARACTERS
_TABLE_MINIMUM_COLUMN_CHARACTERS = TABLE_MINIMUM_COLUMN_CHARACTERS


@dataclass(frozen=True)
class _TableWidthConstraint:
    """One active interval edge in the exact column-minimum solution."""

    start: int
    end: int
    required: int
    token: str


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
