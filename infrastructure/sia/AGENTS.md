# infrastructure/sia — Agent Notes

## Purpose

Deterministic SIA (Self-Improving AI) harness utilities. Implements the Meta →
Target → Feedback artifact contract without vendoring upstream LLM orchestration.

## Public API

- `validate_task_dir(path)` — task layout gate
- `load_agent_execution(path)` — single/multi trajectory logs
- `run_evaluation(evaluate_script, *, gen_dir=..., task_dir=..., timeout_sec=120)` — subprocess evaluate.py
- `run_sia_loop(RunConfig)` — generation state machine
- `RunConfig`, `GenerationArtifacts`, `EvaluationResult`, `TaskLayout`

## Boundaries

- Default path is **fixture replay** (`live=False`); no network in CI.
- `live=True` runs target agents via bounded subprocess; meta/feedback use
  deterministic stubs unless project layer wires Ollama.
- Business logic for exemplar tasks lives in `projects/templates/template_sia/src/`.

## CLI

```bash
# validate task layout (bare TASK_DIR is shorthand for `validate TASK_DIR`)
uv run python -m infrastructure.sia.cli validate tasks/mini_classify
uv run python -m infrastructure.sia.cli tasks/mini_classify
# summarize a run_summary.json (add --json for machine-readable output)
uv run python -m infrastructure.sia.cli inspect-run RUN_SUMMARY_JSON
```

## See Also

- [`../autoresearch/AGENTS.md`](../autoresearch/AGENTS.md) — readiness loop (distinct concern)
- [`../../projects/templates/template_sia/AGENTS.md`](../../projects/templates/template_sia/AGENTS.md)
