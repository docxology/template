# `tests/` — Agent Guide

No-mocks test suite for the coordination core.

**Contents.** The suite consists of `test_agents.py`, `test_confirmation.py`, `test_dead_ends.py`, `test_figures.py`, `test_hermes_live.py`, `test_manuscript_numbers.py`, `test_objective.py`, `test_ranking.py`, `test_search.py`, `test_stagnation.py`, and `test_state.py`, plus `conftest.py` and `__init__.py`. `test_hermes_live.py` is opt-in via `requires_ollama`.

**Contract.** Run: `uv run python scripts/pipeline/stage_01_test.py --project templates/template_autoscientists --project-only`.

See the project [`../AGENTS.md`](../AGENTS.md).
