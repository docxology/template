# Audit reports

Generated filepath and reference audit output, produced by
[`scripts/audit/audit_filepaths.py`](../../scripts/audit/audit_filepaths.py).

## Files in this directory

| File | What it is |
| --- | --- |
| [`filepath-audit-report.md`](filepath-audit-report.md) | Repo-wide scan for broken path references, categorized by severity (red/yellow/green flags), with known false positives filtered out |
| [`executable-bundle-offline-receipt-2026-08-26.md`](executable-bundle-offline-receipt-2026-08-26.md) | Offline-container verification receipt for EXECUTABLE-BUNDLE-MAJ-1/-2 (network-none pytest + fail-closed compose) |

## Regenerating

```bash
uv run python scripts/audit/audit_filepaths.py
```

The report is checked in as a point-in-time snapshot; regenerate it after
large-scale file moves or renames rather than hand-editing it.

Dated session receipts (`DEEP_PASS_*`, `PROJECT_STATE_REPORT_*`) belong here
or under another audit subfolder — not at the repository root — so consistency
linters treat them like other point-in-time audit artifacts.
