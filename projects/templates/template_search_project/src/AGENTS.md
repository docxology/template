# template_search_project/src — Agent guide

## Purpose

Domain glue only: configuration, pipeline orchestration over `infrastructure/`, synthesis prompts, figures, manuscript variable extraction, and reporting. No mocks in callers; tests supply real files and deterministic callables.

## Modules

| Module | Responsibility |
|--------|----------------|
| [`config.py`](template_search_project/publish/config.py) | Typed YAML → `ProjectConfig` |
| [`pipeline.py`](template_search_project/pipeline/pipeline.py) | `run_literature_pipeline` — search, enrich, BibTeX, artifacts |
| [`deep_search.py`](template_search_project/search/deep_search.py) | `run_deep_search` — multi-keyword fan-out with per-paper LLM notes |
| [`synthesis.py`](template_search_project/pipeline/synthesis.py) | LLM prompts; injectable `(str) -> str` callable |
| [`llm_runtime.py`](template_search_project/pipeline/llm_runtime.py) | `build_llm_callable` — Ollama-backed adapter (returns deterministic stub when offline) |
| [`dotenv.py`](template_search_project/pipeline/dotenv.py) | Stdlib `.env` loader used by scripts before infrastructure import |
| [`report.py`](template_search_project/analysis/report.py) | `write_reading_report` |
| [`figures.py`](template_search_project/publish/figures.py) | Matplotlib summaries from search results |
| [`manuscript_variables.py`](template_search_project/publish/manuscript_variables.py) | ``compute_variables``, ``write_resolved_manuscript_tree`` — JSON + ``output/manuscript/`` for render |
| [`analysis.py`](template_search_project/analysis/analysis.py) | Custom `scripts/review` stage hooks; `validate_bibliography_completeness` unions all `manuscript/*.bib`; `validate_variables_resolved` prefers `output/manuscript/` when present |
| [`composition.py`](template_search_project/pipeline/composition.py) | `compose_literature_review` — thin-orchestrator body for `scripts/s_compose_literature_review.py` |
| [`dashboard.py`](template_search_project/publish/dashboard.py) | Interactive search-coverage dashboard payload/panels — body for `scripts/zzz_build_dashboard.py` |
| [`deep_search_cli.py`](template_search_project/search/deep_search_cli.py) | `run_deep_search_cli` — CLI-orchestration body for `scripts/run_deep_search.py` |
| [`search_pipeline_cli.py`](template_search_project/search/search_pipeline_cli.py) | `run_search_pipeline_cli` — CLI-orchestration body for `scripts/run_search_pipeline.py` |
| [`search_invariants.py`](template_search_project/search/search_invariants.py) | Pure-compute coverage invariants over `output/deep_search/aggregate.json` and `output/corpus.json` |
| [`review_report.py`](template_search_project/analysis/review_report.py) | `generate_review_report` — inventory/documentation/bibliography audits, body for `scripts/zz_generate_review_report.py` |

## Contracts

- Import `infrastructure.*` for reusable behaviour; keep project-specific branching here.
- New settings: extend `ProjectConfig`, YAML, and `tests/publish/test_config.py`.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](template_search_project/README.md)
