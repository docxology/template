# `scripts/`

Thin orchestrators for analysis + manuscript variables.

**Contents.** `run_ablation.py` and `run_search_comparison.py` drive experiments via `src/` and write figures/data; `z_generate_manuscript_variables.py` hydrates manuscript tokens.

**Contract.** Scripts coordinate I/O + visualization only; experiment logic lives in `src/ablation.py` / `src/comparison.py`.

See the project [`../AGENTS.md`](../AGENTS.md).
