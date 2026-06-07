"""Tests for deterministic figure generation (real PNG files, no mocks)."""

from __future__ import annotations

import pytest

from textbook.config import iter_chapters, load_config
from visualization import _scaffold, plots


def _png_is_nonempty(path):
    assert path.exists()
    assert path.suffix == ".png"
    assert path.stat().st_size > 0
    # PNG magic number.
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.parametrize(
    "fn",
    [
        plots.plot_logistic_growth,
        plots.plot_saturating_response,
        plots.plot_exponential_decay,
        plots.plot_linear_fit,
    ],
)
def test_worked_figures_write_png(tmp_path, fn):
    _png_is_nonempty(fn(tmp_path))


def test_placeholder_overview(tmp_path):
    path = plots.placeholder_overview("A Chapter", tmp_path, "demo")
    _png_is_nonempty(path)
    assert path.name == "demo.png"


def test_generate_chapter_placeholders_matches_config(tmp_path):
    config = load_config()
    paths = plots.generate_chapter_placeholders(tmp_path, config)
    # One placeholder per enabled chapter — derive from config, not a literal.
    assert len(paths) == len(iter_chapters(config))
    for path in paths:
        _png_is_nonempty(path)


def test_generate_all_figures(tmp_path):
    worked = plots.generate_worked_figures(tmp_path)
    paths = plots.generate_all_figures(tmp_path)
    # all figures = worked figures + one placeholder per enabled chapter.
    assert len(paths) == len(worked) + len(iter_chapters(load_config()))
    names = {p.name for p in paths}
    assert "logistic_growth.png" in names  # a worked figure
    assert "part_0_orientation.png" in names  # a chapter placeholder that is displayed


def test_scaffold_new_figure_and_save(tmp_path):
    fig, ax = _scaffold.new_figure(width=4, height=3)
    ax.plot([0, 1], [0, 1])
    path = _scaffold.save_figure(fig, tmp_path, "noext")
    _png_is_nonempty(path)
    assert path.name == "noext.png"


def test_cover_art(tmp_path):
    path = plots.cover_art(tmp_path, subtitle="A scaffold")
    _png_is_nonempty(path)
    assert path.name == "template_textbook_cover.png"


def test_figures_are_deterministic(tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    p1 = plots.plot_logistic_growth(first)
    p2 = plots.plot_logistic_growth(second)
    assert p1.read_bytes() == p2.read_bytes()
