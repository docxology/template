# Template Project Tests

Comprehensive test suite for the `template` introspection, metrics, and visualization modules.

## Running Tests

```bash
# From repo root
uv run pytest projects/template/tests/ -v

# With coverage
uv run pytest projects/template/tests/ --cov=template --cov-report=term-missing
```

## Test Coverage

| Module | Tests | Target |
|--------|------:|--------|
| `introspection.py` | 36 | 90%+ |
| `inject_metrics.py` | 13 | 90%+ |
| `metrics.py` | 10 | 90%+ |
| `architecture_viz.py` | 6 | File existence + data shape |
| **Total** | **65** | |

All tests use real filesystem paths (Zero-Mock policy) — no mocking of `Path`, `os`, or `importlib`.
