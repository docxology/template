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
# Canonical fresh-clone gate: provisions the project's isolated dependencies.
uv run python scripts/pipeline/stage_01_test.py --project templates/template_literature_meta_analysis --project-only
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
- **Use the Stage-01 test command from the monorepo root.** A direct root
  `pytest` invocation does not provision this exemplar's scientific
  dependencies.
- **Outputs are disposable.** Never hand-edit `output/` — regenerate from
  source and config.
- **Run from the repo root.** Commands assume the template monorepo root
  as working directory unless the child `AGENTS.md` states otherwise.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Exemplar roster: [`projects/AGENTS.md`](../../../../../AGENTS.md)
