"""Query routing: classify a search query and select the best engine ordering.

Classifies a user's search query as ``academic``, ``industry``, or ``mixed``
based on keyword patterns, then selects a source-engine ordering that
prioritizes the engines most likely to have relevant results for that query
type. Also detects DOI and arXiv-ID patterns for exact-match routing, and
preprint-related keywords for preprint-preferring routing.

The router is a pure, stateless classifier — it does not call any engine
or touch the network. The :class:`QueryRoute` it returns is consumed by
:func:`literature.evaluation.evaluate_corpus` for the stage-07 evaluation
report and by :func:`literature.search_runner.run_literature_search` for
optional query-aware engine ordering.

All nine engines appear in every source-order tuple so that no engine is
silently excluded by routing. The ordering within each tuple is the only
thing that changes — academic queries put Crossref first (best DOI
coverage), preprint queries put arXiv first, industry queries put
Crossref first (best technical-report coverage), and mixed queries put
Semantic Scholar first (broadest interdisciplinary coverage).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

QueryType = Literal["academic", "industry", "mixed"]

_DOI_RE = re.compile(r"\b10\.\d{4,9}/\S+\b", re.IGNORECASE)
_ARXIV_RE = re.compile(r"\b\d{4}\.\d{4,5}(?:v\d+)?\b", re.IGNORECASE)

ACADEMIC_PATTERNS = (
    "peer reviewed",
    "peer-reviewed",
    "systematic review",
    "meta-analysis",
    "literature review",
    "journal",
    "published",
    "pubmed",
    "doi",
    "study",
    "trial",
    "cohort",
    "randomized",
    "scholarly",
    "conference paper",
)

INDUSTRY_PATTERNS = (
    "white paper",
    "whitepaper",
    "market report",
    "industry report",
    "technical report",
    "working paper",
    "benchmark",
    "pricing",
    "vendor",
    "product",
    "platform",
    "policy brief",
    "guidelines",
    "consulting",
    "report",
)

PREPRINT_PATTERNS = (
    "preprint",
    "arxiv",
    "biorxiv",
    "medrxiv",
    "chemrxiv",
    "working paper",
    "draft",
)

ACADEMIC_SOURCE_ORDER = (
    "crossref",
    "semantic_scholar",
    "openalex",
    "pubmed",
    "europepmc",
    "arxiv",
    "biorxiv",
    "sovietrxiv",
    "chinarxiv",
)
INDUSTRY_SOURCE_ORDER = (
    "crossref",
    "openalex",
    "semantic_scholar",
    "pubmed",
    "europepmc",
    "arxiv",
    "biorxiv",
    "sovietrxiv",
    "chinarxiv",
)
MIXED_SOURCE_ORDER = (
    "semantic_scholar",
    "openalex",
    "crossref",
    "pubmed",
    "europepmc",
    "arxiv",
    "biorxiv",
    "sovietrxiv",
    "chinarxiv",
)
PREPRINT_SOURCE_ORDER = (
    "arxiv",
    "biorxiv",
    "sovietrxiv",
    "chinarxiv",
    "semantic_scholar",
    "openalex",
    "crossref",
    "pubmed",
    "europepmc",
)


@dataclass(frozen=True)
class QueryRoute:
    """Data container for QueryRoute."""

    query_type: QueryType
    confidence: float
    matched_patterns: tuple[str, ...]
    source_order: tuple[str, ...]
    prefer_preprints: bool = False


class QueryRouter:
    """Data container for QueryRouter."""

    def route(self, query: str | None, available_sources: Sequence[str]) -> QueryRoute:
        """Process route."""
        text = (query or "").lower().strip()
        academic_hits = tuple(pattern for pattern in ACADEMIC_PATTERNS if pattern in text)
        industry_hits = tuple(pattern for pattern in INDUSTRY_PATTERNS if pattern in text)
        preprint_hits = tuple(pattern for pattern in PREPRINT_PATTERNS if pattern in text)
        exact_hits: list[str] = []
        if _DOI_RE.search(text):
            exact_hits.append("doi")
        if _ARXIV_RE.search(text):
            exact_hits.append("arxiv_id")

        query_type: QueryType
        confidence: float
        if exact_hits or preprint_hits or len(academic_hits) > len(industry_hits):
            query_type = "academic"
            confidence = min(
                0.98,
                0.55 + 0.10 * len(academic_hits) + 0.10 * len(exact_hits) + 0.05 * len(preprint_hits),
            )
        elif len(industry_hits) > len(academic_hits):
            query_type = "industry"
            confidence = min(0.95, 0.50 + 0.10 * len(industry_hits))
        else:
            query_type = "mixed"
            confidence = 0.50 + 0.05 * min(len(academic_hits) + len(industry_hits), 4)

        prefer_preprints = bool(preprint_hits or (exact_hits and "arxiv_id" in exact_hits))
        if prefer_preprints:
            source_order = PREPRINT_SOURCE_ORDER
        elif query_type == "academic":
            source_order = ACADEMIC_SOURCE_ORDER
        elif query_type == "industry":
            source_order = INDUSTRY_SOURCE_ORDER
        else:
            source_order = MIXED_SOURCE_ORDER

        available = [source.lower() for source in available_sources]
        ordered_sources = [source for source in source_order if source in available]
        ordered_sources.extend(source for source in available_sources if source.lower() not in ordered_sources)

        return QueryRoute(
            query_type=query_type,
            confidence=confidence,
            matched_patterns=tuple(exact_hits) + academic_hits + industry_hits + preprint_hits,
            source_order=tuple(ordered_sources),
            prefer_preprints=prefer_preprints,
        )
