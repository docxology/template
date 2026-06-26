"""Tests for the pure page/column geometry."""

from __future__ import annotations

import pytest

from newspaper.geometry import INCH, ColumnGrid, PageGeometry


def test_tabloid_default_dimensions() -> None:
    g = PageGeometry()
    assert g.width == pytest.approx(11 * INCH)
    assert g.height == pytest.approx(17 * INCH)
    assert g.content_width == pytest.approx(g.width - g.margin_left - g.margin_right)
    assert g.content_height == pytest.approx(g.content_top - g.content_bottom)
    assert g.content_top > g.content_bottom


def test_page_geometry_content_left_and_right() -> None:
    """content_left and content_right derive correctly from margins."""
    g = PageGeometry(width=792, height=1224, margin_left=36, margin_right=36)
    assert g.content_left == pytest.approx(36.0)
    assert g.content_right == pytest.approx(756.0)
    assert g.content_width == pytest.approx(720.0)


def test_column_grid_partitions_width() -> None:
    grid = ColumnGrid(left=36.0, width=720.0, n_columns=5, gutter=12.0)
    # 5 columns + 4 gutters must reconstruct the total width exactly.
    total = grid.column_width * 5 + grid.total_gutter
    assert total == pytest.approx(720.0)
    assert grid.column_x(0) == pytest.approx(36.0)
    assert grid.column_x(4) + grid.column_width == pytest.approx(36.0 + 720.0)


def test_column_grid_single_column() -> None:
    """A single-column grid has zero total_gutter and zero gutter_centers."""
    grid = ColumnGrid(left=0.0, width=500.0, n_columns=1, gutter=12.0)
    assert grid.total_gutter == pytest.approx(0.0)
    assert grid.gutter_centers() == []
    assert grid.column_x(0) == pytest.approx(0.0)
    assert grid.column_width == pytest.approx(500.0)


def test_column_grid_monotonic_and_gutters() -> None:
    grid = ColumnGrid(left=0.0, width=600.0, n_columns=4, gutter=10.0)
    xs = [grid.column_x(i) for i in range(4)]
    assert xs == sorted(xs)
    centers = grid.gutter_centers()
    assert len(centers) == 3
    # Each gutter centre sits between two adjacent columns.
    assert centers[0] > grid.column_x(0)
    assert centers[0] < grid.column_x(1)


def test_column_grid_right_returns_left_plus_width() -> None:
    """right() == left + width regardless of column count or gutter."""
    grid = ColumnGrid(left=72.0, width=648.0, n_columns=6, gutter=8.0)
    assert grid.right() == pytest.approx(72.0 + 648.0)


def test_column_grid_gutter_zero_is_allowed() -> None:
    """gutter=0 is valid (columns abut); total_gutter is 0."""
    grid = ColumnGrid(left=0.0, width=300.0, n_columns=3, gutter=0.0)
    assert grid.total_gutter == pytest.approx(0.0)
    assert grid.column_width == pytest.approx(100.0)


def test_column_grid_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        ColumnGrid(left=0, width=600, n_columns=0)
    with pytest.raises(ValueError):
        ColumnGrid(left=0, width=-1, n_columns=3)
    with pytest.raises(ValueError):
        ColumnGrid(left=0, width=10, n_columns=50, gutter=10)  # cannot fit
    with pytest.raises(ValueError):
        ColumnGrid(left=0, width=100, n_columns=3, gutter=-1)  # negative gutter
    with pytest.raises(IndexError):
        ColumnGrid(left=0, width=600, n_columns=4).column_x(9)
    with pytest.raises(IndexError):
        ColumnGrid(left=0, width=600, n_columns=4).column_x(-1)
