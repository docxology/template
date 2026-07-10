---
name: template-data-descriptor
description: FAIR data descriptor exemplar for schema, provenance, license, and dataset release-readiness validation.
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, data, fair, provenance]
---

# template-data-descriptor

Load this skill when working inside `projects/templates/template_data_descriptor/`.

## When to Use

- Creating or reviewing a dataset descriptor project.
- Validating schema, file inventory, provenance, and license boundaries.
- Forking a FAIR data-paper scaffold.

## Quick Reference

```bash
uv run pytest projects/templates/template_data_descriptor/tests --cov=projects/templates/template_data_descriptor/src --cov-fail-under=90
uv run python scripts/pipeline/stage_01_test.py --project templates/template_data_descriptor --project-only
```

## Pitfalls

- Keep claims about the data package, not unsupported scientific effects.
- Do not commit restricted raw data to this public exemplar.
