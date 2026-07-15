# Literature Retrieval Module — Agent Directives

## Overview

Retrieval clients (arXiv, Semantic Scholar, OpenAlex, Crossref, PubMed, SovietRxiv/ChinaRxiv,
Europe PMC, bioRxiv/medRxiv), query routing, corpus management, and data models.
Orchestration lives in `literature/search_runner.py` (called from `scripts/01_literature_search.py`).
`run_literature_search(..., arxiv_base_url=..., semantic_scholar_base_url=..., openalex_base_url=..., crossref_base_url=..., pubmed_esearch_url=..., pubmed_efetch_url=..., sovietrxiv_base_url=..., chinarxiv_base_url=..., europepmc_base_url=..., biorxiv_base_url=...)`
accepts injectable API roots for `pytest-httpserver` integration tests without changing production defaults.
`query_router.py` routes queries across engines and toggles preprint preference.
`evaluation.py` reports corpus coverage, source mix, routing choice, and claim-verification summaries for the stage-07 harness.
SovietRxiv and ChinaRxiv share the same unified API (`sovietrxiv_client.py`) but are hosted at
`https://russiarxiv.org` and `https://chinaxiv.org` respectively; the `source` query parameter
distinguishes their sub-corpora.
Europe PMC (`europepmc_client.py`) is a keyless biomedical aggregator search endpoint.
bioRxiv/medRxiv (`biorxiv_client.py`) share one unified date-window + cursor `details` API at
`https://api.biorxiv.org`; the `server` parameter (`"biorxiv"` or `"medrxiv"`) selects the corpus.
Full-text reporting: `literature/fulltext_assessment.py` (`scripts/06_fulltext_assessment.py`).
The corpus JSONL is the single input
to all downstream pipeline stages.

## Invariants Agents Must Preserve

- **Injectable base URLs**: Every client (`search_arxiv`, `search_semantic_scholar`,
  `search_openalex`, `search_crossref`, `search_pubmed`, `search_sovietrxiv`, `search_europepmc`,
  `search_biorxiv`) accepts a `base_url` parameter. Tests use `pytest-httpserver` local servers
  pointed at via this parameter. Never hardcode the URL inside the function body.
- **No mock policy**: Tests in `tests/literature/` must use `pytest-httpserver` for HTTP calls,
  not `unittest.mock.patch`. The httpserver fixture starts a real local HTTP server.
- **Deduplication stability**: `Corpus.add()` keeps the version with higher `metadata_completeness`.
  The completeness score counts non-None optional fields. Do not change this strategy without
  updating the score calculation and re-validating deduplication.
- **Metadata dedupe stability**: `Corpus.deduplicate_by_metadata(prefer_preprints=...)` collapses
  title+author duplicates after relevance/year filtering. Preserve its preprint preference and
  keep the routing tests aligned if the signature changes.
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

## Adding a New Routing or Evaluation Surface

1. Add the routing or scoring logic in `src/literature/query_router.py` or `src/literature/evaluation.py`.
2. Keep script `07_literature_evaluation.py` thin: parse args, load corpus, call `evaluate_corpus`, write JSON.
3. Add tests for source ordering, preprint preference, and summary fields before widening the routing matrix.

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
| Europe PMC | No documented hard limit; be polite (~10 req/s) | Up to 1000/page (`pageSize`) | Keyless; one request per search call |
| bioRxiv/medRxiv | No documented limit; date-window + cursor paginated, keep modest | 100/page fixed, cursor | Keyless; not free-text search — date-window then client-side filter (see `biorxiv_client.py`) |

## Known Limitations

- **Semantic Scholar retry count**: ``MAX_RETRIES=3`` with 10s exponential
  backoff handles burst rate-limit windows. Previously ``MAX_RETRIES=1``
  (conservative); increased to 3 based on observed burst-window durations.
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
- **bioRxiv/medRxiv is not full-text search**: the public API exposes no query parameter —
  `search_biorxiv` walks the date window page by page and keeps only items whose title +
  abstract contain every query term. It is bounded by `BIORXIV_MAX_PAGES` (20 pages / 2000
  raw items); a query with very common terms may exhaust the page cap before `max_results`
  matches are found. Not ranked by relevance.
