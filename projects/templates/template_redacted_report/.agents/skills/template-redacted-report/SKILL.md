---
name: template-redacted-report
description: Redacted release-report exemplar for classification ceilings, source protection, source-safe ledgers, reviewer gates, and mosaic-risk checks.
version: 0.1.0
author: docxology
license: MIT
tags: [exemplar, redaction, disclosure-control, release-review]
---

# template-redacted-report

Load this skill when working inside `projects/templates/template_redacted_report/`.

## When to Use

- Creating or reviewing a sanitized release-report workflow.
- Auditing redaction ledgers, source-control coverage, reviewer approvals, residual-risk patterns, and mosaic risk.
- Forking a disclosure-control scaffold.

## Quick Reference

```bash
uv run pytest projects/templates/template_redacted_report/tests --cov=projects/templates/template_redacted_report/src --cov-fail-under=90
uv run python scripts/pipeline/stage_01_test.py --project templates/template_redacted_report --project-only
```

## Pitfalls

- Use invented or cleared public fixture text only.
- Keep source-safe ledgers hash-based; do not expose original redacted spans in public packets.
- Do not add operational targeting, collection, evasion, or surveillance guidance.
