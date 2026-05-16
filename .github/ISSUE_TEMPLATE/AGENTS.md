# ISSUE_TEMPLATE/ - Agent Guide

## Purpose

This directory defines the public issue intake surface for the template
repository. Templates should help maintainers reproduce problems quickly while
remaining fork-friendly.

## Local Rules

- Keep frontmatter valid for GitHub issue templates.
- Use durable labels: `bug`, `enhancement`, `documentation`, and
  `needs-triage`.
- Keep placeholder text free of local machine paths, private project names, or
  organization-specific support channels.
- Update [`README.md`](README.md) when adding, renaming, or removing templates.

## Validation

```bash
uv run python scripts/lint_docs.py --links-only --json
```

## See Also

- [`../AGENTS.md`](../AGENTS.md)
- [`../workflows/AGENTS.md`](../workflows/AGENTS.md)
