---
name: template-storybook
description: Full-page illustrated storybook exemplar — symbolic shape-family characters, page-level raster scenes, text overlays, deterministic PDF assembly.
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, storybook, illustration, thin-orchestrator]
---

# template-storybook

Project-scoped skill for the in-repo exemplar at
`projects/templates/template_storybook/`. Load this when working inside the project.

## When to Use

- Working inside the `template_storybook` exemplar — running scripts, editing story
  content, or regenerating illustrated pages.
- Forking this exemplar as the starting scaffold for a new illustrated-PDF project.
- Validating that the exemplar's contracts (thin-orchestrator, layer boundaries,
  no-mocks testing) still hold after changes.

## Workflow

1. Read the project `AGENTS.md`.
2. Edit story content in `content/story.yaml`.
3. Put rendering behavior in `src/storybook/` (`models.py`, `characters.py`,
   `story.py`, `illustration.py`, `rendering.py`) — never in `scripts/`.
4. Verify with tests and Stage-02 PDF generation.

## Quick Reference

```bash
# From the repository root
uv run pytest projects/templates/template_storybook/tests --cov=projects/templates/template_storybook/src --cov-fail-under=90
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_storybook
uv run python scripts/pipeline/stage_03_render.py --project templates/template_storybook
uv run python scripts/pipeline/stage_04_validate.py --project templates/template_storybook
uv run python scripts/pipeline/stage_05_copy.py --project templates/template_storybook
```

## Pitfalls

- **Keep scripts thin.** Character construction, image composition, text
  overlay, and PDF assembly belong in `src/storybook/`, not in `scripts/`.
- **No mocks.** All tests must use real data, real files, and real
  computation.
- **Outputs are disposable.** Never hand-edit `output/` — regenerate from
  `content/story.yaml` and source.
- **Run from the repo root.** Commands assume the template monorepo root
  as working directory unless the child `AGENTS.md` states otherwise.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- Exemplar roster: [`projects/AGENTS.md`](../../../../AGENTS.md)
