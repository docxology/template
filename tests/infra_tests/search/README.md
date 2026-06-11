# tests/infra_tests/search/

Tests [`infrastructure.search`](../../../infrastructure/search/) literature client: models, HTTP backends (`pytest-httpserver`), caches, fulltext helpers, CLI.
The same test tree now also covers [`infrastructure.search.deep_research`](../../../infrastructure/search/deep_research/): project context packing, provider selection, prompt builders, dual-provider fan-out, and provider payload normalization.

## Run

```bash
uv run pytest tests/infra_tests/search/ -v
```

## See also

- [`AGENTS.md`](AGENTS.md)
- [`../../../infrastructure/search/AGENTS.md`](../../../infrastructure/search/AGENTS.md)
