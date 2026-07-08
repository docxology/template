# infrastructure/sia — Agent Notes

## Purpose

Deterministic SIA (Self-Improving AI) harness utilities. Implements the Meta →
Target → Feedback artifact contract without vendoring upstream LLM orchestration.

> **Tier: exemplar-support.** Layer-1 by location, but imported only by its
> `template_sia` exemplar — intentionally not generic-reach across
> `infrastructure/`. Treat as exemplar support, not as dead code nor a
> general-purpose infra dependency.

## Public API

- `validate_task_dir(path)` — task layout gate
- `load_agent_execution(path)` — single/multi trajectory logs
- `run_evaluation(evaluate_script, *, gen_dir=..., task_dir=..., timeout_sec=120)` — subprocess evaluate.py
- `run_sia_loop(RunConfig)` — generation state machine
- `RunConfig`, `GenerationArtifacts`, `EvaluationResult`, `TaskLayout`

## Modules

- `task_layout.py` — `validate_task_dir(task_dir)` checks the required
  `data/public`, `data/private`, and `reference/` layout (plus `task.md` and
  `reference_target_agent.py`) and returns a resolved `TaskLayout`.
- `models.py` — Frozen dataclass contracts (`TaskLayout`, `EvaluationResult`,
  `AgentExecutionLog`, `GenerationArtifacts`) plus the mutable `RunConfig` and
  `GenerationState` that carry the harness through a run.
- `execution_logs.py` — `load_agent_execution(path)` loads
  `agent_execution.json` (or an `execution_q*.json` directory) into a normalized
  single- or multi-trajectory `AgentExecutionLog`.
- `evaluation_runner.py` — `run_evaluation()` runs a task's `evaluate.py` as a
  bounded subprocess; `read_results_json()` / `write_results_json()` parse and
  emit the canonical `results.json` as an `EvaluationResult`.
- `context_ledger.py` — `init_context()` and `append_generation()` create and
  grow the deterministic `context.md` ledger, recording each generation's target
  agent, execution log, and metric summary without LLM calls.
- `live_llm.py` — `generate_improvement_markdown()` optionally asks an
  Ollama-backed `LLMClient` for improvement-note markdown, returning `None` when
  no model is configured or the LLM is unreachable.
- `loop_runner.py` — `run_sia_loop(config)` drives the Meta → Target → Feedback
  generation state machine over fixture-replay or live subprocess paths and
  writes `run_summary.json`.

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
