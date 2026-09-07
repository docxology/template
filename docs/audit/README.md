# Audit reports

Generated filepath and reference audit output, produced by
[`scripts/audit/audit_filepaths.py`](../../scripts/audit/audit_filepaths.py).

## Files in this directory

| File | What it is |
| --- | --- |
| [`REVIEW_2026-09-04.md`](REVIEW_2026-09-04.md) | Rendering refactor, checkpoint/export containment fixes, baseline and final verification receipt |
| [`filepath-audit-report.md`](filepath-audit-report.md) | Repo-wide scan for broken path references, categorized by severity (red/yellow/green flags), with known false positives filtered out |
| [`executable-bundle-offline-receipt-2026-08-26.md`](executable-bundle-offline-receipt-2026-08-26.md) | Offline-container verification receipt for EXECUTABLE-BUNDLE-MAJ-1/-2 (network-none pytest + fail-closed compose) |
| [`AUDIT_2026-08-30.md`](AUDIT_2026-08-30.md) and [`AUDIT_2026-08-30_lane_*.md`](AUDIT_2026-08-30_lane_addendum.md) | 2026-08-30 point-in-time fleet audit lane reports (moved from repo root 2026-08-31; see [AGENTS.md](AGENTS.md) archival note) |
| [`PROJECT_STATE_REPORT_2026-08-28.md`](PROJECT_STATE_REPORT_2026-08-28.md) | 2026-08-28 point-in-time project-state session receipt |
| [`_FLEET_REPORT_2026-08-30.md`](_FLEET_REPORT_2026-08-30.md) | 2026-08-30 agent-ergonomics fleet report (moved from repo root 2026-08-31; point-in-time snapshot) |
| [`REVIEW_LOG_2026-08-31.md`](REVIEW_LOG_2026-08-31.md) | 2026-08-31 agent-ergonomics passes review log (moved from repo root 2026-08-31; point-in-time session log) |
| [`REVIEW_LOG_2026-09-02.md`](REVIEW_LOG_2026-09-02.md) | 2026-09-02 infrastructure deep-pass review log (scout-verified findings, TDD fixes, coverage-provenance remediation launch) |

## Regenerating

```bash
uv run python scripts/audit/audit_filepaths.py
```

The report is checked in as a point-in-time snapshot; regenerate it after
large-scale file moves or renames rather than hand-editing it.

Dated session receipts (`DEEP_PASS_*`, `PROJECT_STATE_REPORT_*`) belong here
or under another audit subfolder — not at the repository root — so consistency
linters treat them like other point-in-time audit artifacts.
