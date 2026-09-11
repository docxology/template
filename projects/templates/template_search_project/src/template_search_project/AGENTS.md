# template_search_project/src — Agent guide

## Purpose

Domain glue only: configuration, pipeline orchestration over `infrastructure/`, synthesis prompts, figures, manuscript variable extraction, and reporting. No mocks in callers; tests supply real files and deterministic callables.

## Subpackages

The package is split into four subpackages. Every module is re-exported from
the package root `__init__.py`, so existing `template_search_project.<name>`
imports keep working.

### `search/` — search orchestration

| Module | Responsibility |
|--------|----------------|
| [`deep_search.py`](search/deep_search.py) | `run_deep_search` — multi-keyword fan-out with per-paper LLM notes |
| [`deep_search_cli.py`](search/deep_search_cli.py) | `run_deep_search_cli` — CLI-orchestration body for `scripts/run_deep_search.py` |
| [`search_pipeline_cli.py`](search/search_pipeline_cli.py) | `run_search_pipeline_cli` — CLI-orchestration body for `scripts/run_search_pipeline.py` |
| [`search_invariants.py`](search/search_invariants.py) | Pure-compute coverage invariants over `output/deep_search/aggregate.json` and `output/corpus.json` |

### `pipeline/` — pipeline orchestration and LLM

| Module | Responsibility |
|--------|----------------|
| [`pipeline.py`](pipeline/pipeline.py) | `run_literature_pipeline` — search, enrich, BibTeX, artifacts |
| [`synthesis.py`](pipeline/synthesis.py) | LLM prompts; injectable `(str) -> str` callable |
| [`composition.py`](pipeline/composition.py) | `compose_literature_review` — thin-orchestrator body for `scripts/s_compose_literature_review.py` |
| [`llm_runtime.py`](pipeline/llm_runtime.py) | `build_llm_callable` — Ollama-backed adapter (returns deterministic stub when offline) |
| [`dotenv.py`](pipeline/dotenv.py) | Stdlib `.env` loader used by scripts before infrastructure import |

### `analysis/` — review, analysis, and reporting

| Module | Responsibility |
|--------|----------------|
| [`analysis.py`](analysis/analysis.py) | Custom `scripts/review` stage hooks; `validate_bibliography_completeness` unions all `manuscript/*.bib`; `validate_variables_resolved` prefers `output/manuscript/` when present |
| [`report.py`](analysis/report.py) | `write_reading_report` |
| [`review_report.py`](analysis/review_report.py) | `generate_review_report` — inventory/documentation/bibliography audits, body for `scripts/zz_generate_review_report.py` |

### `publish/` — figures, dashboard, config, manuscript variables

| Module | Responsibility |
|--------|----------------|
| [`config.py`](publish/config.py) | Typed YAML → `ProjectConfig` |
| [`figures.py`](publish/figures.py) | Matplotlib summaries from search results |
| [`dashboard.py`](publish/dashboard.py) | Interactive search-coverage dashboard payload/panels — body for `scripts/zzz_build_dashboard.py` |
| [`manuscript_variables.py`](publish/manuscript_variables.py) | ``compute_variables``, ``write_resolved_manuscript_tree`` — JSON + ``output/manuscript/`` for render |

## Contracts

- Import `infrastructure.*` for reusable behaviour; keep project-specific branching here.
- New settings: extend `ProjectConfig`, YAML, and `tests/publish/test_config.py`.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
