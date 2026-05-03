# `infrastructure/search/literature/`

Multi-source literature search with failure-isolated aggregation,
DOI/arXiv-aware deduplication, deterministic JSON caching, and abstract
/ fulltext enrichment.

```mermaid
flowchart LR
    Q[SearchQuery] --> CLIENT[LiteratureClient]
    CLIENT --> ARXIV[ArxivBackend]
    CLIENT --> CROSSREF[CrossrefBackend]
    CLIENT --> LOCAL[LocalBackend]
    CLIENT --> PAPERCLIP[PaperclipBackend]
    ARXIV --> MERGE{{merge_papers}}
    CROSSREF --> MERGE
    LOCAL --> MERGE
    PAPERCLIP --> MERGE
    MERGE --> RES[SearchResult]
    RES --> ABS[AbstractFetcher]
    RES --> FULL[FulltextFetcher]
    ABS --> ENRICHED[Enriched papers]
    FULL --> ENRICHED
    CACHE[(SearchCache)] -. read/write .- CLIENT

    classDef api fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef agg fill:#0f766e,stroke:#0f172a,color:#fff
    classDef ext fill:#7c2d12,stroke:#0f172a,color:#fff
    class Q,RES,ENRICHED api
    class CLIENT,MERGE,ABS,FULL,CACHE agg
    class ARXIV,CROSSREF,LOCAL,PAPERCLIP ext
```

## Files

| File | Role |
|---|---|
| `models.py` | `Paper`, `SearchQuery`, `SearchResult`, `merge_papers` |
| `backends.py` | `SearchBackend` ABC + 4 concrete backends + HTTP layer |
| `client.py` | `LiteratureClient` aggregator |
| `cache.py` | `SearchCache` JSON-file cache |
| `fulltext.py` | `AbstractFetcher`, `FulltextFetcher`, `enrich_papers`, `write_corpus` |
| `cli.py` | `search` / `to-bibtex` subcommands |

## Quick reference

```python
from infrastructure.search.literature import (
    LiteratureClient, SearchQuery, ArxivBackend, CrossrefBackend,
    LocalBackend, PaperclipBackend,
    AbstractFetcher, FulltextFetcher, SearchCache,
)
```

For agent-oriented API examples see [SKILL.md](SKILL.md); for invariants
and editing rules see the parent module's
[`AGENTS.md`](../AGENTS.md).
