# `scripts/` — Agent Guide

Thin orchestrators for analysis + agent search.

**Contents.** `run_ablation.py` and `run_search_comparison.py` drive experiments via `src/` and write figures/data; `hermes_proposer.py` wires a live Hermes proposer (served through Ollama) into the agent search loop. This template has zero `{{VARIABLE}}` manuscript tokens, so there is no manuscript-variable-generation script.

**Contract.** Scripts coordinate I/O + visualization only; experiment logic lives in `src/ablation.py` / `src/comparison.py`.

See the project [`../AGENTS.md`](../AGENTS.md).
