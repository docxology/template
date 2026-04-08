# audit/ - Audit Reports

Directory for storing automated audit reports and validation results.

## Purpose

This directory contains generated audit reports from repository-wide validation and quality checks. These reports help identify documentation issues, broken links, and quality problems across the codebase.

Reports here are **historical snapshots**: file paths and line numbers refer to the tree at generation time. For the current set of active `projects/` workspaces, use [_generated/active_projects.md](../_generated/active_projects.md) instead of inferring layout from audit tables.

## Contents

| File | Purpose | Audience |
|------|---------|----------|
| [`FILEPATH_AUDIT_REPORT.md`](FILEPATH_AUDIT_REPORT.md) | Default output path for [`scripts/audit_filepaths.py`](../../scripts/audit_filepaths.py) (`--output` default) | Developers |
| [`filepath-audit-report.md`](filepath-audit-report.md) | Same report format when written via `--output docs/audit/filepath-audit-report.md` (keeps a stable secondary filename in-repo if desired) | Developers |
| [`documentation-review-report.md`](documentation-review-report.md) | Documentation completeness review report | All users |
| [`documentation-review-summary.md`](documentation-review-summary.md) | Documentation review executive summary | All users |

## Usage

The thin orchestrator is [`scripts/audit_filepaths.py`](../../scripts/audit_filepaths.py). It calls `run_comprehensive_audit` and `generate_audit_report` in [`infrastructure/validation/repo/audit_orchestrator.py`](../../infrastructure/validation/repo/audit_orchestrator.py). There is no `python -m infrastructure.validation.repo.audit_orchestrator` entry point.

```bash
# Default: writes docs/audit/FILEPATH_AUDIT_REPORT.md (markdown)
uv run python scripts/audit_filepaths.py

# Explicit output path and JSON
uv run python scripts/audit_filepaths.py --output docs/audit/filepath-audit-report.md
uv run python scripts/audit_filepaths.py --format json --output docs/audit/audit.json

# Verbose progress
uv run python scripts/audit_filepaths.py --verbose
```

## Report Structure

Audit reports typically include:

- Executive summary with issue counts
- Link validation issues (broken references, missing files)
- Quality issues (documentation gaps, formatting problems)
- Recommendations for fixes

## See Also

- [AGENTS.md](AGENTS.md) - audit documentation
- [`../operational/troubleshooting/`](../operational/troubleshooting/) - Troubleshooting guide
- [`../reference/faq.md`](../reference/faq.md) - Common questions
