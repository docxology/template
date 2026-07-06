---
name: template-docgen
version: 1.0.0
description: >
  Derived documentation generators for the template research framework.
  Scripts that write to docs/_generated/ and update in-place doc blocks.
  Currently at scripts/ root; this directory is the planned migration target.
tags:
  - docs
  - generation
  - template
trigger: "generate docs|generate api reference|generate stage table|generate active projects|docgen"
---

# template-docgen

Documentation generation scripts (stub subdirectory).

## When to use

Load this skill when you need to regenerate derived documentation:
- Stage table in `docs/_generated/`
- API reference from `__all__`
- Active projects doc
- Architecture overview

## Scripts (currently at scripts/ root)

```bash
uv run python scripts/docgen/stage_table.py
uv run python scripts/docgen/api_reference.py [--check]
uv run python scripts/docgen/active_projects.py
uv run python scripts/docgen/architecture_overview.py
```

## Pitfalls

- Run after any change to `infrastructure/core/pipeline/pipeline.yaml`.
- `generate_api_reference_doc.py --check` is run in CI — do not break exports.
- Generated files in `docs/_generated/` must not be hand-edited.
