"""No-mocks tests for src/chart_rendering.py — real matplotlib output."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from chart_rendering import (
    _apply_donut_autotext_contrast,
    _contrast_ratio,
    _hex_rgb,
    _visible_artist_rgb,
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


def test_donut_autotext_uses_wcag_contrast_on_real_wedge_artists():
    theme = DeckTheme(
        black="#000000",
        white="#FFFFFF",
        highlight_1="#111111",
        highlight_2="#F4E04D",
        highlight_3="#6A1B9A",
    )
    fig, ax = plt.subplots()
    wedges, _labels, autotexts = ax.pie(
        [25, 25, 25, 25],
        colors=[theme.highlight_1, theme.highlight_2, theme.highlight_3, theme.black],
        autopct="%1.0f%%",
    )
    wedges[2].set_alpha(0.75)

    ratios = _apply_donut_autotext_contrast(wedges, autotexts, theme)

    assert min(ratios) >= 4.5
    assert autotexts[0].get_color() == theme.white
    assert autotexts[1].get_color() == theme.black
    canvas_rgb = _hex_rgb(theme.white)
    for wedge, autotext in zip(wedges, autotexts, strict=True):
        visible_wedge_rgb = _visible_artist_rgb(wedge, canvas_rgb)
        text_rgb = _hex_rgb(autotext.get_color())
        assert _contrast_ratio(text_rgb, visible_wedge_rgb) >= 4.5
    plt.close(fig)


def test_donut_autotext_contrast_fails_closed_for_unreadable_theme():
    theme = DeckTheme(
        black="#777777",
        white="#888888",
        highlight_1="#808080",
        highlight_2="#808080",
        highlight_3="#808080",
    )
    fig, ax = plt.subplots()
    wedges, _labels, autotexts = ax.pie([100], colors=[theme.highlight_1], autopct="%1.0f%%")

    with pytest.raises(ValueError, match=r"4\.5:1 contrast floor"):
        _apply_donut_autotext_contrast(wedges, autotexts, theme)
    plt.close(fig)


def test_charts_produce_different_bytes_for_different_data(tmp_path: Path, coverage_rows):
    path_a = tmp_path / "a.png"
    path_b = tmp_path / "b.png"
    render_coverage_bar_chart(plt, THEME, coverage_rows, path_a)
    flipped = [(name, tests, 50.0) for name, tests, _ in coverage_rows]
    render_coverage_bar_chart(plt, THEME, flipped, path_b)
    assert path_a.read_bytes() != path_b.read_bytes()
