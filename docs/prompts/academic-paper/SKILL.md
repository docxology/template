---
name: template-academic-paper
description: |
  Template-native manuscript planning, outline, drafting, revision, formatting, citation
  check, and AI-use disclosure routing. USE WHEN the user asks to write, outline, revise,
  format, or prepare a paper inside the Research Project Template.
metadata:
  version: "1.0.0"
  last_updated: "2026-05-25"
  status: active
  data_access_level: redacted
  task_type: open-ended
  modes:
    - plan
    - outline
    - full
    - revision
    - format
    - citation-check
    - disclosure
  related_skills:
    - template-manuscript-creation
    - template-manuscript-cross-references
    - template-manuscript-claim-verification
    - template-academic-paper-reviewer
---

# Academic paper

Template-native paper workflow. It uses project manuscript sources, generated
variables, validation gates, and evidence registries rather than a copied external
academic agent prompt.

## Natural invoke

- "Help me plan this paper"
- "Write the outline and methods section from these artifacts"
- "Revise the manuscript after reviewer comments"
- "Check citations and convert the final paper format"
- "Write an AI-use disclosure tied to the repo evidence"

## Inputs to confirm

- **Project** - resolve through `docs/_generated/active_projects.md`.
- **Mode** - plan, outline, full, revision, format, citation-check, or disclosure.
- **Manuscript style** - Pandoc-crossref or registry tokens; do not mix styles.
- **Evidence sources** - generated variables, claim ledger, figures, tables, references, validation reports.

## Workflow

1. **Plan first when uncertain** - capture target venue, paper type, contribution, section map, and unresolved material gaps.
2. **Draft from artifacts** - write against `projects/<project>/manuscript/`, generated variables, figure captions, and citekeys; use `[MATERIAL GAP]` instead of fabricating missing evidence.
3. **Preserve injected values** - prefer `[[VAR:...]]`, registry-backed labels, citekeys, and project-defined cross-reference tokens over hard-coded numbers.
4. **Validate continuously** - run prerender, markdown, citation, PDF, and integrity checks appropriate to the mode.
5. **Handoff for review** - use [academic-paper-reviewer](../academic-paper-reviewer/SKILL.md) for read-only critique; use claim verification before finalization.

## Deliverables

- Plan mode: section outline, evidence map, unresolved gaps, and commands to validate.
- Full/revision mode: source-layer manuscript edits, response notes, and validation status.
- Format/citation mode: citation audit, render-safe changes, and output paths.
- Disclosure mode: concise AI-use disclosure grounded in project evidence and human review checkpoints.

## Verification commands

```bash
uv run python -m infrastructure.validation.cli prerender projects/<project>/manuscript --repo-root .
uv run python -m infrastructure.reference.citation validate projects/<project>/manuscript/references.bib
uv run python -m infrastructure.validation.cli markdown projects/<project>/manuscript --repo-root . --strict
uv run python -m infrastructure.validation.cli integrity output/<project>/
```

## References

- [MODE_REGISTRY.md](../MODE_REGISTRY.md)
- [manuscript-creation](../manuscript-creation/SKILL.md)
- [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md)
