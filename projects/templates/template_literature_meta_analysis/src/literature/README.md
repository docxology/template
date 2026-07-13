# Literature Retrieval Module

Multi-source corpus generation for the literature meta-analysis. Retrieves papers from
nine literature engines (arXiv, Semantic Scholar, OpenAlex, Crossref, PubMed, SovietRxiv,
ChinaRxiv, Europe PMC, bioRxiv/medRxiv), deduplicates by canonical identifier, and
persists to JSONL.

## Components

### `models.py`
Core data structures: `Paper`, `Author`, `Citation`. `Paper.canonical_id` returns the best
available identifier in priority order: DOI > arXiv ID > Semantic Scholar ID > OpenAlex ID >
SHA256(title). `Paper.metadata_completeness` counts populated optional fields — used by corpus
merge to select the richer version of duplicate papers. Serializes to/from JSON dicts.

Key fields on `Paper`:
- `title, abstract, year` — always populated
- `doi, arxiv_id, s2_id, openalex_id` — identifier cascade
- `citation_count` — used in hypothesis scoring weight `log(1 + citations)`
- `references: list[str]` — raw reference strings for citation network resolution
- `pdf_url, is_open_access` — used by full-text ingestion (future Step 2)

### `corpus.py`
`Corpus` class: dict-backed collection keyed by `paper.canonical_id`. `add(paper)` merges
with existing by keeping the version with higher `metadata_completeness`. `deduplicate_by_metadata()`
collapses normalized title+author duplicates after a multi-source run, with optional preprint
preference. `merge(other_corpus)` incorporates all papers from another corpus. JSONL persistence:
each line is a JSON-serialized `Paper.to_dict()`.

Key methods:
- `add(paper)` — deduplication merge
- `merge(other)` — in-place corpus merge
- `filter_by_year(start, end) -> Corpus`
- `filter_by_subfield(subfield) -> Corpus` — classifies on-the-fly; expensive on large corpora
- `save(path)` / `Corpus.load(path)` — JSONL I/O

### `arxiv_client.py`
Searches arXiv Atom API (`http://export.arxiv.org/api/query`). Pagination: 100 results per page.
Rate limiting: 3s between requests. Retries: 3 attempts with exponential backoff. Parses XML
Atom format; strips version suffix from arXiv IDs for deduplication canonicalization.

- `search_arxiv(query, max_results, base_url, session, rate_limit_seconds) -> list[Paper]`

### `semantic_scholar.py`
Searches Semantic Scholar Graph API (`/paper/search`). Offset pagination: 100 per page.
Retries on 429/5xx (max 2 attempts). Returns rich metadata including reference IDs for citation
network construction.

- `search_semantic_scholar(query, max_results, base_url, session) -> list[Paper]`
- `get_paper_details(paper_id, base_url, session) -> Paper`

### `openalex_client.py`
Searches OpenAlex `/works` endpoint. Cursor-based pagination: 200 per page (more robust
than offset). Reconstructs abstracts from OpenAlex inverted-index format. Parses ORCID and
DOI URL prefixes automatically.

- `search_openalex(query, max_results, base_url, session) -> list[Paper]`
- `get_work_by_doi(doi, base_url, session) -> Paper`

### `crossref_client.py`
Searches the Crossref `/works` REST endpoint (keyless, polite pool via `mailto` param).
Cursor/offset pagination depending on endpoint. Broad multidisciplinary DOI registry
covering journal articles, books, and conference proceedings.

- `search_crossref(query, max_results, base_url, session) -> list[Paper]`

### `pubmed_client.py`
Searches NCBI Entrez `esearch`/`efetch` (biomedical literature). Keyless; an optional API
key raises the NCBI usage-policy rate limit. `retstart`/`retmax` pagination.

- `search_pubmed(query, max_results, esearch_base_url, efetch_base_url, session) -> list[Paper]`

### `sovietrxiv_client.py`
Unified client for SovietRxiv/RussiaRxiv (translated Soviet-era preprints from Math-Net.Ru
and CyberLeninka) and ChinaRxiv (translated Chinese preprints from ChinaXiv) — same API,
different `source` parameter (`"russiarxiv"` or `"chinaxiv"`) and hostname. Keyless;
`api_email` activates the polite rate-limit pool (300/min vs 30/min anonymous).

- `search_sovietrxiv(query, max_results, base_url, session, api_email, source) -> list[Paper]`

### `europepmc_client.py`
Searches the Europe PMC `/search` endpoint (keyless biomedical aggregator covering PubMed,
PMC, patents, and preprints). Single-request pagination via `pageSize` (capped at 1000).

- `search_europepmc(query, max_results, base_url, session) -> list[Paper]`

### `biorxiv_client.py`
Queries the unified bioRxiv/medRxiv `details/{server}/{interval}/{cursor}/json` endpoint.
Not free-text search: walks a date window page by page (100/page, cursor-based) and keeps
only items whose title+abstract match every query term (client-side filter). `server`
selects `"biorxiv"` or `"medrxiv"`.

- `search_biorxiv(query, max_results, base_url, session, server) -> list[Paper]`

### `query_router.py`
Heuristic query router for the multi-backend search runner. Detects academic, industry, and mixed
queries; prefers preprint engines for preprint-heavy queries; and returns the engine dispatch order
across all nine engines.

- `QueryRouter.route(query, available_sources) -> QueryRoute`

### `engine_dispatch.py`
Declarative engine-enablement registry: `ENGINE_SPECS` enumerates all nine engines (name, CLI
skip-flag, config-toggle key) as a single source of truth, and `engine_enabled()` evaluates the
skip-flag / config-toggle / hermetic-injection gating for a given spec. `dispatch_ordered()` is
the piece actually wired into `search_runner.py` today — it invokes each engine's runner closure
in the query router's chosen order, skipping any key with no registered runner.

- `EngineSpec(name, skip_flag, config_key).enabled(args, engines, *, fast_api, injected) -> bool`
- `engine_enabled(spec, args, engines, *, fast_api, url_injected) -> bool`
- `dispatch_ordered(route_order, runners) -> None`

### `bibliography.py`
Unified BibTeX export: normalizes every `Paper` (regardless of source engine) into a `BibEntry`,
generates collision-free citation keys (`author+year+title-word`, disambiguated on collision),
escapes LaTeX-special characters, and renders the whole corpus to a single `.bib` file. Backs
`scripts/09_export_bibliography.py`.

- `paper_to_bibentry(paper, *, used_keys=None) -> BibEntry`
- `generate_citation_key(paper, used_keys) -> str`
- `render_entries(entries) -> str`
- `corpus_to_bibtex(corpus) -> str`

### `fulltext_download.py`
Full-text resolution, download, and extraction. Resolves open-access PDF URLs via Unpaywall
(opt-in, `unpaywall_email` config), downloads with retry, extracts plaintext and figures from
PDFs, and reports coverage/extraction statistics across the corpus. Backs
`scripts/06_fulltext_assessment.py`.

- `resolve_fulltext_url(paper, unpaywall_email, base_url, session) -> str | None`
- `download_fulltext(paper, dest_dir, session) -> Path | None`
- `extract_fulltext_text(pdf_path) -> str | None`
- `extract_figures(pdf_path, dest_dir, *, stem) -> list[Path]`
- `download_and_extract_fulltext(corpus, dest_dir, *, unpaywall_email, session) -> dict`
- `assess_fulltext_availability(papers) -> dict`
- `assess_fulltext_extraction(corpus, fulltext_dir) -> dict`

### `evaluation.py`
Corpus-level metrics and routing summary helper used by the stage-07 evaluation harness.

- `evaluate_corpus(corpus, query=None, claim_verdicts=None) -> dict`

## Deduplication Strategy

Papers are deduplicated by canonical ID across all nine sources. When the same paper appears
from multiple sources (common for preprints that also appear in Semantic Scholar, OpenAlex,
Crossref, or a biomedical aggregator), `Corpus.add()` retains the version with the highest
`metadata_completeness` score. The cascade:

```
DOI (most stable) > arXiv ID > S2 ID > OpenAlex ID > title hash (last resort)
```

SovietRxiv/ChinaRxiv expose no DOI in their unified API, so those records fall back to the
title-hash tier; they still merge correctly against a DOI-bearing duplicate from another engine
because the title hash is computed identically on both sides. Title-hash collisions are rare but
possible for very short titles. The corpus JSONL includes the source-of-record ID so
deduplication decisions can be audited.

## Output

`output/data/corpus.jsonl` — one JSON object per line, each representing a `Paper`.
`output/data/literature_evaluation.json` — corpus summary from the stage-07 evaluation harness.
`output/data/bibliography.bib` — unified BibTeX export from `scripts/09_export_bibliography.py`.
Corpus size, engine mix, and year range vary per run/topic — see the generated
`retrieval_report.json` and the manuscript's injected `{{N_ENGINES}}`/`{{CORPUS_SIZE}}`
variables for the authoritative figures of the most recent run, rather than a hand-maintained
count here.

See [AGENTS.md](AGENTS.md) for agent constraints and extension guidance.
