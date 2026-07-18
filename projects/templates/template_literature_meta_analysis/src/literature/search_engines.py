"""Configuration-bound search callables for the literature engines.

The runner owns orchestration and provenance; this module owns the small
adapter layer that turns each provider client into a common callable shape.
Imports remain local to each factory so optional provider dependencies stay
isolated from offline corpus and replay paths.
"""

from __future__ import annotations

from collections.abc import Callable

from literature.models import Paper


def _fast_delay() -> Callable[[float], None]:
    """Return a no-op delay for hermetic HTTP fixtures."""
    return lambda _seconds: None


def arxiv_search_fn(base_url: str | None, *, fast: bool) -> Callable[..., list[Paper]]:
    """Build an arXiv search callable."""
    from literature.arxiv_client import ARXIV_API_URL, DEFAULT_RATE_LIMIT_SECONDS, search_arxiv

    url = base_url or ARXIV_API_URL
    delay = _fast_delay() if fast else None
    rate_limit = 0.0 if fast else DEFAULT_RATE_LIMIT_SECONDS

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(
            search_arxiv(
                query,
                max_results=max_results,
                base_url=url,
                rate_limit_seconds=rate_limit,
                delay_override=delay,
            )
        )

    return _search


def semantic_scholar_search_fn(base_url: str | None, *, fast: bool) -> Callable[..., list[Paper]]:
    """Build a Semantic Scholar search callable."""
    from literature.semantic_scholar import S2_API_URL, search_semantic_scholar

    url = base_url or S2_API_URL
    delay = _fast_delay() if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(search_semantic_scholar(query, max_results=max_results, base_url=url, delay_override=delay))

    return _search


def openalex_search_fn(base_url: str | None, *, fast: bool) -> Callable[..., list[Paper]]:
    """Build an OpenAlex search callable."""
    from literature.openalex_client import OPENALEX_API_URL, search_openalex

    url = base_url or OPENALEX_API_URL
    delay = _fast_delay() if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(search_openalex(query, max_results=max_results, base_url=url, delay_override=delay))

    return _search


def crossref_search_fn(base_url: str | None, *, fast: bool) -> Callable[..., list[Paper]]:
    """Build a Crossref search callable."""
    from literature.crossref_client import CROSSREF_API_URL, search_crossref

    url = base_url or CROSSREF_API_URL
    delay = 0.0 if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(search_crossref(query, max_results=max_results, base_url=url, delay_override=delay))

    return _search


def pubmed_search_fn(
    esearch_url: str | None,
    efetch_url: str | None,
    *,
    fast: bool,
) -> Callable[..., list[Paper]]:
    """Build a PubMed search callable."""
    from literature.pubmed_client import PUBMED_EFETCH_URL, PUBMED_ESEARCH_URL, search_pubmed

    es = esearch_url or PUBMED_ESEARCH_URL
    ef = efetch_url or PUBMED_EFETCH_URL
    delay = 0.0 if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(search_pubmed(query, max_results=max_results, esearch_url=es, efetch_url=ef, delay_override=delay))

    return _search


def sovietrxiv_search_fn(
    base_url: str | None,
    *,
    fast: bool,
    api_email: str | None = None,
    source: str | None = None,
) -> Callable[..., list[Paper]]:
    """Build a SovietRxiv or ChinaRxiv search callable."""
    from literature.sovietrxiv_client import SOVIETRXIV_API_URL, search_sovietrxiv

    url = base_url or SOVIETRXIV_API_URL
    delay = 0.0 if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(
            search_sovietrxiv(
                query,
                max_results=max_results,
                base_url=url,
                api_email=api_email,
                source=source,
                delay_override=delay,
            )
        )

    return _search


def europepmc_search_fn(base_url: str | None, *, fast: bool) -> Callable[..., list[Paper]]:
    """Build an Europe PMC search callable."""
    from literature.europepmc_client import EUROPEPMC_API_URL, search_europepmc

    url = base_url or EUROPEPMC_API_URL
    delay = 0.0 if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(search_europepmc(query, max_results=max_results, base_url=url, delay_override=delay))

    return _search


def biorxiv_search_fn(
    base_url: str | None,
    *,
    fast: bool,
    server: str = "biorxiv",
) -> Callable[..., list[Paper]]:
    """Build a bioRxiv or medRxiv search callable."""
    from literature.biorxiv_client import BIORXIV_API_URL, search_biorxiv

    url = base_url or BIORXIV_API_URL
    delay = 0.0 if fast else None

    def _search(query: str, max_results: int = 100) -> list[Paper]:
        return list(
            search_biorxiv(
                query,
                max_results=max_results,
                base_url=url,
                delay_override=delay,
                server=server,
            )
        )

    return _search


__all__ = [
    "arxiv_search_fn",
    "biorxiv_search_fn",
    "crossref_search_fn",
    "europepmc_search_fn",
    "openalex_search_fn",
    "pubmed_search_fn",
    "semantic_scholar_search_fn",
    "sovietrxiv_search_fn",
]
