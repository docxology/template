# Search API pricing — USD per 1,000 searches

Reference table for **direct** web-search APIs. Monid is a gateway: each routed
endpoint has its own `PER_CALL` or `PER_RESULT` price surfaced by
`discover` / `inspect` / `run`. Use
`uv run python -m infrastructure.search.monid pricing-table` to print the
programmatic table from `infrastructure.search.monid.pricing`.

**Last reviewed:** 2026-08-28. Re-verify vendor pages before budgeting.

## Direct search APIs (list price)

| Provider | Product | USD / 1k searches | USD / search | Notes |
| --- | --- | ---: | ---: | --- |
| Serper | Google SERP (Ultimate tier) | $0.30 | $0.0003 | ~12.5M queries/mo volume tier |
| Serper | Google SERP (Starter) | $1.00 | $0.0010 | 50k queries/mo at $50/mo |
| Brave | Search / LLM context API | $5.00 | $0.0050 | Independent index; $5/mo free credits |
| Exa | `POST /answer` | $5.00 | $0.0050 | Grounded answer + citations |
| Exa | `POST /search` (≤10 results) | $7.00 | $0.0070 | +$1/1k for each result above 10 |
| Tavily | Research credits (PAYG) | $8.00 | $0.0080 | ~1 credit per basic search |
| SerpAPI | Google (Developer) | $10.00 | $0.0100 | $75/mo for 5k searches |
| Exa | `POST /monitors` | $15.00 | $0.0150 | Scheduled tracking, not ad-hoc search |

Sources: [Exa pricing](https://exa.ai/pricing?tab=api),
[Brave Search API](https://brave.com/search/api/),
[Tavily](https://tavily.com/#pricing),
[Serper](https://serper.dev/pricing),
[SerpAPI](https://serpapi.com/pricing).

## Monid gateway

Monid does **not** publish a single per-1k search rate. Pricing is per endpoint:

- **PER_CALL** — flat fee per execution (example: $0.003/call → **$3.00/1k**).
- **PER_RESULT** — base fee plus per-item charge (volume multiplies quickly).

The Monid homepage cites an example run at **~$0.0013/call (~$1.30/1k)** for one
tool; Exa-backed routes inherit upstream Exa rates plus gateway markup. Always
`inspect` before `run`:

```python
from infrastructure.search.monid import MonidClient

client = MonidClient.from_env()
for hit in client.discover("web search", limit=5).results:
    per_1k = hit.price.estimated_per_1k_calls_usd() if hit.price else None
    print(hit.provider, hit.endpoint, per_1k)
```

See [Monid pricing guide](https://monid.ai/docs/guide/pricing).

## When to use which

| Need | Typical choice |
| --- | --- |
| Cheapest Google SERP at scale | Serper ($0.30–$1.00/1k) |
| Independent index, privacy | Brave ($5/1k) |
| Neural / semantic web search | Exa search ($7/1k base) |
| Agent-oriented snippets | Tavily ($8/1k PAYG) |
| One wallet, many providers | Monid (inspect per endpoint) |

Prefer the user's existing API key or MCP when they already have one; Monid
spends prepaid balance and should fill gaps only (see [`SKILL.md`](SKILL.md)).
