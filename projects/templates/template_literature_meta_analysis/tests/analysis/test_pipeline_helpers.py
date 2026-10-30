"""Tests for analysis helpers moved from orchestrators."""

from __future__ import annotations

from template_literature_meta_analysis.analysis.temporal_analysis import compute_subfield_timeline
from template_literature_meta_analysis.analysis.text_processing import tokenize_documents
from template_literature_meta_analysis.literature.models import Paper


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
