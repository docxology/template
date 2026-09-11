# `tests/` — Agent Guide

No-mocks test suite for the coordination core.

**Contents.** The suite is mirrored to the `src/` subpackage layout: `agents/test_agents.py` + `agents/test_hermes_live.py` (opt-in via `requires_ollama`), `analysis/test_confirmation.py`/`test_objective.py`/`test_state.py`/`test_transcript.py`, `figures/test_figures.py`, and `search/test_search.py`/`test_ranking.py`/`test_dead_ends.py`/`test_stagnation.py`/`test_manuscript_numbers.py` (which also covers the `search/ablation.py` and `search/comparison.py` experiment modules), plus `conftest.py` and `__init__.py`.

**Contract.** Run: `uv run python scripts/pipeline/stage_01_test.py --project templates/template_autoscientists --project-only`.

See the project [`../AGENTS.md`](../AGENTS.md).
