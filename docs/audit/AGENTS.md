# audit/ - Audit Reports Documentation

## Overview

Historical audit snapshots and on-demand filepath scans. **Live drift status** comes from `lint_docs.py` and `check_template_drift.py`, not from stale reports in this tree.

**Living rosters** of `projects/` names belong in [_generated/active_projects.md](../_generated/active_projects.md). Archived report line references are **point-in-time snapshots** from their generation run.

## Purpose

- Preserve dated audit snapshots under [`archived/`](archived/) (suffix `-YYYY-MM-DD.md`)
- Document how to regenerate a filepath audit when needed
- Point maintainers at live linters instead of top-level stale reports

## Current layout

The top-level audit directory holds **README + AGENTS only**. Historical reports were moved to [`archived/`](archived/) in the May 2026 hardening pass so filenames carry explicit generation dates.

See [`README.md`](README.md) for the archived inventory and live-linter command table.

## Regenerating a snapshot

```bash
uv run python scripts/audit_filepaths.py \
  --output "docs/audit/archived/filepath-audit-report-$(date +%Y-%m-%d).md"
```

Archive directly under `archived/` — do not leave undated copies at the top level.

## Live linters (authoritative)

| Linter | Command |
|--------|---------|
| Repo-wide doc linter | `uv run python scripts/lint_docs.py` |
| Documentation RedTeam audit | `uv run python scripts/audit_documentation.py --format markdown` |
| Template drift checker | `uv run python scripts/check_template_drift.py` |
| Consistency-only pass | `uv run python scripts/lint_docs.py --consistency-only` |

## Integration

Audit tooling integrates with:

- **Validation pipeline:** `scripts/04_validate_output.py`
- **Documentation tools:** `infrastructure/validation/repo/audit_orchestrator.py`
- **Doc linter:** `infrastructure/validation/docs/lint_runner.py`

## See Also

- [`README.md`](README.md) — Status, archived inventory, live linter table
- [`archived/`](archived/) — Historical snapshots
- [`../operational/troubleshooting/`](../operational/troubleshooting/) — Troubleshooting guide
- [`../../infrastructure/validation/AGENTS.md`](../../infrastructure/validation/AGENTS.md) — Validation module documentation
