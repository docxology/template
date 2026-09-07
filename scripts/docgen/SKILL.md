---
name: template-docgen
version: 1.0.0
description: >
  Derived documentation generators for the template research framework.
  Scripts that write to docs/_generated/ and update in-place doc blocks.
tags:
  - docs
  - generation
  - template
trigger: "generate docs|generate api reference|generate stage table|generate active projects|docgen"
---

# template-docgen

Documentation generation scripts under `scripts/docgen/`.

## When to use

Load this skill when you need to regenerate derived documentation:
- Stage table in `docs/_generated/`
- API reference from `__all__`
- Active projects doc
- Architecture overview
- Counts and measured facts

## Scripts

```bash
uv run python scripts/docgen/stage_table.py
uv run python scripts/docgen/api_reference.py --write
uv run python scripts/docgen/active_projects.py --write
uv run python scripts/docgen/architecture_overview.py --write
uv run python scripts/docgen/counts.py --write
```

## Pitfalls

- Run after any change to `infrastructure/core/pipeline/pipeline.yaml`.
- `api_reference.py --check` is run in CI — do not break exports.
- Generated files in `docs/_generated/` must not be hand-edited.
