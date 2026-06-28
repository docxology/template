# Literature Retrieval Module

Multi-source corpus generation for the literature meta-analysis. Retrieves papers from
three academic APIs, deduplicates by canonical identifier, and persists to JSONL.

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

### `query_router.py`
Heuristic query router for the multi-backend search runner. Detects academic, industry, and mixed
queries; prefers preprint engines for preprint-heavy queries; and returns the engine dispatch order.

- `QueryRouter.route(query, available_sources) -> QueryRoute`

### `evaluation.py`
Corpus-level metrics and routing summary helper used by the stage-07 evaluation harness.

- `evaluate_corpus(corpus, query=None, claim_verdicts=None) -> dict`

## Deduplication Strategy

Papers are deduplicated by canonical ID across all three sources. When the same paper appears
from multiple sources (common for arXiv preprints that also appear in S2 and OpenAlex),
`Corpus.add()` retains the version with the highest `metadata_completeness` score. The cascade:

```
DOI (most stable) > arXiv ID > S2 ID > OpenAlex ID > title hash (last resort)
```

Title-hash collisions are rare but possible for very short titles. The corpus JSONL includes
the source-of-record ID so deduplication decisions can be audited.

## Output

`output/data/corpus.jsonl` — one JSON object per line, each representing a `Paper`.
`output/data/literature_evaluation.json` — corpus summary from the stage-07 evaluation harness.
Current corpus: 849 papers from arXiv, Semantic Scholar, and OpenAlex (2005–2026).

See [AGENTS.md](AGENTS.md) for agent constraints and extension guidance.
