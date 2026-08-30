---
name: infrastructure-search
description: Discovery utilities. Hosts subpackages — `literature` for Paperclip-style multi-source academic search; `exa` for Exa-backed web search, contents, answers, and find-similar; `monid` for the Monid gateway (discover/inspect/run) plus offline USD-per-1k search API pricing; and `deep_research` for provider-neutral long-running research over OpenAI and Gemini (PAID). Use when finding papers, running web search, comparing search API costs, routing agent tasks through Monid, or dispatching manuscript deep-research reviews.
---

# Search Module

Discovery utilities for academic literature, modelled after the
agent-native abstractions of [Paperclip](https://paperclip.gxl.ai): every
backend produces normalised `Paper` records that downstream consumers
(citation export, manuscript synthesis, agent loops) can treat uniformly.

## `literature` — Multi-source literature search

```python
from infrastructure.search.literature import (
    Paper, SearchQuery, SearchResult, merge_papers,
    SearchBackend, LocalBackend, CrossrefBackend, ArxivBackend, PaperclipBackend,
    LiteratureClient, SearchCache,
    HttpClient, UrllibHttpClient, HttpResponse, BackendError,
)
```

### Search across arXiv + Crossref

```python
client = LiteratureClient([ArxivBackend(), CrossrefBackend(mailto="you@example.org")])
result = client.search(SearchQuery(text="protein language model fitness", max_results=20))
print(f"{len(result)} unique papers from {len(result.per_source_counts)} backends")
for paper in result.papers[:5]:
    print(f"  [{paper.score:.2f}] {paper.title} ({paper.year})  {paper.doi or paper.url}")
```

### Search a local JSON corpus (offline-friendly)

```python
backend = LocalBackend("data/curated_corpus.json")
result = LiteratureClient([backend]).search(SearchQuery(text="convex"))
```

Corpus format — either a list of `Paper` dicts or `{"papers": [...]}`:

```json
[
  {
    "id": "doi:10.1126/science.1213847",
    "title": "Reproducible research in computational science",
    "authors": ["Roger D Peng"],
    "year": 2011,
    "doi": "10.1126/science.1213847",
    "venue": "Science", "venue_type": "journal"
  }
]
```

### Search Paperclip (API key required)

```python
import os
backend = PaperclipBackend(api_key=os.environ["PAPERCLIP_API_KEY"])
result = LiteratureClient([backend]).search(
    SearchQuery(text="GRPO hyperparameters", sources=["arxiv"], max_results=50)
)
```

### Cache results for reproducibility

```python
cache = SearchCache("output/search_cache", ttl_seconds=3600 * 24)
client = LiteratureClient([ArxivBackend(), CrossrefBackend()], cache=cache)

# First call hits the network and writes search_<hash>.json.
client.search(SearchQuery(text="adam optimizer"))
# Re-running the identical query is a deterministic file read.
client.search(SearchQuery(text="adam optimizer"))
```

### Merge / deduplicate results manually

```python
from infrastructure.search.literature import merge_papers
unique = merge_papers(result_a.papers + result_b.papers)
```

Deduplication priority: DOI → arXiv id → normalised (title, year). Higher
`score` wins; missing fields on the winner are filled from the loser
("union of evidence").

### CLI

```bash
# JSON to stdout
uv run python -m infrastructure.search.literature.cli search \
    "scaling laws" --source arxiv,crossref --max-results 10

# Direct BibTeX to a file
uv run python -m infrastructure.search.literature.cli to-bibtex \
    "GRPO hyperparameters" \
    --source arxiv \
    --output output/grpo_refs.bib

# Cached, offline-only over a local corpus
uv run python -m infrastructure.search.literature.cli search \
    "convex" --source local --corpus data/corpus.json \
    --cache-dir output/cache
```

## `exa` — Web search, contents, answers, find-similar

General web search, content extraction, and grounded answers via the
[Exa](https://exa.ai) API. The client never reads the environment at import
time — construct it explicitly. See [`exa/README.md`](exa/README.md) for the
full reference.

```bash
export EXA_API_KEY="YOUR_API_KEY"   # keys: https://dashboard.exa.ai/api-keys
```

```python
from infrastructure.search.exa import ExaClient

client = ExaClient.from_env()  # or ExaClient(ExaConfig(api_key=...)) for tests

resp = client.search("Next.js route handler authentication example", num_results=10)
for r in resp.results:
    print(r.title, r.url)

client.contents(["https://example.com/post"], text=True)   # parsed content for known URLs
client.answer("What is retrieval-augmented generation?")    # grounded answer + citations
client.find_similar("https://example.com/post")             # similar pages for a seed URL
```

### CLI

```bash
uv run python -m infrastructure.search.exa search "scaling laws" --num-results 10
uv run python -m infrastructure.search.exa contents "https://example.com/post" --text
uv run python -m infrastructure.search.exa answer "What is RAG?"
uv run python -m infrastructure.search.exa find-similar "https://example.com/post"
```

## `monid` — Gateway to hundreds of data endpoints (PAID)

Monid routes agent tasks to third-party endpoints through one wallet. Python
client: `MonidClient`; repository workflow:
[`monid/SKILL.md`](monid/SKILL.md). The separate upstream Monid skill is not
placed under `.agents/skills/`, whose complete tree is pinned to the declared
context-engineering source.

```python
from infrastructure.search.monid import MonidClient, format_pricing_table

client = MonidClient.from_env()
for hit in client.discover("web search", limit=5).results:
    print(hit.provider, hit.price)
print(format_pricing_table())  # offline USD/1k for Exa, Brave, Tavily, Serper, …
```

Direct search API list prices are maintained in
[`monid/PRICING.md`](monid/PRICING.md) (review date in
[`pricing.py`](monid/pricing.py)). Monid gateway pricing is per-endpoint —
always `inspect` before `run`.

## `deep_research` — Manuscript-scale research reports (PAID)

Provider-neutral dispatch to OpenAI `o3-deep-research` and Gemini deep
research. Packages a project's `manuscript/` sources (plus rendered outputs
when present) into the prompt; returns full reports with citations and saves
them under `output/reports/deep_research/`. Live-verified end-to-end
2026-06-10 on the Active Inference exemplar (report with 4 new DOI-backed
citations + section-by-section fixes).

**Costs real money** — measured: ≈ $2/report (OpenAI, `max_tool_calls=12`),
≈ $25/report (Gemini, ~9.3M-token agentic loop). Budget a 9-exemplar loop at
≈ $20 OpenAI-only. Full cost model, budget knobs, and the multi-project loop
recipe: [`deep_research/README.md`](deep_research/README.md); operating rules:
[`deep_research/AGENTS.md`](deep_research/AGENTS.md).

```bash
uv sync --group deep-research                                      # installs openai + google-genai
uv run python -m infrastructure.search.deep_research providers     # free availability check
uv run python -m infrastructure.search.deep_research run-project \
    projects/templates/template_active_inference \
    "Review this manuscript; suggest fixes and new citations." --providers openai
```

Gotchas: `background=True` jobs bill to completion even if never polled;
Gemini jobs run 30–60+ min (poll budgets > 30 min); submits retry transient
connection errors with an OpenAI `Idempotency-Key`.

## End-to-End: search → BibTeX → PDF

```python
from infrastructure.search.literature import (
    LiteratureClient, SearchQuery, ArxivBackend, CrossrefBackend
)
from infrastructure.reference.citation import paper_to_bibentry, write_bibfile
from infrastructure.reference.citation.models import BibDatabase

client = LiteratureClient([ArxivBackend(), CrossrefBackend()])
result = client.search(SearchQuery(text="reproducible research", max_results=15))

db = BibDatabase()
for paper in result.papers:
    db.add(paper_to_bibentry(paper))
write_bibfile("projects/my_project/manuscript/references.bib", db)
```

## Reliability Properties

* **Per-backend failure isolation**: a network outage in one backend records
  an entry in `result.errors[name]` and leaves the rest of the search intact.
* **Deterministic caching**: `SearchCache` keys on the canonical query
  identity; cached files are pretty-printed JSON, version-control friendly.
* **Year filters re-applied defensively** by the aggregator even when a
  backend ignores them — protects downstream code.

## Related Modules

* [`infrastructure.reference.citation`](../reference/SKILL.md) — export side
  of the literature workflow (BibTeX writer, parser, converter).
* [`infrastructure.publishing`](../publishing/SKILL.md) — APA / MLA / DOI
  utilities for the resulting publications.
