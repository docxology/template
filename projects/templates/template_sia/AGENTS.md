# template_sia — Agent Guide

## Purpose

Deterministic Self-Improvement Agent (SIA) harness exemplar. Layer 1 lives in
`infrastructure/sia/`; Layer 2 wires the `mini_classify` task, fixture replay,
and manuscript tokens. See [arXiv:2605.27276](https://arxiv.org/abs/2605.27276)
for the upstream contract; this tree reimplements the harness only.

Decision memory and verifier hardening follow [`docs/rules/memory_and_decision_records.md`](../../../docs/rules/memory_and_decision_records.md): use nearby `WHY:` comments only for surprising local choices, keep volatile counts generated, and add negative controls for verifier-like gates.

## Layout

| Path | Role |
| --- | --- |
| `src/loop.py` | `run_sia_loop_project()` → `infrastructure.sia.run_sia_loop` |
| `src/loop_config.py` | Reads `sia:` block from `manuscript/config.yaml` |
| `src/reports.py` | Loop markdown report + `${SIA_*}` manuscript variables |
| `src/fixtures/recorded_generations/` | Fixture replay for gens 1–3 (default CI) |
| `tasks/mini_classify/` | Public/private task split + `evaluate.py` |
| `scripts/run_sia_loop.py` | Thin orchestrator (`--project-root`, `--live-sia`) |
| `scripts/z_generate_manuscript_variables.py` | Post-analysis token hydration |

## Run modes

| Command | Behaviour |
| --- | --- |
| `uv run python scripts/run_sia_loop.py` | Fixture replay (deterministic) |
| `… --live-sia` | Bounded subprocess target + evaluation; target code unchanged each generation (deterministic stub, no code mutation, no sandbox) |
| `… --live-sia` (model set in `manuscript/config.yaml`) | Live mode with Ollama feedback note written but **not applied to code**; the LLM model is read from the `sia.llm_model` key in `manuscript/config.yaml` (see `src/loop_config.py`), not a CLI flag. Shipped empty (`llm_model: ""`) = no LLM feedback |

Live mode demonstrates the loop's execution/evaluation plumbing, not autonomous
code modification. Cross-generation self-improvement is shown only via fixture
replay. See [`../../../infrastructure/sia/AGENTS.md`](../../../infrastructure/sia/AGENTS.md).

## Validation profile

The harness exposes two validation surfaces:

1. **Layout gate** — `uv run python -m infrastructure.sia.cli validate <task_dir>`
   (add `--json`) checks the required task directory structure (`validate_task_dir`
   in `infrastructure/sia/task_layout.py`) and exits non-zero with a message on an
   invalid or missing task — missing required directories, the public-data file, or
   the `reference/reference_target_agent.py` scaffold.
2. **Loop fail-closed behavior** — `run_sia_loop` (`infrastructure/sia/loop_runner.py`)
   raises `ValidationError`/`BuildError` and aborts the loop when a required input is
   absent: a missing fixture directory or fixture file in replay mode, a missing target
   agent in live mode, a non-positive `max_generations`, or a non-zero target-agent exit.
   There is no declarative `required_artifacts`/`quality_checks` contract — acceptance is
   enforced in Layer-1 code, not by a per-task config file.

## Testing

```bash
uv run pytest projects/templates/template_sia/tests/ -m "not requires_ollama" -v
uv run python scripts/01_run_tests.py --project templates/template_sia --project-only
```

## See also

- [`README.md`](README.md)
- [`manuscript/AGENTS.md`](manuscript/AGENTS.md)
- [`../../../infrastructure/sia/AGENTS.md`](../../../infrastructure/sia/AGENTS.md)
