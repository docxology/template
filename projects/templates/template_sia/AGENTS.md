# template_sia — Agent Guide

## Purpose

Deterministic Self-Improvement Agent (SIA) harness exemplar. Layer 1 lives in
`infrastructure/sia/`; Layer 2 wires the `mini_classify` task, fixture replay,
and manuscript tokens. See [arXiv:2605.27276](https://arxiv.org/abs/2605.27276)
for the upstream contract; this tree reimplements the harness only.

## Layout

| Path | Role |
| --- | --- |
| `src/loop.py` | `run_sia_loop_project()` → `infrastructure.sia.run_sia_loop` |
| `src/loop_config.py` | Reads `sia:` block from `manuscript/config.yaml` |
| `src/reports.py` | Loop markdown report + `${SIA_*}` manuscript variables |
| `src/fixtures/recorded_generations/` | Fixture replay for gens 1–3 (default CI) |
| `tasks/mini_classify/` | Public/private task split + `evaluate.py` |
| `scripts/run_sia_loop.py` | Thin orchestrator (`--live-sia`, `--llm-model`) |
| `scripts/z_generate_manuscript_variables.py` | Post-analysis token hydration |

## Run modes

| Command | Behaviour |
| --- | --- |
| `uv run python scripts/run_sia_loop.py` | Fixture replay (deterministic) |
| `… --live-sia` | Bounded subprocess target + evaluation |
| `… --live-sia --llm-model gemma3:4b` | Live mode with Ollama feedback when available |

## Testing

```bash
uv run pytest projects/templates/template_sia/tests/ -m "not requires_ollama" -v
uv run python scripts/01_run_tests.py --project templates/template_sia --project-only
```

## See also

- [`README.md`](README.md)
- [`manuscript/AGENTS.md`](manuscript/AGENTS.md)
- [`../../../infrastructure/sia/AGENTS.md`](../../../infrastructure/sia/AGENTS.md)
