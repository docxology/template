---
name: template-validation-quality
description: |
  Run validation CLI, prerender, markdown/PDF/integrity gates, and QA workflows for the
  Research Project Template. USE WHEN validate manuscript, check PDF for ?? refs, prerender
  gate, link checker, output integrity, or pre-commit validation — even without
  validation_quality prompt.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: verified_only
  task_type: outcome-gradable
  modes:
    - prerender
    - markdown
    - pdf
    - integrity
  related_skills:
    - template-manuscript-cross-references
    - template-manuscript-claim-verification
---

# Validation quality

Prefer **actual CLI entrypoints** in [`CLAUDE.md`](../../../CLAUDE.md) — not illustrative Python stubs.

## Natural invoke

- "Validate markdown under projects/templates/template_prose_project/manuscript/"
- "PDF has unresolved references — run validation"
- "Strict prerender before render"

## Inputs to confirm

- **Target** — manuscript dir, PDF path, or `output/<project>/`.
- **Project** — from active_projects when path ambiguous.

## Workflow

1. **Source markdown** — `infrastructure.validation.cli markdown` and/or `prerender`.

2. **Citations** — `infrastructure.reference.citation validate` on `.bib`.

3. **Links** — `infrastructure.validation.cli links --repo-root .`

4. **PDF** — after render: `cli pdf output/<project>/pdf/`

5. **Integrity** — `cli integrity output/<project>/`

6. **Report** — diagnostic codes from validation; path + fix per issue.

## Deliverables

- Command list with exit codes
- Issue table: code | file | message | fix

## Verification commands

```bash
uv run python -m infrastructure.validation.cli prerender projects/<project>/manuscript --repo-root .
uv run python -m infrastructure.validation.cli markdown projects/<project>/manuscript --repo-root . --strict
uv run python -m infrastructure.reference.citation validate projects/<project>/manuscript/references.bib
uv run python -m infrastructure.validation.cli links --repo-root .
uv run python -m infrastructure.validation.cli pdf output/<project>/pdf/
uv run python -m infrastructure.validation.cli integrity output/<project>/
uv run python -m infrastructure.prose.cli report projects/<project>/manuscript
```

## When NOT to use

- **Failing pipeline stage triage** → [pipeline-debugging](../pipeline-debugging/SKILL.md)
- **Claim-by-claim manuscript audit** → [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md)

## References

- [`infrastructure/validation/AGENTS.md`](../../../infrastructure/validation/AGENTS.md)
