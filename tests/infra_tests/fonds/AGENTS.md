# tests/infra_tests/fonds/ — Tests for `infrastructure.fonds`

## Purpose

Tests for fonds discovery, structure validation, and confidentiality guards.
Fonds are passive data resource pools (bibliographies, contacts, datasets) that
live under the top-level `fonds/` directory — parallel to `projects/` but
without `src/` or `tests/` subdirectories.

All tests follow the No-Mocks Policy: real `tmp_path` directories with real
files instead of mocks.

## Files

- `test_discovery.py` — coverage of fonds discovery (`discover_fonds`, `resolve_fond_root`), minimal valid fond
  structure, `fonds.yaml` parsing, and `offending_tracked_fonds()` guard logic

## Running

```bash
uv run pytest tests/infra_tests/fonds/ -v
uv run pytest tests/infra_tests/fonds/ --cov=infrastructure.fonds --cov-report=term-missing
```

## See Also

- [`../../../infrastructure/fonds/`](../../../infrastructure/fonds/) — modules under test
- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
