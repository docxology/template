# Search Module

> **Academic literature discovery — multi-source search, deterministic caching, full-text enrichment.**

**Location:** `infrastructure/search/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [Literature Workflow](../../guides/literature-workflow-guide.md) | [Code Review Checklist](../../development/code-review-checklist.md)

---

## Key Features

- **Backends** — `ArxivBackend`, `CrossrefBackend`, `LocalBackend`, `PaperclipBackend` behind the common `SearchBackend` protocol.
- **Client** — `LiteratureClient` orchestrates multi-backend queries, deduplication via `merge_papers`, and enrichment (`enrich_papers`).
- **Caching** — `SearchCache` writes deterministic JSON cache files; same query → identical cache key.
- **Full-text** — `AbstractFetcher`, `FulltextFetcher` retrieve abstracts and PDFs where licensing permits.
- **Corpus export** — `write_corpus()` produces a stable on-disk corpus suitable for downstream LLM synthesis.

This module is the **discovery side** of the literature workflow; the export side (BibTeX) lives in [`reference`](reference-module.md).

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
