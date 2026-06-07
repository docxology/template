# AI workflow skills (`docs/prompts/`)

## Overview

Agent-routable workflow skills for the Research Project Template. Each workflow is a subdirectory with `SKILL.md` (YAML `name`, `description`, and workflow `metadata`). The hub skill at [`SKILL.md`](SKILL.md) routes ambiguous requests, and [`MODE_REGISTRY.md`](MODE_REGISTRY.md) is the compact mode/metadata map.

Discovered by `infrastructure.skills` via root `docs/prompts` in `DEFAULT_SKILL_SEARCH_ROOTS`.

## Skills

| Directory | Skill `name` | Purpose |
| --- | --- | --- |
| [`SKILL.md`](SKILL.md) | `template-workflows` | Hub router |
| [`deep-research/`](deep-research/SKILL.md) | `template-deep-research` | Research intake, source discovery, fact-checking |
| [`academic-paper/`](academic-paper/SKILL.md) | `template-academic-paper` | Paper planning, drafting, revision, formatting |
| [`academic-paper-reviewer/`](academic-paper-reviewer/SKILL.md) | `template-academic-paper-reviewer` | Read-only peer review and re-review |
| [`academic-pipeline/`](academic-pipeline/SKILL.md) | `template-academic-pipeline` | Research-to-publication orchestration |
| [`methods-orchestration/`](methods-orchestration/SKILL.md) | `template-methods-orchestration` | Methods, stage contracts, artifacts, evidence |
| [`code-development/`](code-development/SKILL.md) | `template-code-development` | Standards-compliant code |
| [`test-creation/`](test-creation/SKILL.md) | `template-test-creation` | No-mocks tests |
| [`feature-addition/`](feature-addition/SKILL.md) | `template-feature-addition` | Cross-layer features |
| [`refactoring/`](refactoring/SKILL.md) | `template-refactoring` | Refactors with migration |
| [`infrastructure-module/`](infrastructure-module/SKILL.md) | `template-infrastructure-module` | New `infrastructure/*` packages |
| [`documentation-creation/`](documentation-creation/SKILL.md) | `template-documentation-creation` | AGENTS.md / README.md |
| [`agentic-use/`](agentic-use/SKILL.md) | `template-agentic-use` | Skill inventory, routing, external companion review |
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

Each `docs/prompts/**/SKILL.md` also carries contract metadata validated by:

```bash
uv run python -m infrastructure.skills check-contracts
```

Required fields: `metadata.version`, `metadata.last_updated`, `metadata.status`,
`metadata.data_access_level`, `metadata.task_type`, `metadata.modes`, and
`metadata.related_skills`.

## Adding or changing a workflow skill

When a new `docs/prompts/<skill>/SKILL.md` is added, removed, renamed, or given
new routing semantics, keep the whole agent-facing surface synchronized in the
same change:

1. Create or update the child directory's `SKILL.md`, `README.md`, and
   `AGENTS.md` (and the same doc pair under `references/` when reference files
   are added).
2. Update the hub routing table in [`SKILL.md`](SKILL.md) and keep ambiguous
   routing examples specific enough that agents choose one child skill.
3. Update [`MODE_REGISTRY.md`](MODE_REGISTRY.md) when modes, handoffs,
   oversight level, or data-access semantics change.
4. Update [`README.md`](README.md) if the human-facing skill inventory changes.
5. Add or adjust eval cases in `_skill-eval/evals/evals.json` and
   `_skill-eval/trigger-eval-set.json` when a new trigger phrase or routing
   boundary matters.
6. Regenerate generated skill artifacts:

   ```bash
   uv run python -m infrastructure.skills write
   uv run python -m infrastructure.skills write-index
   ```

7. Verify contracts, discovery, evals, and links:

   ```bash
   uv run python -m infrastructure.skills check
   uv run python -m infrastructure.skills check-contracts
   uv run pytest tests/infra_tests/skills -q
   uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --write-review --fail-under 0.96
   uv run python scripts/lint_docs.py --json --repo-root .
   ```

Avoid editing `docs/_generated/skills_index.md` or `.cursor/skill_manifest.json`
by hand; both are generated from live `SKILL.md` discovery.

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

Academic workflow design is original to this repo, with attribution to
[Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
for the public ideas of mode registries, data-access labels, provenance checkpoints, and
benchmark disclosure. Do not copy ARS prompt bodies, scripts, or schemas into this
Apache-2.0 repository.

Description optimization trigger set: [`_skill-eval/trigger-eval-set.json`](_skill-eval/trigger-eval-set.json) (requires skill-creator `run_loop` + `claude -p` on skill **directory**).

## Conventions

- Exemplar: [`projects/templates/template_code_project/`](../../projects/templates/template_code_project/); active names → [`../_generated/active_projects.md`](../_generated/active_projects.md).
- Manuscript: Pandoc-crossref vs registry tokens — skills state which applies.
- Thin orchestrator + no mocks enforced in every workflow skill.

## See also

- [README.md](README.md) — user-facing index
- [`infrastructure/skills/AGENTS.md`](../../infrastructure/skills/AGENTS.md) — discovery API
- [`../development/contributing.md`](../development/contributing.md)
