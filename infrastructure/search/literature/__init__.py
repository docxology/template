"""Literature search submodule.

Public API:

* :class:`Paper`, :class:`SearchQuery`, :class:`SearchResult` — normalised
  result schema.
* :func:`merge_papers` — DOI/arXiv-aware deduplication.
* :class:`SearchBackend`, :class:`LocalBackend`, :class:`CrossrefBackend`,
  :class:`ArxivBackend`, :class:`PaperclipBackend` — pluggable backends.
* :class:`HttpClient`, :class:`UrllibHttpClient`, :class:`HttpResponse`,
  :class:`BackendError` — HTTP abstraction (so tests can use
  ``pytest-httpserver`` instead of mocks).
* :class:`LiteratureClient` — multi-backend aggregator.
* :class:`SearchCache` — JSON-file cache.
"""

from __future__ import annotations

from infrastructure.search.literature.backends import (
    ArxivBackend,
    BackendError,
    CrossrefBackend,
    HttpClient,
    HttpResponse,
    LocalBackend,
    PaperclipBackend,
    SearchBackend,
    UrllibHttpClient,
)
from infrastructure.search.literature.cache import SearchCache
from infrastructure.search.literature.client import LiteratureClient
from infrastructure.search.literature.fulltext import (
    AbstractFetcher,
    FetchResult,
    FulltextFetcher,
    enrich_papers,
    write_corpus,
)
from infrastructure.search.literature.models import (
    Paper,
    SearchQuery,
    SearchResult,
    merge_papers,
)

__all__ = [
    # Models
    "Paper",
    "SearchQuery",
    "SearchResult",
    "merge_papers",
    # Backends
    "SearchBackend",
    "LocalBackend",
    "CrossrefBackend",
    "ArxivBackend",
    "PaperclipBackend",
    # HTTP layer
    "HttpClient",
    "UrllibHttpClient",
    "HttpResponse",
    "BackendError",
    # Aggregator + cache
    "LiteratureClient",
    "SearchCache",
    # Fulltext + enrichment
    "AbstractFetcher",
    "FulltextFetcher",
    "FetchResult",
    "enrich_papers",
    "write_corpus",
]
