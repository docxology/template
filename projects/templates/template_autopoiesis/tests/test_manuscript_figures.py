"""Tests for manuscript figure writers (src/manuscript_figures.py)."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.grammar import KNOWN_DOMAINS
from src.manuscript_figures import (
    _teal_slate_palette,
    fig_domain_coverage,
    fig_product_space_annotation,
    fig_stacked_product,
    generate_manuscript_figures,
)


@pytest.fixture
def template_root():
    return Path(__file__).parent.parent


def test_teal_slate_palette_cycles_and_has_no_duplicates_within_base_length():
    palette = _teal_slate_palette(8)
    assert len(palette) == 8
    assert len(set(palette)) == 8


def test_teal_slate_palette_wraps_past_base_length():
    palette = _teal_slate_palette(10)
    assert len(palette) == 10
    assert palette[8] == palette[0]
    assert palette[9] == palette[1]


def test_fig_stacked_product_writes_png(template_root, tmp_path):
    out = fig_stacked_product(template_root, tmp_path)
    assert out == tmp_path / "fig_stacked_product.png"
    assert out.exists()
    assert out.stat().st_size > 100


def test_fig_domain_coverage_writes_png(tmp_path):
    out = fig_domain_coverage(tmp_path)
    assert out == tmp_path / "fig_domain_coverage.png"
    assert out.exists()
    assert out.stat().st_size > 100


def test_fig_product_space_annotation_writes_png(template_root, tmp_path):
    out = fig_product_space_annotation(template_root, tmp_path)
    assert out == tmp_path / "fig_product_space.png"
    assert out.exists()
    assert out.stat().st_size > 100


def test_fig_domain_coverage_covers_every_known_domain(tmp_path):
    # A domain missing from the hardcoded color map would raise KeyError.
    fig_domain_coverage(tmp_path)
    assert set(KNOWN_DOMAINS) == {
        "optimization",
        "dynamics",
        "statistics",
        "signal",
        "graph",
    }


def test_generate_manuscript_figures_writes_all_three(template_root, tmp_path):
    paths = generate_manuscript_figures(template_root, tmp_path)
    assert len(paths) == 3
    names = {p.name for p in paths}
    assert names == {
        "fig_stacked_product.png",
        "fig_domain_coverage.png",
        "fig_product_space.png",
    }
    for p in paths:
        assert p.exists()
        assert p.stat().st_size > 100
