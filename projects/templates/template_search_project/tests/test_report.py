"""Tests for src.report — assembles markdown from search + synthesis."""

from __future__ import annotations

from pathlib import Path

from infrastructure.search.literature import Paper, SearchQuery, SearchResult

from src.report import write_reading_report
from src.synthesis import SynthesisResult


def _result_with_papers() -> SearchResult:
    query = SearchQuery(text="reproducibility", max_results=2)
    papers = [
        Paper(
            id="doi:10.1/x",
            title="Reproducible Research",
            authors=["Roger D Peng"],
            year=2011,
            doi="10.1/x",
            abstract="An overview of reproducibility in computational science.",
        ),
        Paper(
            id="arxiv:1412.6980",
            title="Adam: A Method for Stochastic Optimization",
            authors=["Kingma, Diederik P", "Ba, Jimmy"],
            year=2014,
            url="https://arxiv.org/abs/1412.6980",
            abstract="An optimizer for deep learning.",
        ),
    ]
    return SearchResult(
        query=query,
        papers=papers,
        per_source_counts={"local": 2},
    )


def test_report_contains_topic_and_papers(tmp_path: Path):
    result = _result_with_papers()
    keys = {"doi:10.1/x": "peng2011reproducible", "arxiv:1412.6980": "kingma2014adam"}
    out = write_reading_report(
        tmp_path / "report.md",
        search_result=result,
        citation_keys=keys,
        title="Demo",
    )
    text = out.read_text(encoding="utf-8")
    assert "# Demo" in text
    assert "_Topic:_ **reproducibility**" in text
    assert "[peng2011reproducible]" in text
    assert "[kingma2014adam]" in text
    assert "https://doi.org/10.1/x" in text
    assert "Source | Papers" in text


def test_report_includes_per_paper_when_provided(tmp_path: Path):
    result = _result_with_papers()
    keys = {p.id: p.id for p in result.papers}
    per_paper = [
        SynthesisResult(
            kind="per_paper",
            prompt="prompt",
            text="CONTRIBUTION: x\nMETHOD: y",
            paper_id="doi:10.1/x",
        ),
    ]
    out = write_reading_report(
        tmp_path / "r.md",
        search_result=result,
        citation_keys=keys,
        per_paper=per_paper,
    )
    text = out.read_text(encoding="utf-8")
    assert "## Per-Paper Notes" in text
    assert "CONTRIBUTION: x" in text


def test_report_includes_corpus_synthesis(tmp_path: Path):
    result = _result_with_papers()
    keys = {p.id: p.id for p in result.papers}
    synth = SynthesisResult(kind="corpus", prompt="p", text="Cluster A: foo. Cluster B: bar.")
    out = write_reading_report(
        tmp_path / "r.md",
        search_result=result,
        citation_keys=keys,
        corpus_synthesis=synth,
    )
    text = out.read_text(encoding="utf-8")
    assert "## Cross-Corpus Synthesis" in text
    assert "Cluster A: foo." in text


def test_report_warns_about_backend_errors(tmp_path: Path):
    query = SearchQuery(text="x")
    result = SearchResult(
        query=query,
        papers=[],
        per_source_counts={},
        errors={"crossref": "HTTP 503"},
    )
    out = write_reading_report(tmp_path / "r.md", search_result=result, citation_keys={})
    text = out.read_text(encoding="utf-8")
    assert "Partial coverage" in text
    assert "crossref" in text
    assert "HTTP 503" in text


def test_report_handles_year_filter(tmp_path: Path):
    query = SearchQuery(text="x", year_min=2010, year_max=2024)
    result = SearchResult(query=query, papers=[])
    out = write_reading_report(tmp_path / "r.md", search_result=result, citation_keys={})
    text = out.read_text(encoding="utf-8")
    assert "Year filter" in text
    assert "2010" in text and "2024" in text
