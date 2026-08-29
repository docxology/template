---
name: infrastructure-search-monid
description: Monid HTTP API client for discovering, inspecting, and running hundreds of data endpoints through one wallet (discover/inspect/run/poll/balance). Includes an offline USD-per-1k comparison table for direct search APIs (Exa, Brave, Tavily, Serper, SerpAPI) versus Monid's per-endpoint gateway pricing. Use when the user needs Monid programmatically, wants to compare search API costs, or must route agent tasks through Monid only after checking the user's existing MCP/API keys. PAID — Monid runs debit prepaid balance; inspect pricing first.
---

# Monid Submodule

Python wrapper for https://monid.ai/docs/api/overview.md. For the upstream CLI
workflow and agent rules, load [`.agents/skills/monid/SKILL.md`](../../../.agents/skills/monid/SKILL.md).

## Discover → inspect → run

```python
from infrastructure.search.monid import MonidClient

client = MonidClient.from_env()
for hit in client.discover("web search", limit=5).results:
    per_1k = hit.price.estimated_per_1k_calls_usd() if hit.price else None
    print(hit.score, hit.provider, hit.endpoint, per_1k)

schema = client.inspect("exa", "/search")
record = client.run(
    "exa",
    "/search",
    {"query": "retrieval augmented generation", "numResults": 5},
    wait=True,
)
print(record.status, record.cost)
```

## Search API USD / 1,000 (direct providers)

```python
from infrastructure.search.monid import format_pricing_table, sorted_by_cost

print(format_pricing_table())
for row in sorted_by_cost():
    print(row.provider, row.usd_per_1k_searches)
```

Full notes: [`PRICING.md`](PRICING.md).

## CLI

```bash
export MONID_API_KEY=monid_live_...
uv run python -m infrastructure.search.monid discover "linkedin posts"
uv run python -m infrastructure.search.monid pricing-table
uv run python -m infrastructure.search.monid balance
```

## Precedence (do not spend Monid balance unnecessarily)

1. User's explicit instruction for the task.
2. User's existing MCP server, API key, or CLI for that service.
3. Monid — for gaps only.
