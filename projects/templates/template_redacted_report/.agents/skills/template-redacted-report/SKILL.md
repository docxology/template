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
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_redacted_report
```

## Pitfalls

- Use invented or cleared public fixture text only.
- Keep source-safe ledgers hash-based; do not expose original redacted spans in public packets.
- Treat `redaction_audit.json` and `release_ledger.json` as text-free public
  evidence surfaces; the comprehensive narrative packet remains in memory.
- Keep `01_generate_release_artifacts.py` thin and the normal Stage 02 allowlist
  separate from opt-in development PDF generation.
- Do not add operational targeting, collection, evasion, or surveillance guidance.
