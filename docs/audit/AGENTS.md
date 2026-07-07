# Audit reports — agent guide

> Companion to [`README.md`](README.md).

## Purpose

`docs/audit/` holds generated audit reports — currently just the filepath
and reference audit from
[`scripts/audit/audit_filepaths.py`](../../scripts/audit/audit_filepaths.py).
Treat the checked-in `.md` report as a snapshot, not a hand-authored guide.

## Working here

- **Never hand-edit `filepath-audit-report.md`.** Regenerate it with
  `uv run python scripts/audit/audit_filepaths.py` and commit the new
  output as a whole.
- If you add another generated audit report to this directory, list it in
  `README.md`'s table and name the generator script that produces it.
- This directory is distinct from `scripts/audit/` (the generator code) and
  from `output/` (disposable, gitignored pipeline artifacts) — reports here
  are intentionally tracked as point-in-time records.
