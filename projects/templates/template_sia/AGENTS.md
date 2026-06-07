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
| `… --live-sia` (model set in `sia.yaml`) | Live mode with Ollama feedback note written but **not applied to code**; the LLM model is read from config (`sia.yaml`/settings), not a CLI flag |

Live mode demonstrates the loop's execution/evaluation plumbing, not autonomous
code modification. Cross-generation self-improvement is shown only via fixture
replay. See [`../../../infrastructure/sia/AGENTS.md`](../../../infrastructure/sia/AGENTS.md).

## Validation profile

The harness exposes two validation surfaces:

1. **Layout gate** — `uv run python -m infrastructure.sia.cli validate <task_dir>`
   (add `--json`) checks the required task directory structure and exits non-zero
   with a message on an invalid or missing task.
2. **Pipeline contract** — each task's `sia.yaml` declares `required_artifacts`
   and `quality_checks`; the loop fails closed when a required artifact is
   missing or a quality check is unmet. Use these keys to define a project's own
   acceptance profile without touching Layer-1 code.

## Testing

```bash
uv run pytest projects/templates/template_sia/tests/ -m "not requires_ollama" -v
uv run python scripts/01_run_tests.py --project templates/template_sia --project-only
```

## See also

- [`README.md`](README.md)
- [`manuscript/AGENTS.md`](manuscript/AGENTS.md)
- [`../../../infrastructure/sia/AGENTS.md`](../../../infrastructure/sia/AGENTS.md)
