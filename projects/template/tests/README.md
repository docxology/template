# Template Project Tests

Comprehensive test suite for the `template` introspection module.

## Running Tests

```bash
# From repo root
uv run pytest projects/template/tests/ -v

# With coverage
uv run pytest projects/template/tests/ --cov=template --cov-report=term-missing
```

## Test Coverage

| Module | Target |
|--------|--------|
| `introspection.py` | 90%+ |

All tests use real filesystem paths (Zero-Mock policy) — no mocking of `Path`, `os`, or `importlib`.
