# tests/infra_tests/autoresearch/

Tests for `infrastructure.autoresearch` deterministic readiness planning: config loading, pipeline/project overlay composition, validation issue reporting, report writing, and CLI behavior.

## Run

```bash
uv run pytest tests/infra_tests/autoresearch/ -v
uv run pytest tests/infra_tests/autoresearch/ --cov=infrastructure.autoresearch --cov-report=term-missing
```

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../../../infrastructure/autoresearch/README.md`](../../../infrastructure/autoresearch/README.md)
