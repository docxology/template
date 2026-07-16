# Test Suite Architecture

Tests for `template_literature_meta_analysis` enforce the repository no-mocks policy with real data, real temporary files, and local HTTP servers.

## Coverage

Project `src/` coverage must remain at or above 90%:

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/   --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90
```

Live collected test counts and measured coverage snapshots belong in `../../../docs/_generated/COUNTS.md`.

## Fixtures

- `conftest.py` sets up project import paths, `MPLBACKEND=Agg`, temp output dirs, and synthetic corpus fixtures.
- `pytest-httpserver` covers retrieval and LLM HTTP behavior without external network calls.
- File tests use `tmp_path` and real JSON/JSONL payloads.

## Subdirectories

| Path | Scope |
| --- | --- |
| `tests/literature/` | Record models, clients, corpus persistence, search runner, full-text reports |
| `tests/analysis/` | Bibliometrics, TF-IDF, embeddings, entities, topics, temporal metrics |
| `tests/knowledge_graph/` | Assertions, hypothesis scoring, RDF/nanopubs, LLM parsing/resume logic |
| `tests/reproducibility/` | Workflow extraction, persistent-cache/active-scope separation, scoring, reconciled failures |
| `tests/visualization/` | Headless figure generation and style config |
| root tests | Config loading, script entry points, manuscript variables |
