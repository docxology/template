# Search Module

Discovery utilities for literature, scientific databases, and the web. Each
**search interface** is an independent subpackage; the literature side is modelled after
[Paperclip](https://paperclip.gxl.ai)'s agent-native abstractions.

## Submodules

| Submodule | Purpose |
|---|---|
| [`connectors`](connectors/) | Uniform registry for eight scientific databases plus the opt-in Stage 08 project workflow and normalized JSON evidence report. |
| [`literature`](literature/) | Multi-source paper search across arXiv, Crossref, local JSON corpora, and Paperclip; deterministic caching; aggregator client; CLI. |
| [`exa`](exa/) | General web search, content extraction, and grounded answers via the [Exa API](https://exa.ai). One subpackage per endpoint: [`search`](exa/search/), [`contents`](exa/contents/), [`answer`](exa/answer/), [`find_similar`](exa/find_similar/). Pure-stdlib transport, no SDK, no import-time network. |
| [`deep_research`](deep_research/) | Provider-neutral deep research orchestration over OpenAI and Gemini with lazy SDK adapters, provider selection, and normalized job/result models. |

## Exa quick start

```python
from infrastructure.search.exa import ExaClient  # needs EXA_API_KEY

client = ExaClient.from_env()
for r in client.search("Next.js route handler auth example", num_results=10).results:
    print(r.title, r.url)
```

See [`exa/README.md`](exa/README.md) for the full interface, structured-output,
and CLI reference. Canonical API docs:
<https://docs.exa.ai/reference/search-api-guide-for-coding-agents>.

## Deep research quick start

```python
from infrastructure.search.deep_research import DeepResearchClient, DeepResearchRequest

client = DeepResearchClient.from_env()
handle = client.submit(DeepResearchRequest(query="Summarize the latest deep research tooling."))
result = client.poll(handle)
print(result.output_text)
```

OpenAI and Gemini credentials are optional; the dispatcher uses whichever
provider keys are present and selects a provider based on request shape. The
provider adapters stay lazy so `infrastructure.search` remains importable when
the vendor SDKs are absent.

For project-scale runs, `build_project_deep_research_request()` packages text
artifacts from a project tree into the prompt, and
`DeepResearchClient.submit_and_wait_many()` can send one request to both
providers and return both reports. `submit_project_and_save_reports()` persists
those reports under `output/reports/deep_research/`.

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
