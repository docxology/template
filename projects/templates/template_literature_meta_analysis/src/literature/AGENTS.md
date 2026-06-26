# Literature Retrieval Module — Agent Directives

## Overview

Retrieval clients (arXiv, Semantic Scholar, OpenAlex, Crossref, PubMed, SovietRxiv/ChinaRxiv) plus corpus management and data models.
Orchestration lives in `literature/search_runner.py` (called from `scripts/01_literature_search.py`).
`run_literature_search(..., arxiv_base_url=..., semantic_scholar_base_url=..., openalex_base_url=..., crossref_base_url=..., pubmed_esearch_url=..., pubmed_efetch_url=..., sovietrxiv_base_url=..., chinarxiv_base_url=...)`
accepts injectable API roots for `pytest-httpserver` integration tests without changing production defaults.
SovietRxiv and ChinaRxiv share the same unified API (`sovietrxiv_client.py`) but are hosted at
`https://russiarxiv.org` and `https://chinaxiv.org` respectively; the `source` query parameter
distinguishes their sub-corpora.
Full-text reporting: `literature/fulltext_assessment.py` (`scripts/06_fulltext_assessment.py`).
The corpus JSONL is the single input
to all downstream pipeline stages.

## Invariants Agents Must Preserve

- **Injectable base URLs**: Every client (`search_arxiv`, `search_semantic_scholar`,
  `search_openalex`, `search_crossref`, `search_pubmed`, `search_sovietrxiv`) accepts a
  `base_url` parameter. Tests use `pytest-httpserver` local servers pointed at via this
  parameter. Never hardcode the URL inside the function body.
- **No mock policy**: Tests in `tests/literature/` must use `pytest-httpserver` for HTTP calls,
  not `unittest.mock.patch`. The httpserver fixture starts a real local HTTP server.
- **Deduplication stability**: `Corpus.add()` keeps the version with higher `metadata_completeness`.
  The completeness score counts non-None optional fields. Do not change this strategy without
  updating the score calculation and re-validating deduplication.
- **citation_count ≥ 0**: The hypothesis scoring weight `log(1 + citations)` is undefined for
  negative citation counts. API responses can occasionally return `null` — the parser defaults
  to 0 in that case. Never pass negative values to `Assertion.citation_count`.
- **JSONL format stability**: Each line of `corpus.jsonl` is a `Paper.to_dict()` JSON object.
  Adding or removing `Paper` fields requires updating `Paper.from_dict()` to handle both old
  and new format (backward compatibility via `.get()` with defaults).

## Adding a New Literature Source

1. Create `src/literature/new_source_client.py` with:
   - A `search_new_source(query, max_results, base_url, session) -> list[Paper]` function
   - Injectable `base_url` parameter for hermetic tests
   - Rate limiting (check provider's terms of service)
   - Retry on 429/5xx
2. Add a `pytest-httpserver` test in `tests/literature/test_new_source_client.py`.
3. Wire the client from `literature/search_runner.py` (not directly in the script).
4. Update this file and `README.md`.

## Rate Limits and API Policies

| Source | Rate limit | Pagination | Notes |
|---|---|---|---|
| arXiv | 3s between requests | 100/page, offset | Free; no auth |
| Semantic Scholar | 1 req/s (unauthenticated) | 100/page, offset | Auth header boosts quota |
| OpenAlex | Polite pool (mailto param) | 200/page, cursor | Cursor more reliable than offset |
| Crossref | Polite pool encouraged | cursor/offset by endpoint | No key required |
| PubMed | NCBI usage policy | retstart/retmax | API key optional |
| SovietRxiv | 30/min anonymous, 300/min polite | 1–100/page, cursor | Keyless; `X-API-Email` header for polite pool |
| ChinaRxiv | 30/min anonymous, 300/min polite | 1–100/page, cursor | Keyless; same unified API as SovietRxiv |

## Known Limitations

- **Semantic Scholar single retry**: `MAX_RETRIES=1` is conservative; burst rate-limit
  windows may require 2–3 retries. Consider increasing to 3.
- **Inverted index gaps**: OpenAlex abstract reconstruction assumes dense position indices.
  Sparse indices (0, 5, 10...) produce gaps in the abstract string; no validation exists.
- **Title hash collisions**: Fallback ID `sha256(title.lower().strip())` is truncated to
  16 chars. Collision probability is negligible for typical corpus sizes (< 10,000 papers)
  but should not be relied upon for exact identity.
- **SovietRxiv/ChinaRxiv no DOIs**: The unified API does not expose DOIs in the
  `PaperSummary` schema. Records deduplicate via the `title:` fallback hash, so the same
  paper from both SovietRxiv and ChinaRxiv (or from Crossref/PubMed with a matching title)
  will collapse correctly, but DOI-based dedup is not possible for these engines.
- **SovietRxiv/ChinaRxiv citation counts**: The API does not provide citation counts.
  All records from these engines default to `citation_count=0`, so they do not contribute
  to citation-weighted hypothesis scoring.
