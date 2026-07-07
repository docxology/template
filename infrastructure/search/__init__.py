"""Search module — discovery tools for literature and the web.

This package hosts independent **search interfaces**, each in its own subpackage:

* :mod:`infrastructure.search.literature` — Paperclip-style multi-source
  literature search with arXiv, Crossref, local-corpus, and Paperclip
  backends, deterministic JSON caching, and a CLI.
* :mod:`infrastructure.search.exa` — general web search, content extraction, and
  grounded answers via the Exa API (https://exa.ai), with one subpackage per
  endpoint (``search``, ``contents``, ``answer``, ``find_similar``).
* :mod:`infrastructure.search.deep_research` — provider-neutral orchestration
  over OpenAI and Gemini deep research surfaces with lazy SDK adapters.
* :mod:`infrastructure.search.connectors` — the Scientific Connector Registry
  (OpenAlex, arXiv, Semantic Scholar, CrossRef, Europe PMC, bioRxiv, UniProt,
  PDB), independent of the literature/exa/deep_research subpackages above.

The literature side is the discovery half of the citation workflow; see
:mod:`infrastructure.reference.citation` for the export side. Importing this
package (or any one subpackage, e.g. ``infrastructure.search.connectors``) is
side-effect free and does not import the other subpackages' third-party
dependencies (``defusedxml``, Exa/OpenAI/Gemini SDKs) — each name below is
resolved lazily on first attribute access via :pep:`562`. The Exa client reads
``EXA_API_KEY`` only when you call
:meth:`infrastructure.search.exa.ExaClient.from_env`.
"""

from __future__ import annotations

import importlib
from typing import Any

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
    # Deep research orchestration
    "DEFAULT_GEMINI_AGENT",
    "DEFAULT_OPENAI_MODEL",
    "DeepResearchAnalysis",
    "DeepResearchCitation",
    "DeepResearchClient",
    "DeepResearchConfig",
    "DeepResearchJobHandle",
    "DeepResearchMCPServer",
    "DeepResearchReportBundle",
    "DeepResearchRequest",
    "DeepResearchResult",
    "DeepResearchSources",
    "DeepResearchProjectContext",
    "GeminiDeepResearchError",
    "GeminiDeepResearchProvider",
    "OpenAIDeepResearchError",
    "OpenAIDeepResearchProvider",
    "build_gemini_payload",
    "build_gemini_tools",
    "build_project_deep_research_request",
    "build_openai_payload",
    "build_openai_tools",
    "collect_project_context",
    "save_deep_research_result",
    "save_deep_research_results",
]

# Maps each re-exported name to the submodule that actually defines it.
# Resolved on demand via __getattr__ so importing this package (a prerequisite
# for `infrastructure.search.connectors`, which shares none of these names)
# never eagerly pulls in exa/deep_research/literature and their dependencies.
_EXPORT_SOURCES: dict[str, str] = {
    name: "infrastructure.search.literature"
    for name in (
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
    )
}
_EXPORT_SOURCES.update({name: "infrastructure.search.exa" for name in ("ExaClient", "ExaConfig", "ExaError")})
_EXPORT_SOURCES.update(
    {
        name: "infrastructure.search.deep_research"
        for name in (
            "DEFAULT_GEMINI_AGENT",
            "DEFAULT_OPENAI_MODEL",
            "DeepResearchAnalysis",
            "DeepResearchCitation",
            "DeepResearchClient",
            "DeepResearchConfig",
            "DeepResearchJobHandle",
            "DeepResearchMCPServer",
            "DeepResearchReportBundle",
            "DeepResearchRequest",
            "DeepResearchResult",
            "DeepResearchSources",
            "DeepResearchProjectContext",
            "GeminiDeepResearchError",
            "GeminiDeepResearchProvider",
            "OpenAIDeepResearchError",
            "OpenAIDeepResearchProvider",
            "build_gemini_payload",
            "build_gemini_tools",
            "build_project_deep_research_request",
            "build_openai_payload",
            "build_openai_tools",
            "collect_project_context",
            "save_deep_research_result",
            "save_deep_research_results",
        )
    }
)


def __getattr__(name: str) -> Any:
    module_path = _EXPORT_SOURCES.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(module_path), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
