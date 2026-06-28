# `infrastructure.search.exa`

Self-contained client for the [Exa](https://exa.ai) search API — a second search
interface under `infrastructure/search`, sibling to
[`literature/`](../literature/README.md). Where `literature` discovers academic
papers, `exa` is general web search, content extraction, and grounded answers.

> **Canonical API reference (source of truth):**
> <https://docs.exa.ai/reference/search-api-guide-for-coding-agents>
> If anything here drifts from real API behaviour, fetch that URL and report it.

## Layout — one subpackage per Exa search interface

```
exa/
├── config.py            ExaConfig (EXA_API_KEY, host, defaults)
├── errors.py            ExaError
├── http.py              ExaHttpClient protocol + UrllibExaHttpClient + ExaResponse
├── models.py            ExaResult, SearchResponse, ContentsResponse, AnswerResponse, …
├── client.py            ExaClient — the facade tying the interfaces together
├── cli.py / __main__.py python -m infrastructure.search.exa …
├── search/              POST /search        — neural/keyword + structured output
├── contents/            POST /contents      — parsed content for known URLs
├── answer/              POST /answer        — grounded answer + citations
└── find_similar/        POST /findSimilar  — similar pages for a seed URL
```

## Setup

```bash
export EXA_API_KEY="YOUR_API_KEY"   # keys: https://dashboard.exa.ai/api-keys
```

The package never reads the environment at import time — construction is explicit
via `ExaClient.from_env()` (or `ExaConfig(api_key=...)` for tests).

## Quick start

```python
from infrastructure.search.exa import ExaClient

client = ExaClient.from_env()

# Raw retrieval (token-efficient highlights — the default)
resp = client.search("Next.js route handler authentication example", num_results=10)
for r in resp.results:
    print(r.title, r.url, r.highlights)

# Grounded structured output (synthesised JSON + field-level citations)
resp = client.search(
    "articles about GPUs",
    output_schema={"type": "object", "properties": {"summary": {"type": "string"}}},
    system_prompt="Prefer official sources and collapse duplicate reporting.",
)
print(resp.output.content, resp.output.grounding)

# Content for URLs you already have
client.contents(["https://example.com/post"], text=True)

# Grounded answer for a question-first UI
client.answer("what is retrieval-augmented generation?")

# Similar pages for a seed URL
client.find_similar("https://arxiv.org/abs/1706.03762", num_results=5)
```

## CLI

```bash
python -m infrastructure.search.exa search "vector database benchmarks" --num-results 5
python -m infrastructure.search.exa contents https://example.com/post --text
python -m infrastructure.search.exa answer "what is RAG?"
python -m infrastructure.search.exa find-similar https://arxiv.org/abs/1706.03762
```

## Search types

`auto` (default, balanced) · `fast` · `instant` · `deep-lite` · `deep` ·
`deep-reasoning`. `output_schema` works on **every** type; deep variants give
higher-quality synthesis. See the guide's Search Type Reference for latencies.

## Design notes

- **camelCase on the wire, snake_case in Python.** `build_contents_payload`
  is the single place the conventions meet; `None` arguments are pruned.
- **Content keys nest under `contents` on `/search`** but are top-level on
  `/contents` — handled per interface so callers never hit the documented
  mistake.
- **Fail-fast guards** mirror documented `400`s: `category` `company`/`people`
  reject `exclude_domains` and date filters (caught before the request).
- **No external SDK / no import-time network.** Pure-stdlib transport keeps the
  core pipeline offline-reproducible; tests use `pytest-httpserver`, no mocks.

<!-- foam-orphan-nav:start (auto-managed: links sub-docs so they are reachable) -->

## Directory & sub-document map

Navigation links to in-tree documents (keeps them discoverable):

- [exa/answer package (technical)](answer/AGENTS.md)
- [exa/contents package (technical)](contents/AGENTS.md)
- [exa/find_similar package (technical)](find_similar/AGENTS.md)
- [exa/search package (technical)](search/AGENTS.md)

<!-- foam-orphan-nav:end -->
