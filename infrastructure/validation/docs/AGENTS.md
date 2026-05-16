# infrastructure/validation/docs/ - Documentation Validation Docs

## Purpose

The `infrastructure/validation/docs/` package contains repository documentation scanning, quality, discovery, completeness, and accuracy helpers.

## Files

- `models.py` - documentation scan models
- `scanner.py` - documentation scanner
- `discovery.py` - documentation discovery helpers
- `scan_scope.py` - shared exclusions for local/generated trees
- `mermaid_lint.py` - fenced Mermaid validation through `mmdc`
- `cross_link_lint.py` - relative Markdown link validation
- `consistency_lint.py` - stale count and ghost-project checks
- `doc_pair_lint.py` - permanent-template `AGENTS.md` / `README.md` coverage
- `accuracy.py` - accuracy checks
- `completeness.py` - completeness checks
- `quality.py` - quality checks
- `_docs_scan_report.py` - scan report helpers

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
