# template_search_project/src — Agent guide

## Purpose

Domain glue only: configuration, pipeline orchestration over `infrastructure/`, synthesis prompts, figures, manuscript variable extraction, and reporting. No mocks in callers; tests supply real files and deterministic callables.

## Modules

| Module | Responsibility |
|--------|----------------|
| [`config.py`](config.py) | Typed YAML → `ProjectConfig` |
| [`pipeline.py`](pipeline.py) | `run_literature_pipeline` — search, enrich, BibTeX, artifacts |
| [`deep_search.py`](deep_search.py) | `run_deep_search` — multi-keyword fan-out with per-paper LLM notes |
| [`synthesis.py`](synthesis.py) | LLM prompts; injectable `(str) -> str` callable |
| [`llm_runtime.py`](llm_runtime.py) | `build_llm_callable` — Ollama-backed adapter (returns deterministic stub when offline) |
| [`dotenv.py`](dotenv.py) | Stdlib `.env` loader used by scripts before infrastructure import |
| [`report.py`](report.py) | `write_reading_report` |
| [`figures.py`](figures.py) | Matplotlib summaries from search results |
| [`manuscript_variables.py`](manuscript_variables.py) | ``compute_variables``, ``write_resolved_manuscript_tree`` — JSON + ``output/manuscript/`` for render |
| [`analysis.py`](analysis.py) | Custom `scripts/review` stage hooks; `validate_bibliography_completeness` unions all `manuscript/*.bib`; `validate_variables_resolved` prefers `output/manuscript/` when present |
| [`composition.py`](composition.py) | `compose_literature_review` — thin-orchestrator body for `scripts/s_compose_literature_review.py` |
| [`dashboard.py`](dashboard.py) | Interactive search-coverage dashboard payload/panels — body for `scripts/zzz_build_dashboard.py` |
| [`deep_search_cli.py`](deep_search_cli.py) | `run_deep_search_cli` — CLI-orchestration body for `scripts/run_deep_search.py` |
| [`search_pipeline_cli.py`](search_pipeline_cli.py) | `run_search_pipeline_cli` — CLI-orchestration body for `scripts/run_search_pipeline.py` |
| [`search_invariants.py`](search_invariants.py) | Pure-compute coverage invariants over `output/deep_search/aggregate.json` and `output/corpus.json` |
| [`review_report.py`](review_report.py) | `generate_review_report` — inventory/documentation/bibliography audits, body for `scripts/zz_generate_review_report.py` |

## Contracts

- Import `infrastructure.*` for reusable behaviour; keep project-specific branching here.
- New settings: extend `ProjectConfig`, YAML, and `tests/test_config.py`.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
