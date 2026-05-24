---
name: template-manuscript-creation
description: |
  Scaffold a research manuscript and project layout from a research brief — sections,
  config.yaml, src/, scripts/, tests. USE WHEN starting a new paper, new projects/ tree,
  manuscript from topic description, or aligning with template_code_project exemplar — even
  without copy-paste prompts.
---

# Manuscript creation

## Natural invoke

- "Create a new optimization research project and manuscript from this brief"
- "Scaffold projects/my_topic/ like template_code_project"
- "I have a research idea — set up manuscript + src + tests"

## Inputs to confirm

- **Research topic** — objectives, methods, expected contributions (user provides).
- **Exemplar** — default [`projects/template_code_project/`](../../../projects/template_code_project/); prose → `template_prose_project`; search → local `template_search_project` from archive.
- **Cross-ref style** — Pandoc-crossref vs registry tokens (pick one; see [manuscript-cross-references](../manuscript-cross-references/SKILL.md)).

## Workflow

1. **Copy exemplar shape** — match section numbering (`01_*` vs `00_*`), not generic skeleton if exemplar differs.

2. **Manuscript files** — `config.yaml`, `preamble.md`, `references.bib`, ordered `*.md` sections, glossary/references as exemplar does.

3. **Cross-refs** — Pandoc: `@fig:`, `@eq:`, `@sec:`, `[@key]` per [`docs/guides/manuscript-semantics.md`](../../guides/manuscript-semantics.md). Registry: `refs/labels.yaml` + `[[FIG:]]` tokens.

4. **`src/`** — typed public APIs, `get_logger`, fixed seeds, custom exceptions where needed.

5. **`scripts/`** — thin orchestrators only; `MPLBACKEND=Agg`; print output paths.

6. **`tests/`** — no mocks; ≥90% on `projects/<name>/src`.

7. **Docs** — project AGENTS.md + README.md; link active_projects doc, do not hard-code roster.

8. **One-shot alternative** — for LLM scaffold of entire tree, see [`docs/guides/new-project-one-shot-prompt.md`](../../guides/new-project-one-shot-prompt.md).

## Deliverables

- Full `projects/<name>/` tree or delta from brief
- How to run: `uv run pytest projects/<name>/tests/ --cov=...` and `uv run python scripts/01_run_tests.py --project <name>`

## Verification commands

```bash
uv sync
uv run python scripts/01_run_tests.py --project <name>
uv run python -m infrastructure.validation.cli markdown projects/<name>/manuscript/
```

## When NOT to use

- **Existing manuscript claim audit** → [manuscript-claim-verification](../manuscript-claim-verification/SKILL.md)
- **Cross-ref-only fixes** → [manuscript-cross-references](../manuscript-cross-references/SKILL.md)

## References

Section checklist and legacy examples: [references/structure-checklist.md](references/structure-checklist.md)
