# Search Module

> **Two search interfaces: `literature/` — academic discovery (multi-source, deterministic caching, full-text enrichment); `exa/` — general web search, content extraction, and grounded answers via the Exa API.**

**Location:** `infrastructure/search/` (subpackages: `literature/`, `exa/`)
**Quick Reference:** [Modules Guide](../modules-guide.md) | [Literature Workflow](../../guides/literature-workflow-guide.md) | [Code Review Checklist](../../development/code-review-checklist.md)

---

## Key Features

- **Backends** — `ArxivBackend`, `CrossrefBackend`, `LocalBackend`, `PaperclipBackend` behind the common `SearchBackend` protocol.
- **Client** — `LiteratureClient` orchestrates multi-backend queries, deduplication via `merge_papers`, and enrichment (`enrich_papers`).
- **Caching** — `SearchCache` writes deterministic JSON cache files; same query → identical cache key.
- **Full-text** — `AbstractFetcher`, `FulltextFetcher` retrieve abstracts and PDFs where licensing permits.
- **Corpus export** — `write_corpus()` produces a stable on-disk corpus suitable for downstream LLM synthesis.

This is the **discovery side** of the literature workflow; the export side (BibTeX) lives in [`reference`](reference-module.md).

---

## Exa Web Search (`exa/`)

A self-contained, stdlib-only client for the [Exa](https://exa.ai) search API —
the general-web sibling to `literature/`. One normalised `ExaResult` record is
returned across every endpoint, so results and citations are consumed uniformly.

- **Four interfaces** — `search` (`POST /search`, neural/keyword retrieval +
  `output_schema` structured synthesis), `contents` (`POST /contents`, parsed
  text for known URLs), `answer` (`POST /answer`, grounded answer + citations),
  `find_similar` (`POST /findSimilar`, similar pages for a seed URL).
- **Construction** — `ExaClient.from_env()` reads `EXA_API_KEY` from the
  environment (never at import time; no `.env` autoload). Tests inject a
  `pytest-httpserver` transport via `base_url` — no mocks.
- **What you can extract** — ranked URLs, query-relevant highlights, full text
  (RAG), **named entities with field-level citations + confidence**
  (`output_schema` grounding), cited natural-language answers, similarity
  scores, and per-call `cost_dollars`.
- **CLI** — `python -m infrastructure.search.exa {search,contents,answer,find-similar} …`.

```python
from infrastructure.search.exa import ExaClient
client = ExaClient.from_env()
resp = client.search("vector database benchmarks", num_results=5)   # highlights by default
```

Full method reference (params, return shapes, live-confirmed examples, costs):
[`infrastructure/search/exa/CAPABILITIES.md`](../../../infrastructure/search/exa/CAPABILITIES.md).
camelCase on the wire, snake_case in Python; content keys nest under `contents`
for `/search` and `/findSimilar` but are top-level for `/contents`.

---

## Public API

```python
from infrastructure.search import (
    Paper, SearchQuery, SearchResult,
    LiteratureClient, SearchCache,
    ArxivBackend, CrossrefBackend, LocalBackend, PaperclipBackend,
    SearchBackend, BackendError,
    AbstractFetcher, FulltextFetcher, FetchResult,
    enrich_papers, merge_papers, write_corpus,
)
```

The full authoritative export list is in `infrastructure/search/__init__.py`.

---

## Usage Pattern

```python
from infrastructure.search import LiteratureClient, SearchQuery, ArxivBackend

client = LiteratureClient(backends=[ArxivBackend()])
result = client.search(SearchQuery(text="free energy principle", limit=20))
for paper in result.papers:
    print(paper.title, paper.year)
```

---

## Review Criteria Mapping

The search module is reviewed primarily against criteria 2 (Composability — backends behind a single protocol), 4 (Testability — must use `pytest-httpserver` for backend HTTP, never mocks), 5 (Validation — external responses are untrusted, validate at boundary), and 8 (Reproducibility — `SearchCache` keys must be stable across runs). See [Code Review Checklist](../../development/code-review-checklist.md).
