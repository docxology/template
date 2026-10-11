---
name: template-textbook
description: Authored textbook and separate draft scaffolding — units, chapters, labs, question banks, deterministic figures, and completion checks.
version: 0.1.0
author: docxology
license: Apache-2.0 AND CC-BY-4.0
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
# Canonical acceptance gate (requires zero draft markers in every configured section)
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
- **Choose the audit mode deliberately.** The default audit validates structural drafts;
  canonical acceptance uses `--require-complete` across chapters, companions,
  front matter, and reference sections. Execute authored Python examples and
  preserve source custody.
- **Run from the repo root.** Commands assume the template monorepo root
  as working directory unless the child `AGENTS.md` states otherwise.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Exemplar roster: [`projects/AGENTS.md`](../../../../../AGENTS.md)
