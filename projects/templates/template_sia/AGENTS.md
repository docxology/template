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
|  `src/template_sia/loop/loop.py` | Layer-2 adapter: builds `RunConfig`, selects fixtures, invokes `infrastructure.sia.run_sia_loop`, and writes project artifacts |
|  `src/template_sia/loop/loop_config.py` | Reads `project_config.sia` from `manuscript/config.yaml` |
|  `src/template_sia/manuscript/reports.py` | Loop markdown report + `{{SIA_*}}` manuscript variables |
|  `src/template_sia/fixtures/recorded_generations/` | Fixture replay for gens 1–3 (default CI) |
| `tasks/mini_classify/` | Public/private task split (`data/public/` + `data/private/`) with the scorer at `tasks/mini_classify/data/public/evaluate.py` |
| `src/template_sia/loop/live_proposals.py` | Bounded local Ollama numeric proposals, Docker evaluation, frozen holdout, diff/rollback/approval receipts |
| `scripts/run_sia_loop.py` | Thin orchestrator (`--project-root`, `--live-sia`, `--live-proposals`) |
| `scripts/z_generate_manuscript_variables.py` | Post-analysis token hydration |

## Run modes

| Command | Behaviour |
| --- | --- |
| `uv run python scripts/run_sia_loop.py` | Fixture replay (deterministic) |
| `… --live-sia` | Fixed reference subprocess diagnostics; unchanged target code, no live proposal acceptance |
| `… --live-proposals --model <name> --container-image sha256:<id>` | Actual local Ollama threshold proposals; Docker-only evaluation, at most three generations, exact rollback, frozen held-out scoring |

The reference diagnostic mode demonstrates execution/evaluation plumbing.
The numeric proposal mode accepts only a finite threshold and rationale;
arbitrary generated code, paths, host execution, and source application are
outside its scope. Missing required tools or model block with exit 75 and a
retained receipt. Fixture replay records real threshold variants but all score
1.0 on the toy dataset, so it demonstrates deterministic replay and threshold
robustness—not measured self-improvement. See
[`../../../infrastructure/sia/AGENTS.md`](../../../infrastructure/sia/AGENTS.md).
`project_config.sia.approval_mode` is typed and defaults to `fixture_replay`;
forks must select `live_proposal` or `live_apply` only alongside the sandbox,
diff, rollback, and owner-receipt contract in `src/template_sia/loop/approval.py`.
The reference adapter lives in `src/template_sia/loop/loop.py`, and the numeric
proposal controller in `live_proposals.py`. Scripts parse arguments, call these
APIs, and present output paths. See [`docs/live-numeric-proposals.md`](docs/live-numeric-proposals.md)
for the sandbox and evidence contract.

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
uv run python scripts/pipeline/stage_01_test.py --project templates/template_sia --project-only
```

## See also

- [`README.md`](README.md)
- [`manuscript/AGENTS.md`](manuscript/AGENTS.md)
- [`../../../infrastructure/sia/AGENTS.md`](../../../infrastructure/sia/AGENTS.md)

#
## Agent skill

A Hermes/agentskills.io-compatible skill for this exemplar lives at
[`.agents/skills/template-sia/SKILL.md`](.agents/skills/template-sia/SKILL.md).
Load it when working inside this template to get when-to-use guidance,
quick reference commands, and pitfalls.

# Publishing

- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Publishing module reference](../../../infrastructure/publishing/README.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md) · [Archival targets](../../../docs/maintenance/archival-targets.md)
