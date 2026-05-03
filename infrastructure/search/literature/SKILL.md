---
name: infrastructure-search-literature
description: Paperclip-style multi-source literature search across arXiv, Crossref, local JSON corpora, and (opt-in) the Paperclip API. Provides Paper/SearchQuery/SearchResult data models, a LiteratureClient aggregator with per-backend failure isolation, DOI/arXiv-aware deduplication via merge_papers, deterministic JSON caching via SearchCache, an HttpClient protocol for test injection, and a CLI (search/to-bibtex). Use when finding papers by topic, building reading lists, populating references.bib from a query, or replaying a prior search reproducibly.
---

# Literature Search Submodule

Multi-source literature search modelled after
[Paperclip](https://paperclip.gxl.ai)'s agent-native abstractions.

## Quick Search

```python
from infrastructure.search.literature import (
    LiteratureClient, SearchQuery, ArxivBackend, CrossrefBackend
)

client = LiteratureClient([ArxivBackend(), CrossrefBackend(mailto="you@example.org")])
result = client.search(SearchQuery(text="protein language model fitness", max_results=20))

print(f"{len(result)} unique papers from {len(result.per_source_counts)} sources")
print(f"Errors: {result.errors}")    # {} when all backends succeeded
for paper in result.papers[:5]:
    print(f"  [{paper.score:.2f}] {paper.title} ({paper.year}) — {paper.doi or paper.url}")
```

## Backends

```python
from infrastructure.search.literature import (
    LocalBackend, ArxivBackend, CrossrefBackend, PaperclipBackend
)

# Offline / reproducible — searches a JSON corpus on disk.
local = LocalBackend("data/curated_corpus.json")

# Public APIs, no auth.
arxiv = ArxivBackend()
crossref = CrossrefBackend(mailto="you@example.org")

# Paperclip — requires API key.
import os
paperclip = PaperclipBackend(api_key=os.environ["PAPERCLIP_API_KEY"])
```

## Filters

```python
SearchQuery(
    text="adam optimizer",
    max_results=50,
    year_min=2014, year_max=2025,
    sources=["arxiv"],          # subset of configured backends
)
```

## Caching

```python
from infrastructure.search.literature import SearchCache

cache = SearchCache("output/search_cache", ttl_seconds=86400)
client = LiteratureClient([ArxivBackend()], cache=cache)

# First call hits arXiv; second is a deterministic file read.
client.search(SearchQuery(text="x"))
client.search(SearchQuery(text="x"))

# Force refresh:
client.search(SearchQuery(text="x"), use_cache=False)
```

## Deduplication

```python
from infrastructure.search.literature import merge_papers

unique = merge_papers([*result_a.papers, *result_b.papers])
```

Priority: DOI → arXiv id → normalised (title, year). Higher-scored copy
wins; missing fields on the winner are filled from the loser ("union of
evidence").

## Failure Isolation

```python
result = client.search(query)
if result.errors:
    for source, message in result.errors.items():
        log.warning("Backend %s failed: %s", source, message)
# A network outage in one backend never breaks the search; surviving
# backends still contribute results.
```

## CLI

```bash
# JSON to stdout
uv run python -m infrastructure.search.literature.cli search \
    "scaling laws" --source arxiv,crossref --max-results 10

# Direct BibTeX to a file
uv run python -m infrastructure.search.literature.cli to-bibtex \
    "GRPO hyperparameters" --source arxiv \
    --output output/grpo_refs.bib

# Cached, offline-only over a local corpus
uv run python -m infrastructure.search.literature.cli search \
    "convex" --source local --corpus data/corpus.json \
    --cache-dir output/cache
```

## Custom HTTP Client (Tests)

```python
from infrastructure.search.literature import CrossrefBackend, HttpResponse

class MyClient:
    def get(self, url, *, params=None, headers=None, timeout=10.0):
        # ... return HttpResponse(status_code=200, text=..., url=url)
        ...

backend = CrossrefBackend(http_client=MyClient())
```

The project's no-mocks policy is satisfied with `pytest-httpserver`:

```python
def test_crossref_parses_real_payload(httpserver):
    httpserver.expect_request("/works").respond_with_json(payload)
    backend = CrossrefBackend(base_url=httpserver.url_for("/works"))
    results = backend.search(SearchQuery(text="x"))
    assert len(results) > 0
```
