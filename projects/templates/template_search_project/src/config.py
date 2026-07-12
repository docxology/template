"""Typed access to the project's ``manuscript/config.yaml``.

The literature workflow is driven by configuration. Tests construct a
:class:`ProjectConfig` directly; runtime callers go through
:func:`load_project_config`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SearchConfig:
    """Search-stage knobs."""

    query: str
    max_results: int = 25
    year_min: int | None = None
    year_max: int | None = None
    sources: list[str] = field(default_factory=lambda: ["arxiv", "crossref"])
    crossref_mailto: str | None = None
    paperclip: bool = False
    cache_dir: str = "output/search/cache"
    cache_ttl_seconds: int | None = None
    local_corpus: str | None = None
    """Path (relative to the project root) to a JSON corpus. Required iff
    ``"local"`` is in :attr:`sources` and no ``--corpus`` override is passed."""


@dataclass
class EnrichmentConfig:
    """Abstract / fulltext enrichment."""

    fetch_abstracts: bool = True
    fetch_fulltext: bool = False
    abstract_cache_dir: str = "output/cache/abs"
    fulltext_cache_dir: str = "output/cache/pdf"
    max_fulltext_chars: int = 200_000


@dataclass
class LLMConfig:
    """Local-Ollama synthesis knobs."""

    enabled: bool = True
    model: str = "gemma3:4b"
    temperature: float = 0.0
    seed: int = 42
    per_paper: bool = True
    corpus_synthesis: bool = True
    output_dir: str = "output/llm"
    # Passed to Ollama as num_ctx / long generation budget (see infrastructure.llm).
    context_window: int = 131_072
    long_max_tokens: int = 16_384
    max_input_length: int = 600_000
    review_timeout: float = 600.0


@dataclass
class DeepSearchConfig:
    """Knobs for the multi-keyword deep-search mode.

    Distinct from :class:`SearchConfig` (single-query mode). When
    enabled, the deep-search orchestrator iterates over every keyword,
    runs a search capped at :attr:`max_results_per_keyword`, fully
    enriches every paper, and (optionally) writes a per-paper LLM deep
    summary to :attr:`output_dir`.
    """

    enabled: bool = False
    keywords: list[str] = field(default_factory=list)
    max_results_per_keyword: int = 10
    sources: list[str] = field(default_factory=lambda: ["arxiv", "crossref"])
    year_min: int | None = None
    year_max: int | None = None
    crossref_mailto: str | None = None
    fetch_abstracts: bool = True
    fetch_fulltext: bool = True
    max_fulltext_chars: int = 200_000
    llm_per_paper: bool = True
    llm_model: str = "gemma3:4b"
    llm_seed: int = 42
    llm_temperature: float = 0.0
    output_dir: str = "output/deep_search"
    abstract_cache_dir: str = "output/cache/abs"
    fulltext_cache_dir: str = "output/cache/pdf"
    search_cache_dir: str = "output/search/cache"
    write_unified_bibtex: bool = True
    unified_bibtex_path: str = "manuscript/references_deep.bib"
    # When set, override ``ProjectConfig.llm`` for the deep-search LLM only.
    llm_context_window: int | None = None
    llm_long_max_tokens: int | None = None
    llm_max_input_length: int | None = None
    llm_review_timeout: float | None = None

    def resolve_llm_budget(self, llm: LLMConfig) -> tuple[int, int, int, float]:
        """Return (context_window, long_max_tokens, max_input_length, review_timeout)."""
        return (
            self.llm_context_window if self.llm_context_window is not None else llm.context_window,
            self.llm_long_max_tokens if self.llm_long_max_tokens is not None else llm.long_max_tokens,
            self.llm_max_input_length if self.llm_max_input_length is not None else llm.max_input_length,
            self.llm_review_timeout if self.llm_review_timeout is not None else llm.review_timeout,
        )


@dataclass
class ReportConfig:
    """Reading-report assembly."""

    output_path: str = "output/reading_report.md"
    include_per_paper: bool = True
    include_corpus_synthesis: bool = True


@dataclass
class ProjectConfig:
    """Top-level configuration for the search project."""

    title: str
    authors: list[dict[str, str]] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    search: SearchConfig = field(default_factory=lambda: SearchConfig(query=""))
    enrichment: EnrichmentConfig = field(default_factory=EnrichmentConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    deep_search: DeepSearchConfig = field(default_factory=DeepSearchConfig)
    references_path: str = "manuscript/references.bib"

    def __post_init__(self) -> None:
        if not self.search.query.strip():
            raise ValueError("ProjectConfig.search.query must be non-empty")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectConfig":
        """Build config, preferring schema-compliant project-owned settings.

        Older standalone forks stored search settings at the YAML root. Those
        keys remain readable, but new configs place them under
        ``project_config`` so the shared Layer-1 loader can validate without
        unknown-key warnings.
        """
        paper = data.get("paper", {}) or {}
        project_raw = data.get("project_config", {}) or {}
        if not isinstance(project_raw, dict):
            raise ValueError("project_config must be a YAML mapping")
        search_raw = project_raw.get("search", data.get("search", {})) or {}
        enrich_raw = project_raw.get("enrichment", data.get("enrichment", {})) or {}
        llm_raw = data.get("llm", {}) or {}
        report_raw = data.get("report", {}) or {}
        deep_search_raw = project_raw.get("deep_search", data.get("deep_search", {})) or {}
        references_path = project_raw.get("references_path", data.get("references_path"))

        return cls(
            title=str(paper.get("title") or "Literature Search Project"),
            authors=list(data.get("authors") or []),
            keywords=list(data.get("keywords") or []),
            search=SearchConfig(
                query=str(search_raw.get("query") or ""),
                max_results=int(search_raw.get("max_results", 25)),
                year_min=_optional_int(search_raw.get("year_min")),
                year_max=_optional_int(search_raw.get("year_max")),
                sources=list(search_raw.get("sources") or ["arxiv", "crossref"]),
                crossref_mailto=search_raw.get("crossref_mailto"),
                paperclip=bool(search_raw.get("paperclip", False)),
                cache_dir=str(search_raw.get("cache_dir") or "output/search/cache"),
                cache_ttl_seconds=_optional_int(search_raw.get("cache_ttl_seconds")),
                local_corpus=(str(search_raw["local_corpus"]) if search_raw.get("local_corpus") else None),
            ),
            enrichment=EnrichmentConfig(
                fetch_abstracts=bool(enrich_raw.get("fetch_abstracts", True)),
                fetch_fulltext=bool(enrich_raw.get("fetch_fulltext", False)),
                abstract_cache_dir=str(enrich_raw.get("abstract_cache_dir") or "output/cache/abs"),
                fulltext_cache_dir=str(enrich_raw.get("fulltext_cache_dir") or "output/cache/pdf"),
                max_fulltext_chars=int(enrich_raw.get("max_fulltext_chars", 200_000)),
            ),
            llm=LLMConfig(
                enabled=bool(llm_raw.get("enabled", True)),
                model=str(llm_raw.get("model") or "gemma3:4b"),
                temperature=float(llm_raw.get("temperature", 0.0)),
                seed=int(llm_raw.get("seed", 42)),
                per_paper=bool(llm_raw.get("per_paper", True)),
                corpus_synthesis=bool(llm_raw.get("corpus_synthesis", True)),
                output_dir=str(llm_raw.get("output_dir") or "output/llm"),
                context_window=int(llm_raw.get("context_window", 131_072)),
                long_max_tokens=int(llm_raw.get("long_max_tokens", 16_384)),
                max_input_length=int(llm_raw.get("max_input_length", 600_000)),
                review_timeout=float(llm_raw.get("review_timeout", 600.0)),
            ),
            report=ReportConfig(
                output_path=str(report_raw.get("output_path") or "output/reading_report.md"),
                include_per_paper=bool(report_raw.get("include_per_paper", True)),
                include_corpus_synthesis=bool(report_raw.get("include_corpus_synthesis", True)),
            ),
            deep_search=_parse_deep_search(deep_search_raw),
            references_path=str(references_path or "manuscript/references.bib"),
        )


def _parse_deep_search(raw: dict[str, Any]) -> DeepSearchConfig:
    return DeepSearchConfig(
        enabled=bool(raw.get("enabled", False)),
        keywords=list(raw.get("keywords") or []),
        max_results_per_keyword=int(raw.get("max_results_per_keyword", 10)),
        sources=list(raw.get("sources") or ["arxiv", "crossref"]),
        year_min=_optional_int(raw.get("year_min")),
        year_max=_optional_int(raw.get("year_max")),
        crossref_mailto=raw.get("crossref_mailto"),
        fetch_abstracts=bool(raw.get("fetch_abstracts", True)),
        fetch_fulltext=bool(raw.get("fetch_fulltext", True)),
        max_fulltext_chars=int(raw.get("max_fulltext_chars", 200_000)),
        llm_per_paper=bool(raw.get("llm_per_paper", True)),
        llm_model=str(raw.get("llm_model") or "gemma3:4b"),
        llm_seed=int(raw.get("llm_seed", 42)),
        llm_temperature=float(raw.get("llm_temperature", 0.0)),
        output_dir=str(raw.get("output_dir") or "output/deep_search"),
        abstract_cache_dir=str(raw.get("abstract_cache_dir") or "output/cache/abs"),
        fulltext_cache_dir=str(raw.get("fulltext_cache_dir") or "output/cache/pdf"),
        search_cache_dir=str(raw.get("search_cache_dir") or "output/search/cache"),
        write_unified_bibtex=bool(raw.get("write_unified_bibtex", True)),
        unified_bibtex_path=str(raw.get("unified_bibtex_path") or "manuscript/references_deep.bib"),
        llm_context_window=_optional_int(raw.get("llm_context_window")),
        llm_long_max_tokens=_optional_int(raw.get("llm_long_max_tokens")),
        llm_max_input_length=_optional_int(raw.get("llm_max_input_length")),
        llm_review_timeout=(float(raw["llm_review_timeout"]) if raw.get("llm_review_timeout") is not None else None),
    )


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def load_project_config(path: Path | str) -> ProjectConfig:
    """Load a :class:`ProjectConfig` from *path* (YAML)."""
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config {path} must be a YAML mapping at the top level")
    return ProjectConfig.from_dict(data)
