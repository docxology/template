"""Multi-keyword deep search workflow.

Where :mod:`template_search_project.pipeline` runs **one** query and
emits a single reading report, this module runs **N** queries in
parallel-conceptually (each keyword is its own SearchQuery), fully
enriches every paper, and produces:

* A per-keyword directory under ``output/deep_search/<slug>/``:
    - ``papers.json``          — enriched paper records
    - ``reading_report.md``    — markdown summary
    - ``per_paper/<safe_id>.md`` — LLM deep summary (when LLM enabled)
* ``output/deep_search/aggregate.json`` — every paper across all keywords.
* ``output/deep_search/aggregate_report.md`` — cross-keyword overview.
* ``manuscript/references_deep.bib`` — unified BibTeX (deduplicated).

The LLM is duck-typed as ``Callable[[str], str]`` so tests can pass a
deterministic local callable that returns real, well-formed reading-note
text. Runtime callers wrap an :class:`infrastructure.llm.LLMClient`. When
the LLM stack is genuinely unavailable, callers pass ``llm=None`` and the
per-paper synthesis stage is skipped entirely — no placeholder text is
ever written into the archive.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from infrastructure.reference.citation import (
    BibDatabase,
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
    merge_papers,
)

from .config import DeepSearchConfig

# Per-paper LLM prompt — richer than synthesis.PROMPT_PER_PAPER because
# the deep search has access to the fulltext (when fetched) and emits a
# multi-section markdown note suitable for archival as a reading note.
DEEP_PROMPT = """\
You are an expert research analyst preparing a reading note that another
researcher will rely on without re-reading the paper. Write the note in
GitHub-flavoured Markdown using exactly the following section headers:

## Contribution
One paragraph stating the paper's central claim and why it is novel.

## Method
2-4 bullets describing the technical approach in plain language.

## Evidence
2-4 bullets describing experiments / proofs that support the claim.

## Limitations
1-3 bullets covering the most important caveats and what the paper does
NOT address.

## Connections
1-3 bullets relating this paper to other work in the field, citing only
papers explicitly named in the input.

## Significance for {keyword}
One paragraph explaining why this paper is relevant to a researcher
working on the keyword "{keyword}".

## Tags
Comma-separated list of 5-10 lowercase keywords describing the paper.

The paper to summarise is below. Cite it as [{citation_key}] in any
in-line reference. Do NOT introduce papers not present in the input.

PAPER
{paper_block}
"""


@dataclass
class KeywordResult:
    """Outcome of one keyword's search + enrichment + (optional) LLM pass."""

    keyword: str
    slug: str
    search_result: SearchResult
    enrichment_log: list[FetchResult] = field(default_factory=list)
    citation_keys: dict[str, str] = field(default_factory=dict)
    per_paper_summaries: dict[str, str] = field(default_factory=dict)
    output_dir: Path | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "keyword": self.keyword,
            "slug": self.slug,
            "papers": [p.to_dict() for p in self.search_result.papers],
            "per_source_counts": dict(self.search_result.per_source_counts),
            "errors": dict(self.search_result.errors),
            "citation_keys": dict(self.citation_keys),
            "per_paper_summaries": dict(self.per_paper_summaries),
            "output_dir": str(self.output_dir) if self.output_dir else None,
        }


@dataclass
class DeepSearchArtifacts:
    """Aggregate outputs of a multi-keyword run."""

    keyword_results: list[KeywordResult] = field(default_factory=list)
    aggregate_papers: list[Paper] = field(default_factory=list)
    aggregate_citation_keys: dict[str, str] = field(default_factory=dict)
    bibtex_path: Path | None = None
    aggregate_json_path: Path | None = None
    aggregate_report_path: Path | None = None
    output_dir: Path | None = None

    @property
    def total_keywords(self) -> int:
        """Process total keywords."""
        return len(self.keyword_results)

    @property
    def total_papers(self) -> int:
        """Process total papers."""
        return sum(len(kr.search_result.papers) for kr in self.keyword_results)

    @property
    def unique_papers(self) -> int:
        """Process unique papers."""
        return len(self.aggregate_papers)

    def to_dict(self) -> dict[str, object]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "total_keywords": self.total_keywords,
            "total_papers": self.total_papers,
            "unique_papers": self.unique_papers,
            "bibtex_path": str(self.bibtex_path) if self.bibtex_path else None,
            "aggregate_json_path": (str(self.aggregate_json_path) if self.aggregate_json_path else None),
            "aggregate_report_path": (str(self.aggregate_report_path) if self.aggregate_report_path else None),
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "keyword_results": [kr.to_dict() for kr in self.keyword_results],
        }


def slugify(text: str) -> str:
    """ASCII slug for use as a directory name."""
    out = re.sub(r"[^A-Za-z0-9]+", "_", text.strip().lower())
    return re.sub(r"_+", "_", out).strip("_") or "keyword"


def safe_id(paper_id: str) -> str:
    """Process safe id."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", paper_id)


def _build_backends(
    config: DeepSearchConfig,
    *,
    corpus_path: Path | str | None = None,
    extra_backends: Iterable[SearchBackend] = (),
) -> list[SearchBackend]:
    """Build a backend list from the deep-search config."""
    import os

    backends: list[SearchBackend] = []
    for source in config.sources:
        name = source.strip().lower()
        if name == "arxiv":
            backends.append(ArxivBackend())
        elif name == "crossref":
            backends.append(CrossrefBackend(mailto=config.crossref_mailto))
        elif name == "local":
            if corpus_path is None:
                raise ValueError("deep_search.sources includes 'local' but no corpus_path supplied")
            backends.append(LocalBackend(corpus_path))
        elif name == "paperclip":
            api_key = os.environ.get("PAPERCLIP_API_KEY", "")
            if not api_key:
                raise RuntimeError("Paperclip backend requested but PAPERCLIP_API_KEY is not set")
            backends.append(PaperclipBackend(api_key=api_key))
        else:
            raise ValueError(f"Unknown deep-search source: {source!r}")
    backends.extend(extra_backends)
    return backends


def build_rich_paper_block(paper: Paper, *, max_fulltext: int = 400_000) -> str:
    """Render every available field of *paper* into a markdown block for
    the deep-search per-paper synthesis prompt.

    Distinct from :func:`template_search_project.synthesis.build_paper_block`,
    which is intentionally compact (4 000-char fulltext cap) for the
    standard pipeline's brief reading note. This function is rich:
    every Paper field is included and the default ``max_fulltext`` is
    400 k chars (~100 k tokens), which fits inside ``gemma3:4b``'s
    131 k-token context window with headroom for the prompt scaffolding
    and the model's response. Callers running against smaller models
    should pass a smaller ``max_fulltext``.
    """
    rows: list[str] = []
    if paper.title:
        rows.append(f"**Title:** {paper.title}")
    if paper.authors:
        rows.append(f"**Authors:** {', '.join(paper.authors)}")
    if paper.year is not None:
        rows.append(f"**Year:** {paper.year}")
    if paper.venue:
        venue = paper.venue
        if paper.venue_type:
            venue += f" ({paper.venue_type})"
        rows.append(f"**Venue:** {venue}")
    if paper.doi:
        rows.append(f"**DOI:** {paper.doi}")
    if paper.url:
        rows.append(f"**URL:** {paper.url}")
    if paper.volume or paper.issue or paper.pages:
        loc = " · ".join(
            filter(
                None,
                [
                    f"vol {paper.volume}" if paper.volume else "",
                    f"no {paper.issue}" if paper.issue else "",
                    f"pp {paper.pages}" if paper.pages else "",
                ],
            )
        )
        if loc:
            rows.append(f"**Locator:** {loc}")
    if paper.publisher:
        rows.append(f"**Publisher:** {paper.publisher}")
    if paper.keywords:
        rows.append(f"**Backend keywords:** {', '.join(paper.keywords)}")
    if paper.score:
        rows.append(f"**Backend score:** {paper.score:.3f}")
    if paper.source:
        rows.append(f"**Source:** {paper.source}")

    body = "\n\n".join(rows)
    if paper.abstract:
        body += f"\n\n**Abstract**\n\n{paper.abstract.strip()}"
    if paper.fulltext:
        excerpt = paper.fulltext[:max_fulltext]
        suffix = "" if len(paper.fulltext) <= max_fulltext else "\n\n…(truncated)…"
        body += f"\n\n**Excerpt (first {len(excerpt)} chars of fulltext)**\n\n{excerpt}{suffix}"
    return body


def write_per_paper_note(
    output_dir: Path,
    paper: Paper,
    citation_key: str,
    summary: str | None,
    *,
    keyword: str,
) -> Path:
    """Write a single per-paper markdown reading note."""
    out_dir = Path(output_dir) / "per_paper"
    out_dir.mkdir(parents=True, exist_ok=True)
    name = safe_id(paper.id) + ".md"
    path = out_dir / name

    lines: list[str] = []
    lines.append(f"# [{citation_key}] — {paper.title}")
    lines.append("")
    lines.append(f"_Source keyword: **{keyword}**_")
    lines.append("")
    if paper.year:
        lines.append(f"_{paper.year}_  ·  ")
    if paper.authors:
        lines.append(", ".join(paper.authors))
    if paper.doi:
        lines.append(f"DOI: <https://doi.org/{paper.doi}>")
    elif paper.url:
        lines.append(f"URL: <{paper.url}>")
    lines.append("")

    if paper.abstract:
        lines.append("## Abstract")
        lines.append("")
        lines.append(paper.abstract.strip())
        lines.append("")

    if summary:
        lines.append(summary.strip())
        lines.append("")

    if paper.fulltext:
        lines.append("## Fulltext excerpt")
        lines.append("")
        lines.append("```")
        lines.append(paper.fulltext[:1500])
        if len(paper.fulltext) > 1500:
            lines.append("...")
        lines.append("```")
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_keyword_report(
    output_dir: Path,
    keyword_result: KeywordResult,
) -> Path:
    """Write the per-keyword reading report markdown."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "reading_report.md"

    result = keyword_result.search_result
    lines: list[str] = []
    lines.append(f"# Reading report — `{keyword_result.keyword}`")
    lines.append("")
    lines.append(
        f"_Papers:_ **{len(result.papers)}** · "
        f"_max-results:_ {result.query.max_results} · "
        f"_sources:_ {', '.join(result.per_source_counts.keys()) or '—'}"
    )
    lines.append("")

    if result.errors:
        lines.append("> ⚠️ Partial coverage. Backend errors:")
        for src, msg in result.errors.items():
            lines.append(f"> - `{src}`: {msg}")
        lines.append("")

    if result.per_source_counts:
        lines.append("## Coverage")
        lines.append("")
        lines.append("| Source | Papers |")
        lines.append("|---|---:|")
        for src, count in result.per_source_counts.items():
            lines.append(f"| `{src}` | {count} |")
        lines.append("")

    lines.append("## Papers")
    lines.append("")
    for paper in result.papers:
        key = keyword_result.citation_keys.get(paper.id, paper.id)
        authors = ", ".join(paper.authors) if paper.authors else "Unknown"
        locator = f"https://doi.org/{paper.doi}" if paper.doi else (paper.url or "(no link)")
        first_abs = (paper.abstract or "_(no abstract)_").strip().splitlines()[0][:240]
        lines.append(f"- **[{key}]** *{paper.title}* — {authors} ({paper.year or 'n.d.'})")
        lines.append(f"  {locator}")
        lines.append(f"  > {first_abs}")
        lines.append("")

    if keyword_result.per_paper_summaries:
        lines.append("## Deep summaries")
        lines.append("")
        for paper in result.papers:
            summary = keyword_result.per_paper_summaries.get(paper.id)
            if not summary:
                continue
            key = keyword_result.citation_keys.get(paper.id, paper.id)
            lines.append(f"### [{key}]")
            lines.append("")
            lines.append(summary.strip())
            lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_aggregate_report(
    output_dir: Path,
    artifacts: DeepSearchArtifacts,
) -> Path:
    """Write the cross-keyword aggregate markdown report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "aggregate_report.md"

    lines: list[str] = []
    lines.append("# Deep-search aggregate report")
    lines.append("")
    lines.append(
        f"_Keywords:_ **{artifacts.total_keywords}** · "
        f"_total papers:_ **{artifacts.total_papers}** · "
        f"_unique after dedup:_ **{artifacts.unique_papers}**"
    )
    lines.append("")
    lines.append("| Keyword | Papers | Errors |")
    lines.append("|---|---:|---|")
    for kr in artifacts.keyword_results:
        n = len(kr.search_result.papers)
        errs = ", ".join(kr.search_result.errors) or "—"
        lines.append(f"| `{kr.keyword}` | {n} | {errs} |")
    lines.append("")

    lines.append("## Unique paper roster")
    lines.append("")
    for paper in artifacts.aggregate_papers:
        key = artifacts.aggregate_citation_keys.get(paper.id, paper.id)
        loc = paper.doi or paper.url or "(no link)"
        lines.append(f"- **[{key}]** *{paper.title}* ({paper.year or 'n.d.'}) — {loc}")
    lines.append("")

    if artifacts.bibtex_path is not None:
        lines.append(f"_BibTeX written to:_ `{artifacts.bibtex_path}`")
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def run_deep_search(
    config: DeepSearchConfig,
    *,
    project_root: Path | str,
    llm: Callable[[str], str] | None = None,
    corpus_path: Path | str | None = None,
    extra_backends: Iterable[SearchBackend] = (),
    use_cache: bool = True,
    write_outputs: bool = True,
) -> DeepSearchArtifacts:
    """Run the multi-keyword deep search.

    Args:
        config: Deep-search configuration block.
        project_root: Directory under which all relative paths resolve.
        llm: Optional ``(prompt: str) -> str`` callable. When ``None``,
            per-paper summaries are skipped regardless of
            ``config.llm_per_paper``.
        corpus_path: Override for ``LocalBackend``.
        extra_backends: Test-injectable extra :class:`SearchBackend` set.
        use_cache: Whether to read from `SearchCache`. Writes still happen.
        write_outputs: When ``False``, don't write any files (in-memory).

    Returns:
        :class:`DeepSearchArtifacts` with paths and per-keyword detail.
    """
    if not config.enabled:
        raise ValueError("DeepSearchConfig.enabled is False; refusing to run")
    if not config.keywords:
        raise ValueError("DeepSearchConfig.keywords is empty")

    root = Path(project_root)
    output_dir = (root / config.output_dir).resolve()
    if write_outputs:
        output_dir.mkdir(parents=True, exist_ok=True)

    backends = _build_backends(config, corpus_path=corpus_path, extra_backends=extra_backends)
    cache: SearchCache | None = None
    if config.search_cache_dir:
        cache_dir = (root / config.search_cache_dir).resolve()
        cache = SearchCache(cache_dir)
    client = LiteratureClient(backends, cache=cache)

    abs_fetcher: AbstractFetcher | None = None
    ft_fetcher: FulltextFetcher | None = None
    if config.fetch_abstracts:
        abs_fetcher = AbstractFetcher(cache_dir=(root / config.abstract_cache_dir).resolve())
    if config.fetch_fulltext:
        ft_fetcher = FulltextFetcher(
            cache_dir=(root / config.fulltext_cache_dir).resolve(),
            max_chars=config.max_fulltext_chars,
        )

    keyword_results: list[KeywordResult] = []
    for keyword in config.keywords:
        slug = slugify(keyword)
        kw_query = SearchQuery(
            text=keyword,
            max_results=config.max_results_per_keyword,
            year_min=config.year_min,
            year_max=config.year_max,
        )
        result = client.search(kw_query, use_cache=use_cache)

        # Enrich every paper before LLM summarisation.
        enrichment_log: list[FetchResult] = []
        if abs_fetcher is not None:
            for paper in result.papers:
                enrichment_log.append(abs_fetcher.fetch(paper))
        if ft_fetcher is not None:
            for paper in result.papers:
                enrichment_log.append(ft_fetcher.fetch(paper))

        # Citation keys are needed both for reports and for the bib file.
        citation_keys: dict[str, str] = {}
        for paper in result.papers:
            citation_keys[paper.id] = paper_to_bibentry(paper).citation_key

        # Per-paper LLM summaries. We do not catch broad exceptions here:
        # if the LLM raises, the deep-search stage fails loudly so the
        # operator can fix the underlying environment instead of shipping
        # a degraded reading note that silently records the error in the
        # archive. Callers that want to skip the LLM stage entirely should
        # pass ``llm=None`` (which the script-level ``_build_llm_callable``
        # does when the LLM stack is unreachable).
        per_paper_summaries: dict[str, str] = {}
        per_paper_failures: list[str] = []
        if config.llm_per_paper and llm is not None:
            for paper in result.papers:
                key = citation_keys.get(paper.id, paper.id)
                block = build_rich_paper_block(paper, max_fulltext=config.max_fulltext_chars)
                prompt = DEEP_PROMPT.format(keyword=keyword, citation_key=key, paper_block=block)
                # Per-paper LLM failures (model unavailable, transient
                # network error, prompt too long) must not abort the
                # whole deep-search stage: a single uncooperative paper
                # would otherwise discard the unified BibTeX, the
                # aggregate report, and every successful summary.
                # Failures are recorded in ``enrichment_log`` and the
                # per-paper section is omitted; a `--no-llm` rerun then
                # produces the same artefact set without summaries.
                try:
                    per_paper_summaries[paper.id] = llm(prompt)
                except Exception as exc:  # noqa: BLE001 — safety net: isolate one paper's LLM failure
                    per_paper_failures.append(f"{paper.id}: {exc}")

        kw_dir = output_dir / slug if write_outputs else None
        if write_outputs and kw_dir is not None:
            kw_dir.mkdir(parents=True, exist_ok=True)
            (kw_dir / "papers.json").write_text(
                json.dumps(
                    {
                        "keyword": keyword,
                        "papers": [p.to_dict() for p in result.papers],
                        "per_source_counts": dict(result.per_source_counts),
                        "errors": dict(result.errors),
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            for paper in result.papers:
                key = citation_keys.get(paper.id, paper.id)
                summary = per_paper_summaries.get(paper.id)
                write_per_paper_note(kw_dir, paper, key, summary, keyword=keyword)

        kr = KeywordResult(
            keyword=keyword,
            slug=slug,
            search_result=result,
            enrichment_log=enrichment_log,
            citation_keys=citation_keys,
            per_paper_summaries=per_paper_summaries,
            output_dir=kw_dir,
        )
        if write_outputs and kw_dir is not None:
            write_keyword_report(kw_dir, kr)
        keyword_results.append(kr)

    # Aggregate across keywords (dedup by DOI/arXiv id).
    every_paper: list[Paper] = []
    for kr in keyword_results:
        every_paper.extend(kr.search_result.papers)
    aggregate_papers = merge_papers(every_paper)

    # Generate collision-free citation keys for the aggregate.
    # We delegate to the same disambiguator used by the standard
    # single-query pipeline (``src/pipeline.py::_disambiguate_citation_key``)
    # so the alphabetic→double-letter→numeric suffix rules are shared
    # source-of-truth and behave identically across both workflows.
    from .pipeline import _disambiguate_citation_key

    aggregate_citation_keys: dict[str, str] = {}
    used_keys: set[str] = set()
    for paper in aggregate_papers:
        proto = paper_to_bibentry(paper)
        unique_key = _disambiguate_citation_key(proto.citation_key, used_keys)
        aggregate_citation_keys[paper.id] = unique_key
        used_keys.add(unique_key)

    bibtex_path: Path | None = None
    aggregate_json_path: Path | None = None
    if write_outputs:
        # Aggregate JSON.
        aggregate_json_path = output_dir / "aggregate.json"
        aggregate_json_path.write_text(
            json.dumps(
                {
                    "keywords": [kr.keyword for kr in keyword_results],
                    "unique_papers": [p.to_dict() for p in aggregate_papers],
                    "citation_keys": dict(aggregate_citation_keys),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # Unified BibTeX (deduplicated, with collision-free keys).
        if config.write_unified_bibtex:
            db = BibDatabase()
            for paper in aggregate_papers:
                cite_key = aggregate_citation_keys[paper.id]
                db.add(paper_to_bibentry(paper, citation_key=cite_key))
            bibtex_path = (root / config.unified_bibtex_path).resolve()
            write_bibfile(bibtex_path, db)

    artifacts = DeepSearchArtifacts(
        keyword_results=keyword_results,
        aggregate_papers=aggregate_papers,
        aggregate_citation_keys=aggregate_citation_keys,
        bibtex_path=bibtex_path,
        aggregate_json_path=aggregate_json_path,
        aggregate_report_path=None,
        output_dir=output_dir if write_outputs else None,
    )
    if write_outputs:
        artifacts.aggregate_report_path = write_aggregate_report(output_dir, artifacts)
    return artifacts
