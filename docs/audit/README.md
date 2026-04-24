# audit/ - Audit Reports

Directory for storing automated audit reports and validation results.

## Purpose

This directory contains generated audit reports from repository-wide validation and quality checks. These reports help identify documentation issues, broken links, and quality problems across the codebase.

Reports here are **historical snapshots**: file paths and line numbers refer to the tree at generation time. For the current set of active `projects/` workspaces, use [_generated/active_projects.md](../_generated/active_projects.md) instead of inferring layout from audit tables.

## Contents

| File | Purpose | Audience |
|------|---------|----------|
| [`filepath-audit-report.md`](filepath-audit-report.md) | Filepath and reference audit report (regenerate with `uv run python scripts/audit_filepaths.py --output docs/audit/filepath-audit-report.md`) | Developers |
| [`documentation-review-report.md`](documentation-review-report.md) | Documentation completeness review report | All users |
| [`documentation-review-summary.md`](documentation-review-summary.md) | Documentation review executive summary | All users |

## Usage

Regenerate the filepath audit:

```bash
uv run python scripts/audit_filepaths.py --output docs/audit/filepath-audit-report.md
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
