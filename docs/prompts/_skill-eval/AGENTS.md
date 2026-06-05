# Skill eval workspace (`docs/prompts/_skill-eval/`)

## Purpose

Synthetic benchmark for template workflow skills: keyword/heuristic grader, harness-generated responses, benchmark reports, and static review HTML.

## Layout

| Path | Role |
| --- | --- |
| [`evals/evals.json`](evals/evals.json) | 29 eval cases (25 positive, 4 negative) |
| [`latest/`](latest/) | Default harness output (`benchmark.json`, per-eval grading, optional `review.html`) |
| [`baseline/`](baseline/) | Pinned compare reference (`benchmark.json` from `--save-baseline` or `--save-baseline-only`) |
| [`review-template.html`](review-template.html) | Static HTML shell for review generation |
| [`scripts/skill_eval/`](scripts/skill_eval/) | Importable harness package (config, responses, grader, benchmark, report, review, workspace) |
| [`scripts/run_eval_harness.py`](scripts/run_eval_harness.py) | CLI entry (thin shim over `skill_eval.runner`) |
| [`scripts/grade_eval_output.py`](scripts/grade_eval_output.py) | Grader CLI shim |
| [`scripts/generate_review.py`](scripts/generate_review.py) | Review HTML shim |
| [`trigger-eval-set.json`](trigger-eval-set.json) | Description optimization queries (skill-creator loop) |

`latest/` and `baseline/` are regenerated locally and gitignored (like `output/`).

## Stage naming

Eval expectations and skills use **canonical stage labels** from [`infrastructure/core/pipeline/pipeline.yaml`](../../../infrastructure/core/pipeline/pipeline.yaml) via [`stage_vocabulary.py`](../../../infrastructure/core/pipeline/stage_vocabulary.py) — e.g. **Project Analysis**, not numeric stage indices. Script entrypoints (`02_run_analysis.py`) are valid aliases.

## Recommended workflows

| Intent | Command |
| --- | --- |
| Full run + review + pin baseline | `uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --write-review --save-baseline` |
| Pin baseline from last run (no re-grade) | `uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --save-baseline-only` |
| Compare last run vs baseline (no re-grade) | `uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --compare-only` |
| Compare + refresh review HTML | `uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --compare-only --write-review` |
| Pin baseline then compare (no re-grade) | `uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --save-baseline-only --compare-only` |
| CI regression gate | `uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --write-review --fail-under 0.96` |

Default stdout is a human-readable summary table (eval names, pass rates, failed expectations, artifact paths). Progress lines go to stderr (`[12/54] eval · mode · passed/total`) on **full runs only**; offline modes skip re-grading.

| Flag | Output |
| --- | --- |
| *(default)* | ASCII report on stdout; progress on stderr; writes to `latest/` |
| `--output-dir PATH` | Override run directory (default: `latest/`) |
| `--verbose` / `-v` | Also print benchmark summary JSON after the report |
| `--json` | Benchmark `summary` JSON only (CI/scripting) |
| `--compare` | Append with_skill delta vs `baseline/benchmark.json` (full run) |
| `--save-baseline` | Copy `latest/benchmark.json` to `baseline/benchmark.json` after a full run |
| `--save-baseline-only` | Pin baseline from existing workspace without re-grading |
| `--compare-only` | Print report + COMPARE section from existing workspace (requires `baseline/`) |
| `--fail-under RATE` | Exit 1 if positive-only with_skill rate &lt; RATE (0–1) |
| `--write-review` | Generate `review.html` in the run directory |

Standalone review HTML (defaults to `latest/`):

```bash
uv run python docs/prompts/_skill-eval/scripts/generate_review.py
```

## Tests

```bash
uv run pytest tests/infra_tests/skills/test_skill_eval_grader.py tests/infra_tests/skills/test_skill_eval_report.py tests/infra_tests/skills/test_skill_eval_workspace.py tests/infra_tests/skills/test_skill_eval_runner_offline.py tests/infra_tests/core/test_stage_vocabulary.py -q
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub and skill roster
- [`../../../infrastructure/core/pipeline/stage_vocabulary.py`](../../../infrastructure/core/pipeline/stage_vocabulary.py)
