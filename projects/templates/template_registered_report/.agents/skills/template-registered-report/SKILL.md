---
name: template-registered-report
description: Registered-report exemplar for preregistration locking, deviation ledgers, replication, and confirmatory claim boundaries.
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, preregistration, replication, registered-report]
---

# template-registered-report

Load this skill when working inside `projects/templates/template_registered_report/`.

## When to Use

- Creating or reviewing a preregistered study.
- Auditing deviations between a frozen plan and executed analyses.
- Forking a registered-report scaffold.

## Quick Reference

```bash
uv run pytest projects/templates/template_registered_report/tests --cov=projects/templates/template_registered_report/src --cov-fail-under=90
uv run python scripts/pipeline/stage_01_test.py --project templates/template_registered_report --project-only
```

## Pitfalls

- Do not backfill hypotheses from observed results.
- Label exploratory analyses explicitly.
- Regenerate figures through `scripts/generate_figures.py`; it writes
  `output/figures/figure_registry.json` only after all four registered-report
  figures exist, and supports explicit temp destinations for isolated checks.
