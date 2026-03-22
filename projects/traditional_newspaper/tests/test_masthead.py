"""Tests for ``newspaper.masthead``."""

from pathlib import Path

import matplotlib.image as mpimg

from newspaper.masthead import render_masthead_png


def test_render_masthead_png_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "masthead.png"
    result = render_masthead_png(out, seed=7)
    assert result == out
    assert out.is_file()
    assert out.stat().st_size > 2_000


def test_render_masthead_deterministic_seed(tmp_path: Path) -> None:
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    render_masthead_png(a, seed=99)
    render_masthead_png(b, seed=99)
    assert a.read_bytes() == b.read_bytes()


def test_render_masthead_different_seed_differs(tmp_path: Path) -> None:
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    render_masthead_png(a, seed=1)
    render_masthead_png(b, seed=2)
    assert a.read_bytes() != b.read_bytes()


def test_masthead_image_readable(tmp_path: Path) -> None:
    out = tmp_path / "m.png"
    render_masthead_png(out)
    img = mpimg.imread(out)
    assert img.ndim == 3
    assert min(img.shape[0], img.shape[1]) >= 80
