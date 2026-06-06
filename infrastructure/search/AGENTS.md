# Search Module

## Purpose

The Search module provides discovery utilities for academic literature
(`literature/`) and Exa-backed general web search, content extraction, and
grounded answers (`exa/` — see [`exa/README.md`](exa/README.md) and
[`exa/AGENTS.md`](exa/AGENTS.md)). The literature side sits opposite
[`infrastructure/reference/`](../reference/) in the literature workflow:

```mermaid
flowchart LR
    D[discover<br/>search] --> N[normalise<br/>Paper]
    N --> E[export<br/>citation]
    E --> PDF[PDF]

    classDef stage fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef out fill:#0f766e,stroke:#0f172a,color:#fff
    class D,N,E stage
    class PDF out
```

The module is modelled after [Paperclip](https://paperclip.gxl.ai)'s
agent-native abstractions: every backend produces normalised `Paper` records
so downstream code (citation export, manuscript synthesis, agent loops) can
treat results uniformly regardless of source.

## Architecture

### `literature/` — Multi-source literature search

| File | Role |
|---|---|
| `models.py` | `Paper`, `SearchQuery`, `SearchResult` data models, plus `merge_papers()` for DOI / arXiv-aware deduplication. |
| `base.py` | Abstract `SearchBackend` (plus `BackendError`). |
| `local_backend.py` / `crossref_backend.py` / `arxiv_backend.py` / `paperclip_backend.py` | The four concrete backends: `LocalBackend` (JSON corpus on disk), `CrossrefBackend` (Crossref REST), `ArxivBackend` (arXiv Atom export), `PaperclipBackend` (Paperclip API, opt-in). |
| `http_client.py` | The `HttpResponse` record, the `HttpClient` protocol, a stdlib-only `UrllibHttpClient`, and `HttpGetMixin` so backends have no required HTTP dependency. |
| `backends/` | Convenience re-export subpackage: `from infrastructure.search.literature.backends import SearchBackend, LocalBackend, ...`. |
| `client.py` | `LiteratureClient` — runs a query across configured backends, applies year filters defensively, deduplicates with `merge_papers`, sorts by score, caps at `query.max_results`. Per-backend errors are recorded into `result.errors`, never raised. |
| `cache.py` | `SearchCache` — JSON-file cache keyed on query identity. Pretty-printed for greppability; supports optional TTL. |
| `cli.py` | `search` / `to-bibtex` subcommands. |

### `exa/` — Exa-backed web search, contents, and grounded answers

| File | Role |
|---|---|
| `config.py` | `ExaConfig` (`EXA_API_KEY`, host, defaults). |
| `errors.py` | `ExaError`. |
| `http.py` | `ExaHttpClient` protocol, `UrllibExaHttpClient`, `ExaResponse`. |
| `models.py` | `ExaResult`, `SearchResponse`, `ContentsResponse`, `AnswerResponse`, etc. |
| `client.py` | `ExaClient` — facade over the four interfaces; `ExaClient.from_env()` reads `EXA_API_KEY`. |
| `search/` / `contents/` / `answer/` / `find_similar/` | One subpackage per interface (`POST /search`, `/contents`, `/answer`, `/findSimilar`). |
| `cli.py` | `search` / `contents` / `answer` / `find-similar` subcommands (`python -m infrastructure.search.exa`). |

See [`exa/README.md`](exa/README.md), [`exa/AGENTS.md`](exa/AGENTS.md), and
[`exa/CAPABILITIES.md`](exa/CAPABILITIES.md) for full detail.

## Key Features

### Normalised `Paper` records

```python
from infrastructure.search.literature import Paper

paper = Paper(
    id="doi:10.1126/science.1213847",
    title="Reproducible research in computational science",
    authors=["Roger D Peng"],
    year=2011,
    doi="10.1126/science.1213847",
    venue="Science", venue_type="journal",
    pages="1226-1227",
    source="crossref",
    score=0.95,
)
```

The schema is a superset of what BibTeX requires, so
`infrastructure.reference.citation.paper_to_bibentry()` can convert without
going back to the network.

### Multi-backend aggregation with failure isolation

```python
from infrastructure.search.literature import (
    LiteratureClient, SearchQuery, ArxivBackend, CrossrefBackend
)

client = LiteratureClient([ArxivBackend(), CrossrefBackend()])
result = client.search(SearchQuery(text="adam optimizer", max_results=20))

# A network outage in one backend never breaks the search:
print(result.per_source_counts)  # {"arxiv": 20, "crossref": 18}
print(result.errors)              # {} (or {"crossref": "HTTP 503"} on outage)
```

### DOI / arXiv-aware deduplication

```python
from infrastructure.search.literature import merge_papers
unique = merge_papers([*arxiv_results, *crossref_results])
```

Priority: DOI → arXiv id → normalised (title, year). Higher-scored copy
wins; missing fields on the winner are filled from the loser.

### Deterministic caching

```python
from infrastructure.search.literature import SearchCache
cache = SearchCache("output/cache", ttl_seconds=86400)
client = LiteratureClient([ArxivBackend()], cache=cache)
client.search(SearchQuery(text="x"))  # writes search_<hash>.json
client.search(SearchQuery(text="x"))  # cache hit, no network
```

Cache identity is `sha256(text.strip().lower(), max_results, year_min,
year_max, sorted(sources))[:16]` — so `"  Foo  "` and `"foo"` collide.

## Testing

```bash
uv run pytest tests/infra_tests/search/ -v
```

The test suite (71+ assertions) covers:

* `LocalBackend` against real temp files (no mocks).
* HTTP backends via `pytest-httpserver` — a real local HTTP server
  responds with canned arXiv Atom / Crossref JSON / Paperclip JSON, and we
  assert end-to-end parsing.
* `LiteratureClient` aggregator: deduplication, per-backend failure
  capture, year-filter defence, max-results capping.
* `SearchCache` round-trips, TTL expiry, hash collision behaviour.
* CLI subcommands via real subprocess + direct `main()` calls.

## Configuration

Environment variables:

* `PAPERCLIP_API_KEY` — required only for `PaperclipBackend` / the
  `--source paperclip` CLI flag. The module never reads it implicitly;
  callers must pass it through.

## Integration

The Search module is consumed by:

* Reference workflows — `paper_to_bibentry()` in
  `infrastructure.reference.citation`.
* Manuscript curation — bulk reading-list builds, related-work synthesis.
* Agent loops — the JSON cache makes prior searches replayable.

## Troubleshooting

### Cached results are stale

**Issue**: A cached query returns old results after a backend update.

**Solutions**:
- Pass `use_cache=False` to `LiteratureClient.search()` for one-off bypass.
- Pass `--no-cache` on the CLI.
- Construct `SearchCache(path, ttl_seconds=...)` to enforce expiry.
- Clear with `cache.clear()` (returns the number of entries removed).

### A backend is rate-limited

**Issue**: Crossref / arXiv returns HTTP 429 / 503.

**Solutions**:
- Pass `mailto="you@example.org"` to `CrossrefBackend(...)` for the polite pool.
- Reduce `query.max_results` to lower per-call cost.
- Use `SearchCache` so re-runs never re-hit the API.

### Paperclip backend not configured

**Issue**: `--source paperclip` exits with `PAPERCLIP_API_KEY required`.

**Solutions**:
- Sign up at <https://paperclip.gxl.ai/>, set `PAPERCLIP_API_KEY` in the
  environment (or `.env`).
- Or omit `paperclip` from `--source` and rely on `arxiv,crossref`.

### Year filter ignored

**Issue**: Results outside the year range still appear.

**Solutions**:
- The aggregator re-applies `year_min` / `year_max` even when a backend
  ignores them; if filtering still fails, the underlying records may have
  no `year` field — `Paper.matches_year(None)` defaults to True.
- Filter explicitly post-hoc:
  `[p for p in result.papers if p.year and 2010 <= p.year <= 2020]`.

### Corpus loading is slow

**Issue**: A large `LocalBackend` corpus blocks the first call.

**Solutions**:
- The corpus is cached in memory after the first load; subsequent searches
  are O(N) over the cached list.
- For very large corpora consider a separate index (out of scope for this
  module — `LocalBackend` targets curated reading lists, not full-text
  search of millions of papers).

## Best Practices

### Use `mailto` with Crossref

Crossref's polite pool offers higher rate limits when you identify yourself:

```python
CrossrefBackend(mailto=os.environ.get("CROSSREF_MAILTO", "you@example.org"))
```

### Pin reading lists with caches

Commit the contents of `output/cache/search_*.json` to your project repo
when reproducibility matters — they are deterministic, human-readable, and
diff-friendly.

### Prefer `to-bibtex` for the manuscript flow

```bash
uv run python -m infrastructure.search.literature.cli to-bibtex \
    "your topic" --source arxiv,crossref \
    --output projects/my_project/manuscript/references.bib
```

This produces a `.bib` already in the format Pandoc expects (see
`infrastructure/reference/citation/`), with citation keys in the project's
house style.

## See Also

- [README.md](README.md) — quick reference
- [SKILL.md](SKILL.md) — agent-oriented API
- [`literature/`](literature/) — submodule
- [`infrastructure/reference/`](../reference/) — export side of the workflow
