---
name: template-literature-meta-analysis
description: "Literature meta-analysis exemplar — multi-engine retrieval, dedup, full-text, bibliometrics, embeddings, optional knowledge graph. Default term: modafinil."
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, literature, meta-analysis, bibliometrics]
---

# template-literature-meta-analysis

Project-scoped skill for the in-repo exemplar at
`projects/templates/template_literature_meta_analysis/`. Load this when working inside the project.

## When to Use

- Working inside the `template_literature_meta_analysis` exemplar — running scripts, editing source,
  or regenerating outputs.
- Forking this exemplar as the starting scaffold for a new research project.
- Validating that the exemplar's contracts (thin-orchestrator, layer boundaries,
  no-mocks testing) still hold after changes.

## Quick Reference

```bash
# From the repository root
uv run pytest projects/templates/template_literature_meta_analysis/tests --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_literature_meta_analysis
uv run python scripts/pipeline/stage_03_render.py --project templates/template_literature_meta_analysis
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_literature_meta_analysis
uv run python scripts/pipeline/stage_05_copy.py --project templates/template_literature_meta_analysis
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
