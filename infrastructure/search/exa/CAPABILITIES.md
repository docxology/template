# `infrastructure.search.exa` — Methods, Return Shapes & What You Can Learn

A practical reference for every method on `ExaClient`: what it does, what it
returns, and what intelligence you can extract (entities, citations, full text,
relevance scores, cost). Every row below was **confirmed against the live Exa
API on 2026-06-02** with a real key — not just read from the client code.

> **Source of truth for the wire API:**
> <https://docs.exa.ai/reference/search-api-guide-for-coding-agents>
> This file documents the *Python client*; if it drifts from real behaviour,
> fetch that URL and re-run the probes in this doc.

## Setup

```python
from infrastructure.search.exa import ExaClient
client = ExaClient.from_env()   # reads EXA_API_KEY from the environment
```

`from_env()` reads `os.environ` only — it does **not** auto-load `.env`. Either
`set -a; source .env; set +a` first, or go through anything that calls
`load_dotenv()` (e.g. `infrastructure.core.credentials.CredentialManager`).

## At a glance

| Method | Endpoint | Input | Returns | Primary use | Live status | Typical cost |
|--------|----------|-------|---------|-------------|-------------|--------------|
| `client.search(query, …)` | `POST /search` | free-text query | `SearchResponse` | Find pages; optionally synthesise grounded JSON | ✅ confirmed | ~$0.005–0.012 |
| `client.contents(urls, …)` | `POST /contents` | known URLs / result `id`s | `ContentsResponse` | Extract clean parsed text/highlights for URLs you already have | ✅ confirmed | ~$0.001 |
| `client.answer(query, …)` | `POST /answer` | question | `AnswerResponse` | One grounded answer + citations (question-first UIs) | ✅ confirmed | ~$0.005 |
| `client.find_similar(url, …)` | `POST /findSimilar` | seed URL | `SearchResponse` | Semantically similar pages to a seed document | ✅ confirmed | ~$0.007 |

> **Fix landed 2026-06-02:** `find_similar` previously posted to `/find-similar`
> and returned **HTTP 404** against the live API. The correct path is camelCase
> `/findSimilar`. The no-mocks httpserver test had registered the *same wrong
> path*, so it passed while the real endpoint was broken — the test encoded the
> bug. Both code and test now use `/findSimilar`, re-verified live.

---

## The universal record: `ExaResult`

Every endpoint normalises results into the same `ExaResult` dataclass, so
`/search`, `/contents`, `/findSimilar` results and `/answer` citations are all
consumed uniformly. Fields:

| Field | Type | Populated when | What you learn |
|-------|------|----------------|----------------|
| `id` | `str` | always | Stable Exa doc id — re-fetch via `/contents` (falls back to URL) |
| `url` | `str \| None` | always | Canonical landing page |
| `title` | `str \| None` | usually | Page/document title |
| `score` | `float \| None` | `/findSimilar` (and relevance-ranked search) | Semantic similarity 0–1; **`None` for plain neural `/search`** |
| `published_date` | `str \| None` | when known | Publication date (often `None` for academic PDFs) |
| `author` | `str \| None` | when known | Author(s) — e.g. `"Ryan Smith, Karl J. Friston, …"` |
| `text` | `str \| None` | `text=True` | Full parsed page text (e.g. 44 039 chars for a Wikipedia article) |
| `highlights` | `list[str]` | default / `highlights=True` | Query-relevant excerpts (token-efficient) |
| `highlight_scores` | `list[float]` | with highlights | Per-highlight relevance |
| `summary` | `str \| None` | `summary=True` | LLM-written summary of the page |
| `image` / `favicon` | `str \| None` | when present | Lead image / site favicon URLs |
| `extras` | `dict` | varies | Endpoint extras (e.g. subpages) |
| `raw` | `dict` | always | The untouched JSON object — anything not modelled is here |

`SearchResponse` / `ContentsResponse` / `AnswerResponse` also carry
`request_id`, `cost_dollars` (parsed from `costDollars.total`), and `raw`.

---

## 1. `search()` — neural/keyword retrieval + grounded synthesis

`POST /search`. Two modes from one method.

### 1a. Raw retrieval (default)

```python
r = client.search("active inference free energy principle tutorial", num_results=3)
for x in r.results:
    print(x.title, x.url, x.author, x.highlights[:1])
print(r.cost_dollars)   # e.g. 0.007
```

Defaults to `highlights=True` (the token-efficient mode). **What you learn:**
ranked pages with title/url/id/author + query-relevant highlight excerpts.
Note plain neural search returns `score=None` and often `published_date=None`.

Key params: `type` (`auto`·`fast`·`instant`·`deep-lite`·`deep`·`deep-reasoning`),
`num_results`, `category`, `include_domains`/`exclude_domains`,
`start_published_date`/`end_published_date`, `user_location`, `moderation`.
Content knobs: `highlights`, `text`, `summary`, `max_age_hours` (freshness /
livecrawl), `subpages`.

> Guardrail enforced client-side: `category="company"|"people"` rejects
> `exclude_domains` and date filters (Exa returns HTTP 400) — caught before the
> request with a clear `ExaError`.

### 1b. Structured output / **entity extraction** (`output_schema`)

Pass a JSON Schema and Exa synthesises grounded JSON with **field-level
citations**. This is the path for "pull entities + where each fact came from."

```python
schema = {
  "type": "object", "required": ["researchers"],
  "properties": {"researchers": {"type": "array", "items": {
    "type": "object", "required": ["name"],
    "properties": {"name": {"type": "string"}, "affiliation": {"type": "string"}}}}},
}
r = client.search("key researchers in active inference", type="deep",
                  output_schema=schema,
                  system_prompt="Prefer primary sources; dedupe people.")
print(r.output.content)      # → {"researchers": [{"name": "Karl J. Friston", "affiliation": "…UCL…"}, …]}
for g in r.output.grounding: # field-level provenance
    print(g.field, g.confidence, [c["url"] for c in g.citations])
```

**Live result (2026-06-02):** extracted Karl J. Friston, Thomas Parr, Giovanni
Pezzulo, Thomas FitzGerald with affiliations; grounding e.g.
`field=researchers[0].name confidence=high citations=['https://www.fil.ion.ucl.ac.uk/~karl/', …]`.
Cost $0.012.

- `r.output.content` — your schema's shape (dict, or a string for `{"type":"text"}`).
- `r.output.grounding` — list of `Grounding(field, citations, confidence)`;
  `confidence ∈ {high, medium, low}`, `citations` are `{url, title}` dicts.
- Schema limits: nesting depth ≤ 2, ≤ 10 total properties. Do **not** add
  citation/confidence fields yourself — grounding is returned automatically.
- `output_schema` works on **every** `type`; `deep`/`deep-reasoning` give
  higher-quality synthesis at higher latency/cost.

**What you can learn here:** named entities (people, companies, products),
structured attributes per entity, and a per-field citation trail with
confidence — i.e. extraction *and* its evidence in one call.

---

## 2. `contents()` — clean parsed content for URLs you already have

`POST /contents`. For URLs from a database, RSS, user input, or prior result
`id`s — and to refresh stale content via `max_age_hours`.

```python
r = client.contents(["https://en.wikipedia.org/wiki/Free_energy_principle"], text=True)
x = r.results[0]
print(x.title, len(x.text))   # "Free energy principle - Wikipedia", 44039
```

**Live result:** 44 039 chars of parsed text, cost $0.001 (cheapest endpoint).
Params: `highlights` / `text` / `summary` (default highlights), `max_age_hours`,
`livecrawl_timeout`, `subpages`. **What you learn:** full body text (RAG-ready),
highlights, or an LLM summary for arbitrary URLs without a search step.

> Content keys are **top-level** on `/contents` but **nested under `contents`**
> on `/search` and `/findSimilar`. The client handles this per-interface, so you
> never hit the documented mistake.

---

## 3. `answer()` — one grounded answer + citations

`POST /answer`. Best for question-first UIs where you want a synthesised answer
and don't need to inspect raw results.

```python
r = client.answer("What is the free energy principle in one sentence?")
print(r.answer)                                  # synthesised, with [1][2][3] markers
for c in r.citations: print(c.title, "::", c.url)
```

**Live result:** a one-sentence grounded answer plus 4 citations including the
MIT *Open Encyclopedia of Cognitive Science*, Friston's *TICS* "rough guide",
and the *Unified brain theory* paper. Cost $0.005. Params: `text=True` (include
full source text on each citation), `system_prompt`, `output_schema` (structured
answer). **What you learn:** a cited natural-language answer + its full source
list as `ExaResult` citations.

---

## 4. `find_similar()` — semantically similar pages for a seed URL

`POST /findSimilar`. Same `SearchResponse` shape as `/search`, but the query is
a URL instead of free text.

```python
r = client.find_similar("https://arxiv.org/abs/1706.03762",
                        num_results=3, exclude_source_domain=True)
for x in r.results: print(x.score, x.title, x.url)
```

**Live result (2026-06-02, post-fix):** for the "Attention Is All You Need"
arXiv URL → NeurIPS/NIPS proceedings copies and a related OpenReview PDF, with
real similarity **scores** (0.927, 0.895, 0.882). Cost $0.007. Params:
`num_results`, `include_domains`/`exclude_domains`, date filters,
`exclude_source_domain` (drop pages from the seed's own domain), content knobs.
**What you learn:** a ranked neighbourhood of related documents *with* similarity
scores — the one endpoint that reliably populates `ExaResult.score`.

---

## Cross-cutting: what intelligence is available

| You want… | Use | Field(s) |
|-----------|-----|----------|
| Ranked relevant URLs | `search` | `results[].url/title/id` |
| Query-relevant excerpts (cheap) | any, default | `results[].highlights` |
| Full page text (RAG) | `search`/`contents` `text=True` | `results[].text` |
| **Named entities + attributes** | `search(output_schema=…)` | `output.content` |
| **Per-fact citations + confidence** | `search(output_schema=…)` | `output.grounding[].{citations,confidence}` |
| A cited natural-language answer | `answer` | `answer` + `citations[]` |
| Author / publication date | any | `results[].author` / `published_date` (often `None` for PDFs) |
| Similarity scores | `find_similar` | `results[].score` |
| Spend per call | all | `cost_dollars` (`raw["costDollars"]` for the breakdown) |
| Anything unmodelled | all | `results[].raw`, `response.raw` |

## Errors & reproducing this doc

All failures raise `ExaError` (with `.status` / `.body` on non-2xx). Transient
TLS handshake/read timeouts are wrapped as `ExaError` too — wrap live calls in a
short retry loop (the probes used to confirm this doc retried 4–6×).

To re-confirm against the live API: `set -a; source .env; set +a` then exercise
each method as shown above. Offline/CI verification is the no-mocks suite:
`uv run pytest tests/infra_tests/search/test_exa.py -q` (20 tests, pytest-httpserver,
no network).
