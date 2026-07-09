"""No-mocks tests for src/chart_rendering.py — real matplotlib output."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from chart_rendering import (
    render_coverage_bar_chart,
    render_infra_subpackage_donut,
    render_test_count_vs_coverage_scatter,
)
from infrastructure.rendering.slide_deck import DeckTheme

THEME = DeckTheme()


@pytest.fixture
def coverage_rows():
    return [
        ("template_pitch_deck", 82, 97.13),
        ("alpha_exemplar", 300, 91.0),
        ("beta_exemplar", 50, 100.0),
    ]


@pytest.fixture
def infra_rows():
    return [("core", 100), ("rendering", 40), ("validation", 30), ("search", 5)]


def test_render_coverage_bar_chart_writes_real_file(tmp_path: Path, coverage_rows):
    output_path = tmp_path / "coverage.png"
    count = render_coverage_bar_chart(plt, THEME, coverage_rows, output_path)
    assert count == 3
    assert output_path.is_file()
    assert output_path.stat().st_size > 1000


def test_render_test_count_vs_coverage_scatter_writes_real_file(tmp_path: Path, coverage_rows):
    output_path = tmp_path / "scatter.png"
    count = render_test_count_vs_coverage_scatter(plt, THEME, coverage_rows, output_path)
    assert count == 3
    assert output_path.is_file()
    assert output_path.stat().st_size > 1000


def test_render_infra_subpackage_donut_writes_real_file(tmp_path: Path, infra_rows):
    output_path = tmp_path / "donut.png"
    count = render_infra_subpackage_donut(plt, THEME, infra_rows, output_path)
    assert count == 4
    assert output_path.is_file()
    assert output_path.stat().st_size > 1000


def test_render_infra_subpackage_donut_aggregates_beyond_top_n(tmp_path: Path):
    many_rows = [(f"pkg{i}", 10 - i) for i in range(12)]
    output_path = tmp_path / "donut_many.png"
    count = render_infra_subpackage_donut(plt, THEME, many_rows, output_path)
    assert count == 12
    assert output_path.is_file()


def test_charts_produce_different_bytes_for_different_data(tmp_path: Path, coverage_rows):
    path_a = tmp_path / "a.png"
    path_b = tmp_path / "b.png"
    render_coverage_bar_chart(plt, THEME, coverage_rows, path_a)
    flipped = [(name, tests, 50.0) for name, tests, _ in coverage_rows]
    render_coverage_bar_chart(plt, THEME, flipped, path_b)
    assert path_a.read_bytes() != path_b.read_bytes()
