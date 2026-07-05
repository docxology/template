"""Tests for the figure gallery (every plot type produces a real PNG)."""

from __future__ import annotations

import pytest

from visualization import gallery


def _assert_png(path):
    assert path.exists()
    assert path.suffix == ".png"
    assert path.stat().st_size > 0
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.parametrize("name,fn", gallery.GALLERY, ids=[n for n, _ in gallery.GALLERY])
def test_each_gallery_plot_writes_png(tmp_path, name, fn):
    path = fn(tmp_path)
    _assert_png(path)
    assert path.name == f"gallery_{name}.png"


def test_generate_gallery_figures_covers_registry(tmp_path):
    paths = gallery.generate_gallery_figures(tmp_path)
    assert len(paths) == len(gallery.GALLERY)
    for path in paths:
        _assert_png(path)


def test_gallery_registry_names_unique():
    names = [name for name, _ in gallery.GALLERY]
    assert len(names) == len(set(names))
    assert len(names) >= 16  # broad coverage of plot types


def test_gallery_is_deterministic(tmp_path):
    p1 = gallery.histogram(tmp_path / "a")
    p2 = gallery.histogram(tmp_path / "b")
    assert p1.read_bytes() == p2.read_bytes()


def test_load_specs_reads_yaml_catalogue():
    specs = gallery.load_specs()
    assert len(specs) == len(gallery.GALLERY)
    assert specs[0]["name"] == "line"


def test_render_gallery_entry_unknown_name(tmp_path):
    with pytest.raises(ValueError, match="unknown gallery plot name"):
        gallery.render_gallery_entry({"name": "not_a_plot"}, tmp_path)
