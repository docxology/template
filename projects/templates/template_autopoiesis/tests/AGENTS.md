# tests/ — template_autopoiesis

Project test suite (90% coverage floor on `src/`). No mocks — real temp trees
and subprocess CLI invocations.

## Running

```bash
uv run pytest projects/templates/template_autopoiesis/tests/ \
  --cov=projects/templates/template_autopoiesis/src --cov-fail-under=90
```

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
