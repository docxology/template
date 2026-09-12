# Audit reports

Generated filepath and reference audit output, produced by
[`scripts/audit/audit_filepaths.py`](../../scripts/audit/audit_filepaths.py).

## Files in this directory

| File | What it is |
| --- | --- |
| [`filepath-audit-report.md`](filepath-audit-report.md) | Repo-wide scan for broken path references, categorized by severity (red/yellow/green flags), with known false positives filtered out |

## Regenerating

```bash
uv run python scripts/audit/audit_filepaths.py
```

The report is checked in as a point-in-time snapshot; regenerate it after
large-scale file moves or renames rather than hand-editing it.

Dated point-in-time session receipts (`AUDIT_*`, `REVIEW_*`, `REVIEW_LOG_*`,
`BACKLOG-CLOSURE-*`, `PROJECT_STATE_REPORT_*`, `_FLEET_REPORT_*`, and offline
verification receipts) are no longer tracked in this repository: they were
removed on 2026-09-11 and remain recoverable from git history. Record
point-in-time verification evidence in the commit message and the
[`STATUS.md`](../../STATUS.md) verification ledger instead of checking in a
new receipt.
