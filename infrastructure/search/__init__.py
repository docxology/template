"""Search module — discovery tools for academic literature.

This package contains tools for finding, retrieving, and aggregating
literature from external sources:

* :mod:`infrastructure.search.literature` — Paperclip-style multi-source
  literature search with arXiv, Crossref, local-corpus, and Paperclip
  backends, deterministic JSON caching, and a CLI.

The search module is the discovery side of the literature workflow; see
:mod:`infrastructure.reference.citation` for the export side.
"""

from infrastructure.search.literature import (
    AbstractFetcher,
    ArxivBackend,
    BackendError,
    CrossrefBackend,
    FetchResult,
    FulltextFetcher,
    LiteratureClient,
    LocalBackend,
    Paper,
    PaperclipBackend,
    SearchBackend,
    SearchCache,
    SearchQuery,
    SearchResult,
    enrich_papers,
    merge_papers,
    write_corpus,
)

__all__ = [
    "Paper",
    "SearchQuery",
    "SearchResult",
    "merge_papers",
    "SearchBackend",
    "LocalBackend",
    "CrossrefBackend",
    "ArxivBackend",
    "PaperclipBackend",
    "BackendError",
    "LiteratureClient",
    "SearchCache",
    "AbstractFetcher",
    "FulltextFetcher",
    "FetchResult",
    "enrich_papers",
    "write_corpus",
]
