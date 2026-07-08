---
name: template-search-project
description: Literature-search pipeline exemplar — multi-backend search (arXiv/Crossref), BibTeX generation, deep search, optional LLM synthesis.
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, search, literature, bibtex]
---

# template-search-project

Project-scoped skill for the in-repo exemplar at
`projects/templates/template_search_project/`. Load this when working inside the project.

## When to Use

- Working inside the `template_search_project` exemplar — running scripts, editing source,
  or regenerating outputs.
- Forking this exemplar as the starting scaffold for a new research project.
- Validating that the exemplar's contracts (thin-orchestrator, layer boundaries,
  no-mocks testing) still hold after changes.

## Quick Reference

```bash
# From the repository root
uv run pytest projects/templates/template_search_project/tests --cov=projects/templates/template_search_project/src --cov-fail-under=90
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_search_project
uv run python scripts/pipeline/stage_03_render.py --project templates/template_search_project
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_search_project
uv run python scripts/pipeline/stage_05_copy.py --project templates/template_search_project
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
- Exemplar roster: [`projects/AGENTS.md`](../../../../../AGENTS.md)
