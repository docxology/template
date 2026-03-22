# Testing: area_handbook

## Policy

- **No mocks** for domain logic; corpora are dicts or committed YAML.
- **Coverage**: 100% on `projects/area_handbook/src` (enforced in `pyproject.toml`).
- **Markers**: none required; tests finish in under one second.

## Commands

```bash
cd /path/to/template
uv run pytest projects/area_handbook/tests/ -v --cov=projects/area_handbook/src --cov-fail-under=90
```

Via orchestrator (runs infra + project when configured):

```bash
uv run python scripts/01_run_tests.py --project area_handbook
```

## Module map

| Test file | Targets |
|-----------|---------|
| `test_corpus_io.py` | Validation, JSON/YAML load, duplicate ids, empty fields |
| `test_corpus_stats.py` | Counts, unused themes, total weight |
| `test_handbook_md.py` | Markdown builders, TOC depth, tables |
| `test_outline_synthesis_metrics.py` | Outline, `synthesize`, `section_coverage_score`, metrics dict |
| `test_integration.py` | Fixture end-to-end JSON and body |
| `test_init_exports.py` | `src.__all__` |

## Adding a test

1. Prefer extending an existing class/file if the behavior fits.
2. Use `load_corpus_from_dict` for minimal reproducers; use `FIXTURE` path for integration-style checks.
3. Run coverage locally before pushing; new branches in `src/` must be executed by at least one test.
