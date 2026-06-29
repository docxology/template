"""Tests for :func:`literature.evaluation.evaluate_corpus`.

Real Paper/Corpus objects only (no mocks). Exercises every branch of the
public evaluation harness used by ``scripts/07_literature_evaluation.py``:
source breakdown, duplicate-title detection, metadata completeness, optional
query routing, and the optional claim-verdict summary (both dict-shaped and
attribute-shaped verdicts).
"""

from __future__ import annotations

from dataclasses import dataclass

from literature.corpus import Corpus
from literature.evaluation import evaluate_corpus
from literature.models import Author, Paper


def _published(title: str, *, doi: str | None, source: str | None = None) -> Paper:
    return Paper(
        title=title,
        abstract="An abstract about modafinil and wakefulness.",
        authors=[Author(name="Jane Researcher")],
        year=2021,
        doi=doi,
        venue="Journal of Sleep",
        full_text_source=source,
    )


def _build_corpus() -> Corpus:
    corpus = Corpus()
    # Two papers with the same normalized title -> one duplicate group.
    corpus.add(_published("Modafinil and Wakefulness", doi="10.1/a", source="openalex"))
    corpus.add(_published("Modafinil and Wakefulness", doi="10.1/b", source="openalex"))
    # A preprint with an arXiv id and no DOI.
    corpus.add(
        Paper(
            title="Eugeroic Mechanisms Reviewed",
            abstract="A preprint on eugeroic mechanisms.",
            authors=[Author(name="Sam Author")],
            year=2022,
            arxiv_id="2201.00001",
            full_text_source="arxiv",
        )
    )
    return corpus


def test_evaluate_corpus_basic_counts() -> None:
    """Aggregate counts reflect the real corpus contents."""
    result = evaluate_corpus(_build_corpus())

    assert result["total_papers"] == 3
    assert result["doi_count"] == 2
    assert result["preprint_count"] == 1
    assert result["duplicate_title_groups"] == 1
    assert isinstance(result["metadata_completeness_mean"], float)
    assert result["source_breakdown"]  # non-empty mapping
    # No query and no verdicts supplied -> those sections are None.
    assert result["query_route"] is None
    assert result["claim_verification"] is None


def test_evaluate_corpus_empty() -> None:
    """An empty corpus yields zeroed counts without raising."""
    result = evaluate_corpus(Corpus())

    assert result["total_papers"] == 0
    assert result["doi_count"] == 0
    assert result["preprint_count"] == 0
    assert result["metadata_completeness_mean"] == 0.0
    assert result["duplicate_title_groups"] == 0


def test_evaluate_corpus_with_query_route() -> None:
    """Supplying a query populates the routing summary."""
    result = evaluate_corpus(_build_corpus(), query="modafinil cognition")

    route = result["query_route"]
    assert route is not None
    assert isinstance(route["query_type"], str)
    assert isinstance(route["source_order"], list)
    assert route["source_order"]  # router returns an ordering
    assert isinstance(route["prefer_preprints"], bool)


@dataclass
class _Verdict:
    verdict: str
    confidence: float


def test_evaluate_corpus_claim_verdicts_objects_and_dicts() -> None:
    """Verdict summary tallies both attribute- and dict-shaped verdicts."""
    verdicts = [
        _Verdict("supported", 0.9),
        _Verdict("contradicted", 0.4),
        {"verdict": "insufficient", "confidence": 0.5},
        {"verdict": "supported", "confidence": 0.7},
        {"verdict": "not_a_category", "confidence": "n/a"},  # ignored gracefully
    ]
    result = evaluate_corpus(_build_corpus(), claim_verdicts=verdicts)

    summary = result["claim_verification"]
    assert summary is not None
    assert summary["count"] == 4  # the unknown verdict is not counted
    assert summary["supported"] == 2
    assert summary["contradicted"] == 1
    assert summary["insufficient"] == 1
    # Mean confidence over the numeric confidences only (0.9, 0.4, 0.5, 0.7).
    assert summary["mean_confidence"] == 0.625


def test_evaluate_corpus_empty_verdicts_list() -> None:
    """An empty verdict list still produces a zeroed summary."""
    result = evaluate_corpus(_build_corpus(), claim_verdicts=[])

    summary = result["claim_verification"]
    assert summary is not None
    assert summary["count"] == 0
    assert summary["mean_confidence"] == 0.0
