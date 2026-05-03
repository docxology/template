"""Tests for src.figures — real matplotlib, no mocks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.search.literature import Paper, SearchQuery, SearchResult

from src.figures import (
    generate_all_figures,
    load_search_result,
    plot_papers_per_source,
    plot_score_distribution,
    plot_year_histogram,
)


def _result_with_papers() -> SearchResult:
    return SearchResult(
        query=SearchQuery(text="x", max_results=5),
        papers=[
            Paper(id="a", title="Alpha", year=2010, score=0.9),
            Paper(id="b", title="Beta", year=2014, score=0.6),
            Paper(id="c", title="Gamma", year=2014, score=0.4),
        ],
        per_source_counts={"arxiv": 2, "crossref": 1},
        errors={},
    )


def test_papers_per_source_writes_png(tmp_path: Path):
    out = plot_papers_per_source(_result_with_papers(), tmp_path)
    assert out.exists()
    assert out.suffix == ".png"
    assert out.stat().st_size > 0


def test_year_histogram_writes_png(tmp_path: Path):
    out = plot_year_histogram(_result_with_papers(), tmp_path)
    assert out.exists() and out.stat().st_size > 0


def test_score_distribution_writes_png(tmp_path: Path):
    out = plot_score_distribution(_result_with_papers(), tmp_path)
    assert out.exists() and out.stat().st_size > 0


def test_handles_empty_result(tmp_path: Path):
    empty = SearchResult(query=SearchQuery(text="x"), papers=[], per_source_counts={})
    paths = generate_all_figures(empty, tmp_path)
    assert all(p.exists() for p in paths)
    assert {p.name for p in paths} == {
        "papers_per_source.png",
        "year_histogram.png",
        "score_distribution.png",
    }


def test_generate_all_returns_stable_order(tmp_path: Path):
    result = _result_with_papers()
    first = [p.name for p in generate_all_figures(result, tmp_path)]
    second = [p.name for p in generate_all_figures(result, tmp_path)]
    assert first == second


def test_load_search_result_round_trip(tmp_path: Path):
    result = _result_with_papers()
    path = tmp_path / "results.json"
    path.write_text(result.to_json(), encoding="utf-8")
    loaded = load_search_result(path)
    assert loaded.query.text == "x"
    assert len(loaded.papers) == 3
    assert loaded.per_source_counts == {"arxiv": 2, "crossref": 1}


def test_load_search_result_with_filters(tmp_path: Path):
    result = SearchResult(
        query=SearchQuery(text="x", max_results=5, year_min=2010, year_max=2020),
        papers=[],
    )
    path = tmp_path / "r.json"
    path.write_text(result.to_json(), encoding="utf-8")
    loaded = load_search_result(path)
    assert loaded.query.year_min == 2010
    assert loaded.query.year_max == 2020


def test_papers_with_missing_year_skipped_in_histogram(tmp_path: Path):
    result = SearchResult(
        query=SearchQuery(text="x"),
        papers=[
            Paper(id="a", title="Alpha", year=None),
            Paper(id="b", title="Beta", year=2020),
        ],
    )
    out = plot_year_histogram(result, tmp_path)
    assert out.exists()
