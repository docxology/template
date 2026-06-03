"""Search module — discovery tools for literature and the web.

This package hosts independent **search interfaces**, each in its own subpackage:

* :mod:`infrastructure.search.literature` — Paperclip-style multi-source
  literature search with arXiv, Crossref, local-corpus, and Paperclip
  backends, deterministic JSON caching, and a CLI.
* :mod:`infrastructure.search.exa` — general web search, content extraction, and
  grounded answers via the Exa API (https://exa.ai), with one subpackage per
  endpoint (``search``, ``contents``, ``answer``, ``find_similar``).

The literature side is the discovery half of the citation workflow; see
:mod:`infrastructure.reference.citation` for the export side. Importing this
package is side-effect free — the Exa client reads ``EXA_API_KEY`` only when you
call :meth:`infrastructure.search.exa.ExaClient.from_env`.
"""

from infrastructure.search.exa import ExaClient, ExaConfig, ExaError
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
    # Exa web-search interface
    "ExaClient",
    "ExaConfig",
    "ExaError",
]
