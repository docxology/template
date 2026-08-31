# Audit reports — agent guide

> Companion to [`README.md`](README.md).

## Purpose

`docs/audit/` holds generated audit reports and dated point-in-time session
receipts (`DEEP_PASS_*`, `PROJECT_STATE_REPORT_*`, offline verification
receipts). Do not place those at the repository root — consistency linters
scan root Markdown as long-lived documentation.

Currently tracked:

- filepath/reference audit from
  [`scripts/audit/audit_filepaths.py`](../../scripts/audit/audit_filepaths.py)
- dated offline verification receipts (see [`README.md`](README.md) files table)

Treat every checked-in `.md` report as a snapshot, not a hand-authored guide.

## 2026-08-31 fleet archival note

The four root-level `AUDIT_2026-08-30*.md` lane reports were moved here from the
repo root on 2026-08-31 (agent-ergonomics fleet pass) — they are untracked
working-tree snapshots, not yet in git history, and root Markdown is reserved
for long-lived documentation. They are point-in-time audit lanes for
2026-08-30 only; no entry doc links to them as current guidance.

The two root-level dated session logs `_FLEET_REPORT_2026-08-30.md` and
`REVIEW_LOG_2026-08-31.md` were moved here from the repo root on 2026-08-31
(agent-ergonomics round-2 pass), per the same policy: root Markdown is
reserved for long-lived documentation, and dated lane reports are snapshots.
`TO-DO.md` row `ERG-ENTRY-DOCS-2026-08-31` references
[`REVIEW_LOG_2026-08-31.md`](REVIEW_LOG_2026-08-31.md) at its new path.


## Working here

- **Never hand-edit `filepath-audit-report.md`.** Regenerate it with
  `uv run python scripts/audit/audit_filepaths.py` and commit the new
  output as a whole.
- If you add another generated audit report to this directory, list it in
  `README.md`'s table and name the generator script that produces it.
- This directory is distinct from `scripts/audit/` (the generator code) and
  from `output/` (disposable, gitignored pipeline artifacts) — reports here
  are intentionally tracked as point-in-time records.
