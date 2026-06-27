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
]


def _get_value(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def evaluate_corpus(
    corpus: Corpus,
    *,
    query: str | None = None,
    claim_verdicts: Sequence[Any] | None = None,
) -> dict[str, Any]:
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
        counts = {"supported": 0, "contradicted": 0, "insufficient": 0}
        confidences: list[float] = []
        for verdict in claim_verdicts:
            value = _get_value(verdict, "verdict")
            if value in counts:
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
        "query_route": None
        if route is None
        else {
            "query_type": route.query_type,
            "confidence": route.confidence,
            "matched_patterns": list(route.matched_patterns),
            "source_order": list(route.source_order),
            "prefer_preprints": route.prefer_preprints,
        },
        "claim_verification": verdict_summary,
    }
