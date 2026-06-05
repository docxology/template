---
name: template-agentic-use
description: |
  Agentic-use and skill-routing workflow for the Research Project Template. USE WHEN
  discovering relevant skills, making template easier for agents to navigate, auditing
  docs/prompts skill coverage, checking .cursor/skill_manifest.json, evaluating external
  skills, or improving agent onboarding/routing without changing project behavior.
metadata:
  version: "1.0.0"
  last_updated: "2026-06-04"
  status: active
  data_access_level: raw
  task_type: open-ended
  modes:
    - inventory
    - route
    - harden
    - external-review
  related_skills:
    - template-workflows
    - template-comprehensive-assessment
    - template-documentation-creation
    - template-validation-quality
---

# Agentic use

## Natural invoke

- "Discover all relevant skills for working with template/"
- "Make this repo easier for agents to navigate"
- "Improve skill routing and eval coverage"
- "Check whether an external skill should be installed or just referenced"

## Inputs to confirm

- **Scope** - skill discovery only, routing docs, or contract/eval hardening.
- **External installs** - default is no install and no vendoring unless explicitly requested.
- **Audience** - local agents, maintainers, or new contributors.

## Workflow

1. **Inventory** - run `uv run python -m infrastructure.skills list-json`, `check`, and `check-contracts`. Use [`docs/_generated/skills_index.md`](../../_generated/skills_index.md) as the human index and `.cursor/skill_manifest.json` as the editor manifest.

2. **Route locally first** - choose `docs/prompts/SKILL.md` ([template-workflows](../SKILL.md)) for broad template work, then exactly one child skill for implementation. Use this skill only for agent onboarding, routing, skill-surface maintenance, and external-skill review.

3. **Harden discoverability** - update the hub routing table, README, mode registry, trigger eval set, and generated manifest/index when the skill surface changes. Avoid unrelated documentation normalization.

4. **Evaluate external skills** - check install count, source reputation, and repository health. Record strong candidates as optional companion skills; do not add external skill directories to this public repo by default.

5. **Verify** - rerun skill checks, skill tests, eval harness, and docs lint before claiming the routing surface is ready.

## Deliverables

- Skill inventory summary with counts and paths.
- Local routing recommendation and any docs/eval updates.
- External companion list with install commands only when requested.
- Commands run with raw exit status.

## Verification commands

```bash
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills check-contracts
uv run pytest tests/infra_tests/skills -q
uv run python docs/prompts/_skill-eval/scripts/run_eval_harness.py --write-review --fail-under 0.96
uv run python scripts/lint_docs.py
```

## When NOT to use

- **Feature implementation** -> [feature-addition](../feature-addition/SKILL.md)
- **One module or algorithm** -> [code-development](../code-development/SKILL.md)
- **Full repo audit** -> [comprehensive-assessment](../comprehensive-assessment/SKILL.md)
- **Manuscript claim repair** -> [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md)

## References

- [`../SKILL.md`](../SKILL.md) - template workflow hub (`docs/prompts/SKILL.md`)
- [`../../_generated/skills_index.md`](../../_generated/skills_index.md) - generated skill index
- [`../../../infrastructure/skills/SKILL.md`](../../../infrastructure/skills/SKILL.md) - discovery and manifest API
