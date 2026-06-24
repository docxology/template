"""Tests for analysis helpers moved from orchestrators."""

from __future__ import annotations

from types import SimpleNamespace

from analysis.temporal_analysis import compute_subfield_timeline
from analysis.text_processing import tokenize_documents
from literature.models import Paper


def test_compute_subfield_timeline(sample_papers: list[Paper]) -> None:
    classified = {"A1_formal": sample_papers[:2], "B_tools": sample_papers[2:]}
    timeline = compute_subfield_timeline(classified)
    assert isinstance(timeline, dict)
    for years in timeline.values():
        assert all(isinstance(y, str) for y in years)


def test_tokenize_documents() -> None:
    docs = ["Active Inference free energy", "Predictive coding models"]
    tokens = tokenize_documents(docs)
    assert len(tokens) == 2
    assert all(isinstance(row, list) for row in tokens)


def test_count_paper_references_prefers_references_list() -> None:
    from analysis.pipeline_runner import _count_paper_references

    paper = Paper(title="t", abstract="a", authors=[], references=["r1", "r2", "r3"])
    assert _count_paper_references(paper) == 3


def test_count_paper_references_falls_back_to_referenced_works() -> None:
    from analysis.pipeline_runner import _count_paper_references

    paper = SimpleNamespace(references=[], referenced_works=["w1", "w2"])
    assert _count_paper_references(paper) == 2
