# tests/infra_tests/provenance/ — Provenance DAG Tests

Tests for `infrastructure/provenance/`: content-addressed DAG store,
Review system, and CLI.

## Files

| File | What it covers |
|---|---|
| `test_store.py` | `Provenance` store: record, link, get, query, list, clear, persistence, content addressing |
| `test_review.py` | `Review` namespace: findings, deduplication, verdicts, severity, metadata |

## Run

```bash
uv run pytest tests/infra_tests/provenance -q
```

## Standards

- No mocks — all tests use `tmp_path` for isolated store files.
- `Provenance.with_path(tmp_path / "graph.json")` for store isolation.
- `Review._store = isolated_store` for review isolation.
