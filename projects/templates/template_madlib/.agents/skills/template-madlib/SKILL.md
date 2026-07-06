---
name: template-madlib
description: Deterministic token-injection manuscript generator — config-owned lexicon, conditional IMRAD, QA probes, authoring contract, and token provenance.
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, madlib, token-injection, imrad]
---

# template-madlib

Project-scoped skill for the in-repo exemplar at
`projects/templates/template_madlib/`. Load this when working inside the project.

## When to Use

- Working inside the `template_madlib` exemplar — running scripts, editing source,
  or regenerating outputs.
- Forking this exemplar as the starting scaffold for a new research project.
- Validating that the exemplar's contracts (thin-orchestrator, layer boundaries,
  no-mocks testing) still hold after changes.

## Quick Reference

```bash
# From the repository root
uv run pytest projects/templates/template_madlib/tests --cov=projects/templates/template_madlib/src --cov-fail-under=90
uv run python scripts/02_run_analysis.py --project templates/template_madlib
uv run python scripts/03_render_pdf.py --project templates/template_madlib
uv run python scripts/04_validate_output.py --project templates/template_madlib
uv run python scripts/05_copy_outputs.py --project templates/template_madlib
```

## Pitfalls

- **Keep scripts thin.** Business logic belongs in `src/` modules (`run.py`, `composition_*`, `figure_specs`, `analysis_*`), not in `scripts/`.
- **Import surface.** Prefer `composition.py` re-exports in tests; edit split modules for body/table/figure changes.
- **No mocks.** All tests must use real data, real files, and real computation.
- **Outputs are disposable.** Never hand-edit `output/` — regenerate from
  source and config.
- **Run from the repo root.** Commands assume the template monorepo root
  as working directory unless the child `AGENTS.md` states otherwise.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Exemplar roster: [`projects/AGENTS.md`](../../../../AGENTS.md)
