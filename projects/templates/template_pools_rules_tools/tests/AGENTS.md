# tests/ — template_pools_rules_tools

Project tests (90% coverage floor on `src/`). Real fixtures under `fonds/`,
`rules/`, and `tools/` template trees — no mocks.

## Running

```bash
uv run pytest projects/templates/template_pools_rules_tools/tests/ \
  --cov=projects/templates/template_pools_rules_tools/src --cov-fail-under=90
```

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
