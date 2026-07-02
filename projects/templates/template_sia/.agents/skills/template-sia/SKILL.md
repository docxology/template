---
name: template-sia
description: SIA (Self-Improvement Agent) harness exemplar — Meta/Target/Feedback loops, public/private splits, fixture replay, fail-closed validation.
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, sia, self-improvement, harness]
---

# template-sia

Project-scoped skill for the in-repo exemplar at
`projects/templates/template_sia/`. Load this when working inside the project.

## When to Use

- Working inside the `template_sia` exemplar — running scripts, editing source,
  or regenerating outputs.
- Forking this exemplar as the starting scaffold for a new research project.
- Validating that the exemplar's contracts (thin-orchestrator, layer boundaries,
  no-mocks testing) still hold after changes.

## Quick Reference

```bash
# From the repository root
uv run pytest projects/templates/template_sia/tests --cov=projects/templates/template_sia/src --cov-fail-under=90
uv run python scripts/02_run_analysis.py --project templates/template_sia
uv run python scripts/03_render_pdf.py --project templates/template_sia
uv run python scripts/04_validate_output.py --project templates/template_sia
uv run python scripts/05_copy_outputs.py --project templates/template_sia
```

## Pitfalls

- **Keep scripts thin.** Business logic belongs in `src/` or shared
  `infrastructure/`, not in `scripts/`.
- **No mocks.** All tests must use real data, real files, and real
  computation.
- **Outputs are disposable.** Never hand-edit `output/` — regenerate from
  source and config.
- **Run from the repo root.** Commands assume the template monorepo root
  as working directory unless the child `AGENTS.md` states otherwise.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Exemplar roster: [`projects/AGENTS.md`](../../../../AGENTS.md)
