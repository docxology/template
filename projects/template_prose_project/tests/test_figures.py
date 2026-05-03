"""Tests for src.figures — real matplotlib, no mocks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.prose import analyze_files

from src.figures import (
    generate_all_figures,
    load_manuscript_report,
    plot_citation_density,
    plot_readability_radar,
    plot_section_word_counts,
)


def _sample_report():
    files = {
        "00_a.md": "# A\n\nThis paragraph cites [@k1] and explains things.",
        "01_b.md": "# B\n\nThis text cites [@k2] briefly.",
    }
    return analyze_files(files)


def test_section_word_counts(tmp_path: Path):
    out = plot_section_word_counts(_sample_report(), tmp_path)
    assert out.exists() and out.stat().st_size > 0


def test_readability_radar(tmp_path: Path):
    out = plot_readability_radar(_sample_report(), tmp_path)
    assert out.exists() and out.stat().st_size > 0


def test_citation_density(tmp_path: Path):
    out = plot_citation_density(_sample_report(), tmp_path)
    assert out.exists() and out.stat().st_size > 0


def test_generate_all_stable_order(tmp_path: Path):
    report = _sample_report()
    first = [p.name for p in generate_all_figures(report, tmp_path)]
    second = [p.name for p in generate_all_figures(report, tmp_path)]
    assert first == second


def test_handles_empty_report(tmp_path: Path):
    from infrastructure.prose import analyze_files as af
    report = af({})
    paths = generate_all_figures(report, tmp_path)
    assert all(p.exists() for p in paths)


def test_load_manuscript_report_round_trip(tmp_path: Path):
    report = _sample_report()
    path = tmp_path / "r.json"
    path.write_text(report.to_json(), encoding="utf-8")
    loaded = load_manuscript_report(path)
    assert loaded.total_words == report.total_words
    assert len(loaded.files) == len(report.files)
    assert loaded.citation_keys == report.citation_keys
