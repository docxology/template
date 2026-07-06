---
name: template-documentation-creation
description: |
  Author or refresh AGENTS.md and README.md for template directories — accurate commands,
  Mermaid where helpful, link _generated/active_projects.md. USE WHEN folder needs AGENTS,
  README audit, doc contract fix, or signposting after code change — even without
  documentation_creation prompt.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: raw
  task_type: open-ended
  modes:
    - author-docs
  related_skills:
    - template-comprehensive-assessment
---

# Documentation creation

## Natural invoke

- "Write AGENTS.md for projects/templates/template_code_project/scripts/"
- "README and AGENTS for new infrastructure package"
- "Fix stale commands in docs/prompts AGENTS.md"

## Inputs to confirm

- **Directory** — path to document.
- **Audience** — AGENTS (technical/API) vs README (quick nav).

## Workflow

1. **Read live code** — list modules, entrypoints, tests; do not invent APIs.

2. **AGENTS.md** — purpose, layout diagram, public functions/signatures or pointers, verification commands, see-also links.

3. **README.md** — short index, quick commands, link to AGENTS.

4. **Cross-links** — relative paths; active project names → [`docs/_generated/active_projects.md`](../../_generated/active_projects.md).

5. **Tone** — understated; show not tell; trim non-semantic adjectives.

6. **Validate** — `uv run python scripts/audit/lint_docs.py` when touching many md files.

## Deliverables

- Updated AGENTS.md + README.md (and SKILL.md if agent-routable folder)

## Verification commands

```bash
uv run python scripts/audit/lint_docs.py
# Spot-check links mentioned in docs resolve
```

## When NOT to use

- **Full repo audit** → [comprehensive-assessment](../comprehensive-assessment/SKILL.md)
- **Manuscript prose** → manuscript skills

## References

- [`docs/rules/documentation_standards.md`](../../rules/documentation_standards.md)
