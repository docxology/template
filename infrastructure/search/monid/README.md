# Monid search gateway

Python client for the [Monid](https://monid.ai) HTTP API: discover endpoints,
inspect schemas/pricing, execute runs, and check wallet balance.

## Quick start

```python
from infrastructure.search.monid import MonidClient

client = MonidClient.from_env()  # reads MONID_API_KEY
hits = client.discover("web search", limit=5)
for hit in hits.results:
    print(hit.provider, hit.endpoint, hit.price)

detail = client.inspect("exa", "/search")
record = client.run("exa", "/search", {"query": "vector databases", "numResults": 5}, wait=True)
print(record.status, record.output)
```

## CLI

```bash
export MONID_API_KEY=monid_live_...
uv run python -m infrastructure.search.monid discover "twitter posts"
uv run python -m infrastructure.search.monid inspect apify /apidojo/tweet-scraper
uv run python -m infrastructure.search.monid pricing-table
uv run python -m infrastructure.search.monid balance
```

## Search API pricing (direct providers)

See [`PRICING.md`](PRICING.md) for USD per 1,000 searches across Exa, Brave,
Tavily, Serper, SerpAPI, and how Monid gateway pricing differs.

## Docs

- Upstream skill: [`.agents/skills/monid/SKILL.md`](../../../.agents/skills/monid/SKILL.md)
- API reference: https://monid.ai/docs/api/overview.md
- [`AGENTS.md`](AGENTS.md) — module contract
- [`SKILL.md`](SKILL.md) — agent-oriented API
