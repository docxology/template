# `scripts/` — Agent Guide

Thin orchestrators for analysis + agent search.

**Contents.** `run_ablation.py` and `run_search_comparison.py` drive experiments via `src/` and write figures/data; `run_search_comparison.py --mode live` delegates to the source-owned bounded local coordination runner. This template has zero `{{VARIABLE}}` manuscript tokens, so there is no manuscript-variable-generation script.

**Contract.** Scripts coordinate I/O + visualization only; experiment logic lives in `src/template_autoscientists/search/ablation.py` / `src/template_autoscientists/search/comparison.py`.

The search controller preserves an existing launcher audit and its fresh cache.
It verifies the selected SDK and project roots against that fixed pre-import
scope; discovering an optional unconsumed package does not extend the scope.
A fresh standalone controller still owns its complete provider-root selection.

See the project [`../AGENTS.md`](../AGENTS.md).
