# Skill Eval Workspace

This directory contains the offline, synthetic benchmark harness for the
template workflow skills. It is a maintainer workspace, not a discoverable
workflow skill.

## Contents

| Path | Role |
| --- | --- |
| [`evals/evals.json`](evals/evals.json) | Benchmark cases and expectation metadata. |
| [`scripts/run_eval_harness.py`](scripts/run_eval_harness.py) | Main CLI for full runs, baseline pinning, and comparisons. |
| [`scripts/grade_eval_output.py`](scripts/grade_eval_output.py) | Grader CLI shim (grade an existing response without re-running the harness). |
| [`scripts/skill_eval/`](scripts/skill_eval/) | Importable harness implementation. |
| [`baseline/benchmark.json`](baseline/benchmark.json) | Pinned comparison baseline when present. |
| [`latest/`](latest/) | Regenerated local run output. |
| [`review-template.html`](review-template.html) | Static HTML template for review output. |

## Common Commands

```bash
uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --write-review --save-baseline
uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --compare-only
uv run python docs/prompts/_skill-eval/scripts/generate_review.py
```

Targeted regression tests:

```bash
uv run pytest tests/infra_tests/skills/test_skill_eval_grader.py tests/infra_tests/skills/test_skill_eval_report.py tests/infra_tests/skills/test_skill_eval_workspace.py tests/infra_tests/skills/test_skill_eval_runner_offline.py tests/infra_tests/core/test_stage_vocabulary.py -q
```

`latest/` and generated response fixtures are excluded from repository
cross-link and doc-pair lint because they intentionally mirror harness output.
The authored workspace reference is [`AGENTS.md`](AGENTS.md).
