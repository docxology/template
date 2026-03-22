"""Tests for ``newspaper.layout_figure``."""

from pathlib import Path

import matplotlib.image as mpimg

from newspaper.layout_figure import render_layout_schematic_png
from newspaper.layout_spec import LAYOUT, NewspaperLayout


def test_render_layout_schematic_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "layout_schematic.png"
    result = render_layout_schematic_png(out)
    assert result == out
    assert out.is_file()
    assert out.stat().st_size > 1_500


def test_render_layout_schematic_deterministic(tmp_path: Path) -> None:
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    render_layout_schematic_png(a, dpi=120)
    render_layout_schematic_png(b, dpi=120)
    assert a.read_bytes() == b.read_bytes()


def test_layout_schematic_image_shape(tmp_path: Path) -> None:
    out = tmp_path / "l.png"
    render_layout_schematic_png(out, dpi=100)
    img = mpimg.imread(out)
    assert img.ndim == 3
    assert img.shape[0] >= 400
    assert img.shape[1] >= 250


def test_custom_layout_alters_width(tmp_path: Path) -> None:
    narrow = NewspaperLayout(paper_width_in=8.5, paper_height_in=11.0, margin_in=0.5)
    a = tmp_path / "tabloid.png"
    b = tmp_path / "letter.png"
    render_layout_schematic_png(a, layout=LAYOUT, dpi=80)
    render_layout_schematic_png(b, layout=narrow, dpi=80)
    assert a.read_bytes() != b.read_bytes()
