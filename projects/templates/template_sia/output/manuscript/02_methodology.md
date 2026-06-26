# Methodology {#sec:methodology}

## SIA loop

The harness implements a three-agent cycle:

1. **Meta** — proposes or seeds a target agent for generation $n$.
2. **Target** — runs against public task data and writes `agent_execution.json`.
3. **Feedback** — reads private evaluation metrics and proposes improvements for generation $n+1$.

![Meta → Target → Feedback loop topology for the SIA harness, generated programmatically by `write_sia_loop_topology`.](../output/figures/sia_loop_topology.png){#fig:sia-loop-topology width=90%}

Artifacts land under `output/runs/run_{id}/gen_{n}/` with `target_agent.py`, `agent_execution.json`, optional `improvement.md`, and canonical `results.json`.

## Task layout

Each task exposes:

- `data/public/` — agent-visible instructions and data (`task.md`, `train.csv`, `evaluate.py`).
- `data/private/` — held-out labels for evaluation only.
- `reference/reference_target_agent.py` — deterministic baseline.

The exemplar task `mini_classify` is a threshold classifier on a single feature column.

## Determinism contract

When `sia.live: false` (default), generations replay recorded fixtures from `src/fixtures/recorded_generations/`. CI never executes generated agent code or calls external LLM APIs.

Pass `--live-sia` to `scripts/run_sia_loop.py` for bounded subprocess execution and optional Ollama feedback when a model is configured.

## Per-generation metric overview

The heatmap below provides a compact overview of per-generation accuracy and sample
count, enabling at-a-glance comparison across runs.

![Per-generation metric heatmap showing accuracy and sample count across SIA generations.](../output/figures/sia_generation_heatmap.png){#fig:sia-generation-heatmap width=80%}
