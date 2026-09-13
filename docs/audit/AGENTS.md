# Audit reports — agent guide

> Companion to [`README.md`](README.md).

## Purpose

`docs/audit/` holds generated, regenerable audit reports only. It is distinct
from `scripts/audit/` (the generator code) and from `output/` (disposable,
gitignored pipeline artifacts).

Currently tracked:

- filepath/reference audit from
  [`scripts/audit/audit_filepaths.py`](../../scripts/audit/audit_filepaths.py)

Treat the checked-in `.md` report as a snapshot, not a hand-authored guide.

## 2026-09-11 receipt-removal note

All dated point-in-time receipts previously tracked here
(`AUDIT_2026-08-30*.md`, `_FLEET_REPORT_2026-08-30.md`,
`PROJECT_STATE_REPORT_2026-08-28.md`, `REVIEW_LOG_2026-08-31.md`,
`REVIEW_LOG_2026-09-02.md`, `REVIEW_2026-09-04.md`, `REVIEW_2026-09-05.md`,
`BACKLOG-CLOSURE-2026-09-05.md`, `BACKLOG-CLOSURE-2026-09-06.md`,
`executable-bundle-offline-receipt-2026-08-26.md`) plus the tracked
root-level `REVIEW_LOG_2026-08-31.md` were deleted on 2026-09-11 by
maintainer instruction; recover them from git history. Root Markdown remains
reserved for long-lived documentation. Do not check in new dated session
receipts anywhere in the repository: record point-in-time verification
evidence in the commit message and the [`STATUS.md`](../../STATUS.md)
verification ledger instead.

## Working here

- **Never hand-edit `filepath-audit-report.md`.** Regenerate it with
  `uv run python scripts/audit/audit_filepaths.py` and commit the new
  output as a whole.
- If a generator script adds a new tracked report to this directory, list it
  in `README.md`'s table and name the generator script that produces it.
