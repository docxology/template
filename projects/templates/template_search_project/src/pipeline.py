"""Pure orchestration of the literature pipeline.

This module wires `infrastructure.search.literature` and
`infrastructure.reference.citation` into a single function that:

1. Builds a :class:`SearchBackend` set from the project config.
2. Runs the search via :class:`LiteratureClient` with deterministic caching.
3. Optionally enriches results with abstracts / fulltext.
4. Persists a JSON corpus and a Pandoc-ready ``references.bib``.

The function returns a :class:`LiteratureRunArtifacts` record so the
calling script can locate every produced file without re-deriving paths.

There is **no LLM call here** — synthesis is a separate stage in
:mod:`template_search_project.synthesis`. Splitting them keeps this
function trivially testable without an Ollama server.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from infrastructure.reference.citation import (
    BibDatabase,
    BibEntry,
    paper_to_bibentry,
    write_bibfile,
)
from infrastructure.search.literature import (
    AbstractFetcher,
    ArxivBackend,
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
    write_corpus,
)

from .config import ProjectConfig


@dataclass
class LiteratureRunArtifacts:
    """Outputs of a single :func:`run_literature_pipeline` call.

    Attributes:
        result: The raw :class:`SearchResult`.
        corpus_path: JSON corpus file (LocalBackend-compatible).
        bibtex_path: BibTeX file written for Pandoc.
        enrichment_log: One :class:`FetchResult` per fetcher per paper.
        cache_dir: Search-cache directory used for this run, when one was
            configured.
        citation_keys: Mapping ``paper.id -> citation_key`` (collision-free).
    """

    result: SearchResult
    corpus_path: Path | None = None
    bibtex_path: Path | None = None
    enrichment_log: list[FetchResult] = field(default_factory=list)
    cache_dir: Path | None = None
    citation_keys: dict[str, str] = field(default_factory=dict)

    @property
    def papers(self) -> list[Paper]:
        """Process papers."""
        return list(self.result.papers)


def _disambiguate_citation_key(base: str, taken: set[str]) -> str:
    """Append ``a``, ``b``, …, ``z``, ``aa``, … until *base* is unique."""
    if base not in taken:
        return base
    suffix_chars = "abcdefghijklmnopqrstuvwxyz"
    # Single-letter suffixes first, then double, etc.
    for length in range(1, 4):
        from itertools import product

        for combo in product(suffix_chars, repeat=length):
            candidate = base + "".join(combo)
            if candidate not in taken:
                return candidate
    # Pathological fallback — append a numeric counter.
    counter = 1
    while f"{base}_{counter}" in taken:
        counter += 1
    return f"{base}_{counter}"


def _build_citation_keys(papers: Iterable[Paper]) -> tuple[dict[str, str], list[BibEntry]]:
    """Generate collision-free citation keys for *papers*.

    Returns the ``paper.id -> key`` mapping and the list of
    :class:`BibEntry` records ready to add to a database.

    Year backfill (intentional non-policy)
    --------------------------------------
    ``paper_to_bibentry`` is intentionally pure: it copies ``paper.year``
    verbatim and never mines ``paper.raw`` for an alternative year hint
    (e.g. via Crossref's ``published-print.date-parts`` or an arXiv
    submission timestamp). The Crossref backend already tries
    ``issued`` → ``published-print`` → ``published-online`` in that
    order during ``_item_to_paper``, so a ``Paper`` arriving here with
    ``year=None`` genuinely lacks a year in every upstream source —
    inventing one from a DOI suffix or filing date would be a
    fabrication. Such entries render correctly as
    ``[Author, n.d.]`` under natbib's authoryear style. This contract
    is pinned by ``tests/test_deep_improvements.py::TestYearBackfillContract``.
    """
    mapping: dict[str, str] = {}
    entries: list[BibEntry] = []
    taken: set[str] = set()
    for paper in papers:
        proto = paper_to_bibentry(paper)
        unique_key = _disambiguate_citation_key(proto.citation_key, taken)
        if unique_key != proto.citation_key:
            entry = paper_to_bibentry(paper, citation_key=unique_key)
        else:
            entry = proto
        mapping[paper.id] = unique_key
        taken.add(unique_key)
        entries.append(entry)
    return mapping, entries


def _serialise_enrichment_log(log: list[FetchResult]) -> list[dict[str, object]]:
    """Strip the :class:`Paper` cycle and produce a JSON-serialisable view."""
    out: list[dict[str, object]] = []
    for entry in log:
        out.append(
            {
                "paper_id": entry.paper.id,
                "status": entry.status,
                "message": entry.message,
                "path": str(entry.path) if entry.path else None,
            }
        )
    return out


def _build_backends(
    config: ProjectConfig,
    *,
    corpus_path: Path | str | None = None,
    extra_backends: Iterable[SearchBackend] = (),
) -> list[SearchBackend]:
    """Translate config sources → backend instances.

    *corpus_path* is required iff ``"local"`` is in ``config.search.sources``.
    *extra_backends* are appended verbatim (used by tests to inject fakes).
    """
    backends: list[SearchBackend] = []
    for source in config.search.sources:
        name = source.strip().lower()
        if name == "arxiv":
            backends.append(ArxivBackend())
        elif name == "crossref":
            backends.append(CrossrefBackend(mailto=config.search.crossref_mailto))
        elif name == "local":
            if corpus_path is None:
                raise ValueError("config.search.sources includes 'local' but no corpus_path was supplied")
            backends.append(LocalBackend(corpus_path))
        elif name == "paperclip":
            api_key = os.environ.get("PAPERCLIP_API_KEY", "")
            if not api_key:
                raise RuntimeError("Paperclip backend requested but PAPERCLIP_API_KEY is not set")
            backends.append(PaperclipBackend(api_key=api_key))
        else:
            raise ValueError(f"Unknown search source: {source!r}")
    backends.extend(extra_backends)
    return backends


def run_literature_pipeline(
    config: ProjectConfig,
    *,
    project_root: Path | str,
    corpus_path: Path | str | None = None,
    extra_backends: Iterable[SearchBackend] = (),
    use_cache: bool = True,
    write_outputs: bool = True,
) -> LiteratureRunArtifacts:
    """Run the configured literature pipeline.

    Args:
        config: Project configuration.
        project_root: Directory under which all relative paths are resolved.
        corpus_path: Override for the local corpus. When ``None`` and
            ``config.search.sources`` contains ``"local"``,
            ``config.search.local_corpus`` (resolved against
            *project_root*) is used.
        extra_backends: Extra :class:`SearchBackend` instances appended after
            the configured ones (tests inject fakes here).
        use_cache: Whether to read from the configured search cache. Writes
            still happen.
        write_outputs: When ``False``, skip writing the corpus and BibTeX
            files (useful for in-memory tests).

    Returns:
        :class:`LiteratureRunArtifacts` with paths and the search result.
    """
    root = Path(project_root)

    # Resolve a configured local corpus path against the project root if the
    # caller did not supply one explicitly.
    if corpus_path is None and "local" in {s.lower() for s in config.search.sources}:
        if config.search.local_corpus:
            corpus_path = (root / config.search.local_corpus).resolve()

    backends = _build_backends(
        config,
        corpus_path=corpus_path,
        extra_backends=extra_backends,
    )
    cache_dir: Path | None = None
    cache: SearchCache | None = None
    if config.search.cache_dir:
        cache_dir = (root / config.search.cache_dir).resolve()
        cache = SearchCache(cache_dir, ttl_seconds=config.search.cache_ttl_seconds)

    client = LiteratureClient(backends, cache=cache)
    query = SearchQuery(
        text=config.search.query,
        max_results=config.search.max_results,
        year_min=config.search.year_min,
        year_max=config.search.year_max,
    )
    result = client.search(query, use_cache=use_cache)

    enrichment_log: list[FetchResult] = []
    if config.enrichment.fetch_abstracts:
        abs_dir = (root / config.enrichment.abstract_cache_dir).resolve()
        fetcher = AbstractFetcher(cache_dir=abs_dir)
        for paper in result.papers:
            enrichment_log.append(fetcher.fetch(paper))
    if config.enrichment.fetch_fulltext:
        ft_dir = (root / config.enrichment.fulltext_cache_dir).resolve()
        fetcher_ft = FulltextFetcher(
            cache_dir=ft_dir,
            max_chars=config.enrichment.max_fulltext_chars,
        )
        for paper in result.papers:
            enrichment_log.append(fetcher_ft.fetch(paper))

    # Build collision-free citation keys + BibEntry records once.
    citation_keys, bib_entries = _build_citation_keys(result.papers)

    corpus_out: Path | None = None
    bibtex_out: Path | None = None
    if write_outputs:
        corpus_out = (root / "output" / "corpus.json").resolve()
        write_corpus(result.papers, corpus_out)

        db = BibDatabase()
        for entry in bib_entries:
            db.add(entry)
        bibtex_out = (root / config.references_path).resolve()
        write_bibfile(bibtex_out, db)

        # Persist a structured enrichment log so downstream stages (and CI
        # debugging) can see exactly which papers were fetched, cached, or
        # skipped without parsing free-text logs.
        if enrichment_log:
            log_path = (root / "output" / "enrichment_log.json").resolve()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(
                json.dumps(_serialise_enrichment_log(enrichment_log), indent=2),
                encoding="utf-8",
            )

    return LiteratureRunArtifacts(
        result=result,
        corpus_path=corpus_out,
        bibtex_path=bibtex_out,
        enrichment_log=enrichment_log,
        cache_dir=cache_dir,
        citation_keys=citation_keys,
    )
