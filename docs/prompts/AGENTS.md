# AI workflow skills (`docs/prompts/`)

## Overview

Agent-routable workflow skills for the Research Project Template. Each workflow is a subdirectory with `SKILL.md` (YAML `name` + `description`). The hub skill at [`SKILL.md`](SKILL.md) routes ambiguous requests.

Discovered by `infrastructure.skills` via root `docs/prompts` in `DEFAULT_SKILL_SEARCH_ROOTS`.

## Skills

| Directory | Skill `name` | Purpose |
| --- | --- | --- |
| [`SKILL.md`](SKILL.md) | `template-workflows` | Hub router |
| [`code-development/`](code-development/SKILL.md) | `template-code-development` | Standards-compliant code |
| [`test-creation/`](test-creation/SKILL.md) | `template-test-creation` | No-mocks tests |
| [`feature-addition/`](feature-addition/SKILL.md) | `template-feature-addition` | Cross-layer features |
| [`refactoring/`](refactoring/SKILL.md) | `template-refactoring` | Refactors with migration |
| [`infrastructure-module/`](infrastructure-module/SKILL.md) | `template-infrastructure-module` | New `infrastructure/*` packages |
| [`documentation-creation/`](documentation-creation/SKILL.md) | `template-documentation-creation` | AGENTS.md / README.md |
| [`validation-quality/`](validation-quality/SKILL.md) | `template-validation-quality` | Validation CLI / gates |
| [`comprehensive-assessment/`](comprehensive-assessment/SKILL.md) | `template-comprehensive-assessment` | Full checkout audit |
| [`reproducibility-audit/`](reproducibility-audit/SKILL.md) | `template-reproducibility-audit` | Determinism before release |
| [`pipeline-debugging/`](pipeline-debugging/SKILL.md) | `template-pipeline-debugging` | DAG stage triage |
| [`manuscript-creation/`](manuscript-creation/SKILL.md) | `template-manuscript-creation` | Manuscript + project scaffold |
| [`manuscript-cross-references/`](manuscript-cross-references/SKILL.md) | `template-manuscript-cross-references` | Registry/token cross-refs |
| [`manuscript-claim-verification/`](manuscript-claim-verification/SKILL.md) | `template-manuscript-claim-verification` | Triple-check claims |
| [`literature-synthesis/`](literature-synthesis/SKILL.md) | `template-literature-synthesis` | LLM synthesis blocks |

## Skill anatomy

Each child skill directory ships **`README.md`** (quick nav) and **`AGENTS.md`** (technical index) in addition to **`SKILL.md`** (routable workflow). Optional `references/` subdirs carry the same doc pair when they hold checklist files.

Each child `SKILL.md` includes: natural invoke examples, inputs, workflow, deliverables, verification commands, when NOT to use, references.

## Eval workspace

[`_skill-eval/`](_skill-eval/) holds `evals/evals.json`, regenerated harness output under `latest/` (benchmark + review HTML), optional pinned `baseline/` for compare, and the importable [`scripts/skill_eval/`](_skill-eval/scripts/skill_eval/) package. Measured synthetic benchmark: **100%** with_skill, **100%** positive-only (keyword grader over extracted skill sections).

| Intent | Command |
| --- | --- |
| Full run + review + pin baseline | `uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --write-review --save-baseline` |
| Pin baseline (no re-grade) | `uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --save-baseline-only` |
| Compare vs baseline (no re-grade) | `uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --compare-only` |
| CI regression gate | `uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --write-review --fail-under 0.96` |

Machine-readable summary: `--json`. Standalone review HTML: `uv run python docs/prompts/_skill-eval/scripts/generate_review.py`.

Harness is synthetic (extracts skill sections + keyword grader), not live agent runs. Stage names in evals/skills follow canonical labels from `pipeline.yaml` (see [`stage_vocabulary.py`](../../infrastructure/core/pipeline/stage_vocabulary.py)), not numeric stage indices. Grader unit tests: `tests/infra_tests/skills/test_skill_eval_grader.py`; report formatter: `tests/infra_tests/skills/test_skill_eval_report.py`; workspace loader and offline CLI: `test_skill_eval_workspace.py`, `test_skill_eval_runner_offline.py`. Full eval workspace reference: [`_skill-eval/AGENTS.md`](_skill-eval/AGENTS.md).

The `_skill-eval/` tree is **excluded** from `lint_docs.py` cross-link and doc-pair lint (regenerated fixture outputs with intentionally wrong relative links — same policy as `output/` and `docs/_generated/`).

Description optimization trigger set: [`_skill-eval/trigger-eval-set.json`](_skill-eval/trigger-eval-set.json) (requires skill-creator `run_loop` + `claude -p` on skill **directory**).

## Conventions

- Exemplar: [`projects/template_code_project/`](../../projects/template_code_project/); active names → [`../_generated/active_projects.md`](../_generated/active_projects.md).
- Manuscript: Pandoc-crossref vs registry tokens — skills state which applies.
- Thin orchestrator + no mocks enforced in every workflow skill.

## See also

- [README.md](README.md) — user-facing index
- [`infrastructure/skills/AGENTS.md`](../../infrastructure/skills/AGENTS.md) — discovery API
- [`../development/contributing.md`](../development/contributing.md)
