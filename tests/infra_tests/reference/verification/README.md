# tests/infra_tests/reference/verification/

Tests [`infrastructure.reference.verification`](../../../../infrastructure/reference/verification/) — reference-existence resolution, the SQLite resolution cache, status classification, temporal-integrity (anachronism) detection, and the CLI. No mocks: HTTP paths use `pytest-httpserver`; the cache uses a real temp SQLite file.

## Run

```bash
uv run pytest tests/infra_tests/reference/verification/ -v
```

## See also

- [`AGENTS.md`](AGENTS.md)
- [`../../../../infrastructure/reference/verification/AGENTS.md`](../../../../infrastructure/reference/verification/AGENTS.md)
