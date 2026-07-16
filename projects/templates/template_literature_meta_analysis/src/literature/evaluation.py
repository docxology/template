"""Corpus evaluation: source mix, metadata coverage, and claim-verification summaries.

Produces a single JSON-serializable dict summarizing corpus quality along
three axes:

1. **Source provenance** — which engines contributed each paper's full text,
   broken down by ``full_text_source`` and OA/preprint/published status.
2. **Metadata completeness** — mean ``metadata_completeness`` across the
   corpus, DOI coverage, duplicate-title detection (a proxy for cross-engine
   dedup quality).
3. **Claim verification** — optional summary of LLM-extracted assertion
   verdicts (supports/contradicts/insufficient) passed in by the caller;
   ``None`` when no verdicts are supplied.

Mirrors :mod:`literature.fulltext_assessment` in convention: a pure function
over a :class:`~literature.corpus.Corpus` (no I/O, no side effects), with
the caller (``scripts/07_literature_evaluation.py``) handling JSON
serialization. The function never raises on missing/malformed fields — a
paper with no abstract, no authors, or no DOI contributes zeros, not
exceptions.

The ``_SOURCE_KEYS`` list reflects all 10 engines in the search roster
(arXiv, Semantic Scholar, OpenAlex, Crossref, PubMed, SovietRxiv, ChinaRxiv,
Europe PMC, bioRxiv, medRxiv), kept in sync with
:mod:`literature.engine_dispatch`'s ``ENGINE_SPECS``.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any, Sequence

from literature.corpus import Corpus
from literature.query_router import QueryRouter

_SOURCE_KEYS = [
    "arxiv",
    "semantic_scholar",
    "openalex",
    "crossref",
    "pubmed",
    "sovietrxiv",
    "chinarxiv",
    "europepmc",
    "biorxiv",
    "medrxiv",
]


def _get_value(obj: Any, name: str) -> Any:
    """Retrieve *name* from a dict (``.get``) or an object (``getattr``)."""
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def evaluate_corpus(
    corpus: Corpus,
    *,
    query: str | None = None,
    claim_verdicts: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Compute a corpus-quality summary over source mix, metadata, and claims.

    Args:
        corpus: The corpus to evaluate.
        query: Optional search query string. When provided, the
            :class:`~literature.query_router.QueryRouter` is invoked to
            determine the best source ordering for this query type, and the
            route is included in the output under ``query_route``. When
            ``None``, no routing is performed.
        claim_verdicts: Optional sequence of claim-verdict objects (dicts or
            dataclasses with ``verdict`` and ``confidence`` attributes).
            Each verdict is classified into ``supported``/``contradicted``/
            ``insufficient``; mean confidence is computed across all
            verdicts that supply a numeric ``confidence``. When ``None``,
            ``claim_verification`` is ``None`` in the output.

    Returns:
        A dict with keys ``total_papers``, ``doi_count``, ``preprint_count``,
        ``metadata_completeness_mean``, ``duplicate_title_groups``,
        ``source_breakdown``, ``query_route``, and ``claim_verification``.
        Never raises on missing fields — empty papers contribute zeros.
    """
    papers = corpus.papers
    total = len(papers)

    source_counter = Counter(
        (paper.full_text_source or ("preprint" if paper.is_preprint else "published" if paper.doi else "unknown"))
        for paper in papers
    )
    title_counter = Counter(paper.normalized_title for paper in papers if paper.normalized_title)
    metadata_mean = round(mean(paper.metadata_completeness for paper in papers), 2) if papers else 0.0

    route = QueryRouter().route(query, _SOURCE_KEYS) if query else None

    verdict_summary = None
    if claim_verdicts is not None:
        counts: dict[str, int] = {"supported": 0, "contradicted": 0, "insufficient": 0}
        confidences: list[float] = []
        for verdict in claim_verdicts:
            value = _get_value(verdict, "verdict")
            if isinstance(value, str) and value in counts:
                counts[value] += 1
            confidence = _get_value(verdict, "confidence")
            if isinstance(confidence, (int, float)):
                confidences.append(float(confidence))
        verdict_summary = {
            "count": sum(counts.values()),
            "supported": counts["supported"],
            "contradicted": counts["contradicted"],
            "insufficient": counts["insufficient"],
            "mean_confidence": round(mean(confidences), 3) if confidences else 0.0,
        }

    return {
        "total_papers": total,
        "doi_count": sum(1 for paper in papers if paper.doi),
        "preprint_count": sum(1 for paper in papers if paper.is_preprint),
        "metadata_completeness_mean": metadata_mean,
        "duplicate_title_groups": sum(1 for _, count in title_counter.items() if count > 1),
        "source_breakdown": dict(source_counter.most_common()),
        "query_route": (
            None
            if route is None
            else {
                "query_type": route.query_type,
                "confidence": route.confidence,
                "matched_patterns": list(route.matched_patterns),
                "source_order": list(route.source_order),
                "prefer_preprints": route.prefer_preprints,
            }
        ),
        "claim_verification": verdict_summary,
    }
