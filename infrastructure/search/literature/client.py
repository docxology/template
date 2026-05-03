"""Aggregator client over multiple literature-search backends.

The :class:`LiteratureClient` runs a :class:`SearchQuery` against every
configured backend (filtered by ``query.sources`` if non-empty), merges the
results with :func:`infrastructure.search.literature.models.merge_papers`,
re-applies year filters defensively, and re-ranks by score.

Per-backend errors are captured into :attr:`SearchResult.errors` rather than
raised so a single offline source never breaks a search.
"""

from __future__ import annotations

from typing import Iterable

from infrastructure.core.logging.utils import get_logger
from infrastructure.search.literature.backends import BackendError, SearchBackend
from infrastructure.search.literature.cache import SearchCache
from infrastructure.search.literature.models import (
    Paper,
    SearchQuery,
    SearchResult,
    merge_papers,
)

logger = get_logger(__name__)


class LiteratureClient:
    """Run a :class:`SearchQuery` across multiple :class:`SearchBackend`s.

    Args:
        backends: Iterable of backend instances. Iteration order is
            preserved — earlier backends contribute records first, which
            biases tie-breaks during deduplication.
        cache: Optional :class:`SearchCache` for deterministic replay.
    """

    def __init__(
        self,
        backends: Iterable[SearchBackend],
        *,
        cache: SearchCache | None = None,
    ) -> None:
        self.backends: list[SearchBackend] = list(backends)
        self.cache = cache

    def search(self, query: SearchQuery, *, use_cache: bool = True) -> SearchResult:
        """Execute *query*. Returns aggregated, deduplicated results."""
        if use_cache and self.cache is not None:
            cached = self.cache.get(query)
            if cached is not None:
                logger.debug("Cache hit for query %r", query.text)
                return cached

        result = self._search_uncached(query)

        if self.cache is not None:
            self.cache.put(result)
        return result

    def _search_uncached(self, query: SearchQuery) -> SearchResult:
        wanted_sources = {s.lower() for s in (query.sources or [])}
        all_papers: list[Paper] = []
        per_source_counts: dict[str, int] = {}
        errors: dict[str, str] = {}

        for backend in self.backends:
            if wanted_sources and backend.name.lower() not in wanted_sources:
                continue
            try:
                papers = backend.search(query)
            except BackendError as exc:
                errors[backend.name] = str(exc)
                logger.warning("Backend %s failed: %s", backend.name, exc)
                continue
            per_source_counts[backend.name] = len(papers)
            for paper in papers:
                if paper.source is None:
                    paper.source = backend.name
                if query.matches_year(paper.year):
                    all_papers.append(paper)

        merged = merge_papers(all_papers)
        merged.sort(key=_rank_key, reverse=True)
        if len(merged) > query.max_results:
            merged = merged[: query.max_results]

        return SearchResult(
            query=query,
            papers=merged,
            per_source_counts=per_source_counts,
            errors=errors,
        )


def _rank_key(paper: Paper) -> tuple[float, int]:
    """Sort key for ranking merged results: score desc, then year desc."""
    return (paper.score, paper.year or 0)
