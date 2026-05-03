# Search Module

Discovery utilities for academic literature, modelled after
[Paperclip](https://paperclip.gxl.ai)'s agent-native abstractions.

## Submodules

| Submodule | Purpose |
|---|---|
| [`literature`](literature/) | Multi-source paper search across arXiv, Crossref, local JSON corpora, and Paperclip; deterministic caching; aggregator client; CLI. |

## Quick Start

```python
from infrastructure.search.literature import (
    LiteratureClient, SearchQuery, ArxivBackend, CrossrefBackend
)

client = LiteratureClient([ArxivBackend(), CrossrefBackend(mailto="you@example.org")])
result = client.search(SearchQuery(text="protein language model fitness", max_results=10))

for paper in result.papers:
    print(f"{paper.title} ({paper.year}) — {paper.doi or paper.url}")
```

## CLI

```bash
# Search and emit JSON
uv run python -m infrastructure.search.literature.cli search \
    "scaling laws" --source arxiv,crossref -n 20

# Search and emit BibTeX directly
uv run python -m infrastructure.search.literature.cli to-bibtex \
    "GRPO hyperparameters" --source arxiv -o output/grpo.bib
```

## Backends

| Backend | Auth | Notes |
|---|---|---|
| `LocalBackend` | none | Searches a JSON corpus on disk; ideal for offline / reproducible runs. |
| `ArxivBackend` | none | Hits the arXiv export API (Atom XML). |
| `CrossrefBackend` | none | Hits the Crossref REST API; pass `mailto=` for the polite pool. |
| `PaperclipBackend` | API key | Requires `PAPERCLIP_API_KEY`; off by default. |

All HTTP backends accept an injectable `http_client`, so tests use
`pytest-httpserver` instead of mocks (project's no-mocks policy).

## Caching

```python
from infrastructure.search.literature import SearchCache

cache = SearchCache("output/cache", ttl_seconds=86400)
client = LiteratureClient([ArxivBackend()], cache=cache)
```

Cache files are pretty-printed JSON named by a deterministic hash of the
query, so they're greppable and version-control-friendly.

## Integration with Citation Export

```python
from infrastructure.reference.citation import paper_to_bibentry, write_bibfile
from infrastructure.reference.citation.models import BibDatabase

db = BibDatabase()
for paper in result.papers:
    db.add(paper_to_bibentry(paper))
write_bibfile("references.bib", db)
```

## Testing

```bash
uv run pytest tests/infra_tests/search/ -v
```

71+ tests, no mocks: `pytest-httpserver` for HTTP, real temp files for
local-corpus tests, real subprocess invocation for the CLI.

See [SKILL.md](SKILL.md) for the agent-oriented API and [AGENTS.md](AGENTS.md)
for architecture / troubleshooting.
