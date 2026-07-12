---
name: template-textbook
description: Modular fillable textbook scaffold — parts/chapters/labs/question banks from config.yaml, auto-numbering, deterministic figures, structural contract enforcement.
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, textbook, scaffold, contract]
---

# template-textbook

Project-scoped skill for the in-repo exemplar at
`projects/templates/template_textbook/`. Load this when working inside the project.

## When to Use

- Working inside the `template_textbook` exemplar — running scripts, editing source,
  or regenerating outputs.
- Forking this exemplar as the starting scaffold for a new research project.
- Validating that the exemplar's contracts (thin-orchestrator, layer boundaries,
  no-mocks testing) still hold after changes.

## Quick Reference

```bash
# From the repository root
uv run pytest projects/templates/template_textbook/tests --cov=projects/templates/template_textbook/src --cov-fail-under=90
# Structural scaffold gate (reports stubs but allows them)
uv run python projects/templates/template_textbook/scripts/audit_textbook_quality.py
# Filled-manuscript gate (fails until every audited section has zero stubs)
uv run python projects/templates/template_textbook/scripts/audit_textbook_quality.py --require-complete
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_textbook
uv run python scripts/pipeline/stage_03_render.py --project templates/template_textbook
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_textbook
uv run python scripts/pipeline/stage_05_copy.py --project templates/template_textbook
```

## Pitfalls

- **Keep scripts thin.** Business logic belongs in `src/` or shared
  `infrastructure/`, not in `scripts/`.
- **No mocks.** All tests must use real data, real files, and real
  computation.
- **Outputs are disposable.** Never hand-edit `output/` — regenerate from
  source and config.
- **Choose the audit mode deliberately.** The default audit validates a fillable
  scaffold; `--require-complete` is the opt-in zero-stub gate for a filled
  manuscript.
- **Run from the repo root.** Commands assume the template monorepo root
  as working directory unless the child `AGENTS.md` states otherwise.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Exemplar roster: [`projects/AGENTS.md`](../../../../../AGENTS.md)
