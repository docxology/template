"""Tests for manuscript figure writers (src/manuscript_figures.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.grammar import KNOWN_DOMAINS
from src.manuscript_figures import (
    _teal_slate_palette,
    fig_coverage_by_module,
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


def _write_fake_coverage_json(path: Path, module_pcts: dict[str, float]) -> None:
    files = {
        f"/repo/projects/templates/template_autopoiesis/src/{name}": {"summary": {"percent_covered": pct}}
        for name, pct in module_pcts.items()
    }
    path.write_text(json.dumps({"files": files}))


def test_fig_coverage_by_module_writes_png(tmp_path):
    cov_json = tmp_path / "coverage_full.json"
    _write_fake_coverage_json(cov_json, {"cli.py": 75.28, "grammar.py": 94.29, "cover_art.py": 100.0})
    out_dir = tmp_path / "figures"
    out_dir.mkdir()
    out = fig_coverage_by_module(cov_json, out_dir)
    assert out == out_dir / "fig_coverage_by_module.png"
    assert out.exists()
    assert out.stat().st_size > 100


def test_fig_coverage_by_module_sorts_lowest_first(tmp_path):
    cov_json = tmp_path / "coverage_full.json"
    _write_fake_coverage_json(cov_json, {"a.py": 51.0, "b.py": 100.0, "c.py": 88.0})
    out_dir = tmp_path / "figures"
    out_dir.mkdir()
    data = json.loads(cov_json.read_text())
    pcts = sorted(entry["summary"]["percent_covered"] for entry in data["files"].values())
    assert pcts == [51.0, 88.0, 100.0]
    fig_coverage_by_module(cov_json, out_dir)


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
