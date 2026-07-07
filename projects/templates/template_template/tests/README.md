# Template Project Tests

Comprehensive test suite for the `template_template` introspection, metrics, and visualization modules.

## Running Tests

```bash
# From repo root
uv run pytest projects/templates/template_template/tests/ -v

# With coverage
uv run pytest projects/templates/template_template/tests/ --cov=projects/templates/template_template/src/template_template --cov-report=term-missing
```

## Test Coverage

| File | Tests | Target |
|------|------:|--------|
| `test_meta.py` | 63 | 90%+ on `introspection.py`, `inject_metrics.py` |
| `test_metrics.py` | 13 | 90%+ on `metrics.py` |
| `test_architecture_viz.py` | 6 | File existence + data shape |
| `test_confidentiality.py` | 9 | Public/private discovery boundary |
| `test_edge_cases.py` | 39 | Error branches, fallbacks |
| **Total** | **130** | See [`AGENTS.md`](AGENTS.md) for the per-class breakdown |

All tests use real filesystem paths (Zero-Mock policy) — no mocking of `Path`, `os`, or `importlib`.
