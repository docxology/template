# `scripts/` — Agent Guide

Thin orchestrators for analysis + agent search.

**Contents.** `run_ablation.py` and `run_search_comparison.py` drive experiments via `src/` and write figures/data; `run_search_comparison.py --mode live` delegates to the source-owned bounded local coordination runner. This template has zero `{{VARIABLE}}` manuscript tokens, so there is no manuscript-variable-generation script.

**Contract.** Scripts coordinate I/O + visualization only; experiment logic lives in `src/template_autoscientists/search/ablation.py` / `src/template_autoscientists/search/comparison.py`.

See the project [`../AGENTS.md`](../AGENTS.md).
