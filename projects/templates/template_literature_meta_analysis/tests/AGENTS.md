# Test Suite Architecture

Tests for `template_literature_meta_analysis` enforce the repository no-mocks policy with real data, real temporary files, and local HTTP servers.

## Coverage

Project `src/` coverage must remain at or above 90%:

From the monorepo root, provision the isolated project gate:

```bash
uv run python scripts/pipeline/stage_01_test.py --project templates/template_literature_meta_analysis --project-only
```

From an independent checkout's root, after the platform wheel and project `dev`
extra are installed in its own environment (see [`../STANDALONE.md`](../STANDALONE.md)):

```bash
python -I -m pytest tests/ --cov=src --cov-fail-under=90
```

`test_canonical_test_command.py` runs bounded configured-pytest children against
owned copies of the actual source, configuration, conftest, and corpus oracles.
It proves a nonempty standalone source invocation and rejects a false corpus
expectation and zero collection. An additional actual own-root/own-source/ancestor SDK
shadow case must preserve the selected provider origin/version without executing
any invalid package. It does not establish full-suite coverage or
installed-wheel acceptance. Root-stage integration belongs to the Root suite.

Live collected test counts and measured coverage snapshots belong in `../../../docs/_generated/COUNTS.md`.

## Fixtures

- `conftest.py` selects the declared SDK before registering own source, `MPLBACKEND=Agg`, temp output dirs, and synthetic corpus fixtures.
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
