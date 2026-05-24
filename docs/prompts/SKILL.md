---
name: template-workflows
description: |
  Router and workflow hub for the Research Project Template — code, tests, manuscripts,
  pipeline, validation, docs, and reproducibility. USE WHEN the user wants to audit the
  repo, debug ./run.sh or execute_pipeline.py, add a feature, write tests, scaffold a
  manuscript, verify claims, fix cross-references, run validation gates, refactor, or
  prepare a Zenodo release — even if they never say "prompt", "skill", or docs/prompts.
  Also USE WHEN intent is ambiguous ("something wrong with my manuscript", "full health
  check", "fix the pipeline") — pick ONE child skill from the routing table and follow it.
  Do NOT use for generic homework, unrelated app security scans, or casual PDF summarization.
---

# Template workflow hub

When intent is clear, open the matching child `SKILL.md` directly. When ambiguous, use the routing table, then load exactly one child skill.

## Ambiguous routing

- **Broken refs / "manuscript wrong"** — ask whether the failure is pipeline (validate/render) or prose (tokens/registry). Route to [manuscript-cross-references](manuscript-cross-references/SKILL.md), [validation-quality](validation-quality/SKILL.md), or [manuscript-claim-verification](manuscript-claim-verification/SKILL.md). Do **not** open [code-development](code-development/SKILL.md).
- **Example:** "refs broken, not sure if pipeline or prose" → clarify stage vs registry; default to cross-refs when `[[FIG:]]` / `labels.yaml` mentioned.
- **Full health check with no symptom** → [comprehensive-assessment](comprehensive-assessment/SKILL.md).
- **Generic coding homework or unrelated app** → do not load template workflow skills.

## Routing table

| Symptom or goal | Child skill |
| --- | --- |
| Pipeline stage failed, stuck, or flaky | [pipeline-debugging/SKILL.md](pipeline-debugging/SKILL.md) |
| Regenerate-from-clean / determinism / double-run diff | [reproducibility-audit/SKILL.md](reproducibility-audit/SKILL.md) |
| Triple-check every manuscript claim; pre-submission | [manuscript-claim-verification/SKILL.md](manuscript-claim-verification/SKILL.md) |
| `[[FIG:]]` / `labels.yaml` registry audit | [manuscript-cross-references/SKILL.md](manuscript-cross-references/SKILL.md) |
| New manuscript + project from research brief | [manuscript-creation/SKILL.md](manuscript-creation/SKILL.md) |
| Literature search corpus synthesis (LLM blocks) | [literature-synthesis/SKILL.md](literature-synthesis/SKILL.md) |
| Full repo audit (tests, docs, manuscript, pipeline) | [comprehensive-assessment/SKILL.md](comprehensive-assessment/SKILL.md) |
| Validation CLI, gates, markdown/PDF checks | [validation-quality/SKILL.md](validation-quality/SKILL.md) |
| New module or algorithm (thin orchestrator) | [code-development/SKILL.md](code-development/SKILL.md) |
| Tests under no-mocks policy | [test-creation/SKILL.md](test-creation/SKILL.md) |
| End-to-end feature across layers | [feature-addition/SKILL.md](feature-addition/SKILL.md) |
| Clean-break refactor with migration | [refactoring/SKILL.md](refactoring/SKILL.md) |
| New `infrastructure/*` package | [infrastructure-module/SKILL.md](infrastructure-module/SKILL.md) |
| AGENTS.md / README.md for a directory | [documentation-creation/SKILL.md](documentation-creation/SKILL.md) |

**New project scaffold (one-shot):** [docs/guides/new-project-one-shot-prompt.md](../guides/new-project-one-shot-prompt.md) — not a separate skill; link from manuscript-creation when starting from zero.

## Conventions (all children)

- Project names: [`docs/_generated/active_projects.md`](../_generated/active_projects.md) — never hard-code rotating paths.
- Business logic: `infrastructure/` or `projects/<name>/src/` only; scripts orchestrate.
- Tests: no mocks; infra ≥60%, project ≥90% unless CI documents an exception.
- Metrics: measure with pytest or cite [`docs/_generated/canonical_facts.md`](../_generated/canonical_facts.md).

## Discovery

These skills are indexed in `.cursor/skill_manifest.json` (`uv run python -m infrastructure.skills write`). Human index: [README.md](README.md).
