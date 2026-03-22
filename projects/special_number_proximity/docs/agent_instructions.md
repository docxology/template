# Agent instructions

When editing this project:

1. Keep **business logic** in `src/`; keep `scripts/` as thin orchestrators (YAML, paths, matplotlib only).
2. Any new public function in `src/` needs **type hints**, a **docstring**, and **tests** (no `unittest.mock`).
3. If you change JSON fields from `proximity_monte_carlo.py`, update **`04_results.md`** and **`manuscript/AGENTS.md`**.
4. Preserve **`compare_mod1`** semantics: when `true`, both constants and distances use fractional parts for alignment with Uniform$(0,1)$.
5. Run `uv run pytest projects/special_number_proximity/tests/ --cov=projects/special_number_proximity/src --cov-fail-under=90` before claiming completion.
