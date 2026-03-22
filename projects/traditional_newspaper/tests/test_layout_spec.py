"""Tests for ``newspaper.layout_spec``."""

from newspaper.layout_spec import LAYOUT, NewspaperLayout, column_count_valid


def test_default_layout_constants() -> None:
    assert LAYOUT.column_count == 3
    assert LAYOUT.paper_width_in == 11.0
    assert LAYOUT.paper_height_in == 17.0
    assert LAYOUT.body_font_pt == 9


def test_geometry_latex_options_contains_dimensions() -> None:
    s = LAYOUT.geometry_latex_options()
    assert "11" in s and "17" in s and "margin" in s


def test_multicol_sep_latex() -> None:
    assert r"\columnsep" in LAYOUT.multicol_sep_latex()


def test_custom_layout() -> None:
    alt = NewspaperLayout(margin_in=0.5, column_count=4)
    assert alt.margin_in == 0.5
    assert "0.5in" in alt.geometry_latex_options()


def test_column_count_valid() -> None:
    assert column_count_valid(2) is True
    assert column_count_valid(3) is True
    assert column_count_valid(8) is True
    assert column_count_valid(1) is False
    assert column_count_valid(9) is False
