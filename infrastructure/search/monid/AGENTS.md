# AGENTS — `infrastructure.search.monid`

Monid HTTP API client. Unified gateway to hundreds of data endpoints; sibling to
`exa/` (direct Exa) and `literature/` (academic search).

## Invariants

- **No import-time side effects.** Env is read only in `MonidConfig.from_env`.
- **No external SDK.** Transport is stdlib `urllib` via `UrllibMonidHttpClient`.
- **No mocks in tests.** Use `pytest-httpserver` and a `base_url` override.
- **Errors are `MonidError`** carrying `.status`/`.body` for non-2xx.
- **Monid runs cost money.** Do not route around the user's existing MCP/API keys.

## Public API

| Symbol | Role |
| --- | --- |
| `MonidConfig` / `MonidClient` | Config + facade |
| `MonidClient.discover(query, limit=5, min_score=None)` | `POST /v1/discover` |
| `MonidClient.inspect(provider, endpoint)` | `POST /v1/inspect` |
| `MonidClient.run(provider, endpoint, input, wait=False)` | `POST /v1/run`; optional poll |
| `MonidClient.get_run(run_id)` / `poll_run(run_id)` | `GET /v1/runs/:id` |
| `MonidClient.balance()` | `GET /v1/wallet/balance` |
| `SEARCH_API_PRICES` / `format_pricing_table()` | Offline direct-provider USD/1k table |

Environment: `MONID_API_KEY` (format `monid_live_...`).

## Source of truth

https://monid.ai/docs/llms.txt — fetch API pages when behaviour drifts.

## Agent skill

Repository skill: [`.agents/skills/monid/SKILL.md`](../../../.agents/skills/monid/SKILL.md)
(upstream CLI workflow). Module skill: [`SKILL.md`](SKILL.md).

## Tests

```bash
uv run pytest tests/infra_tests/search/test_monid.py -v
```
