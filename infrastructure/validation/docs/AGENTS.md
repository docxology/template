# infrastructure/validation/docs/ - Documentation Validation Docs

## Purpose

The `infrastructure/validation/docs/` package contains repository documentation scanning, quality, discovery, completeness, and accuracy helpers.

## Files

- `models.py` - documentation scan models
- `scanner.py` - documentation scanner
- `discovery.py` - documentation discovery helpers
- `scan_scope.py` - shared exclusions for local/generated trees
- `mermaid_lint.py` - fenced Mermaid validation through `mmdc`
- `cross_link_lint.py` - relative Markdown link validation and link-cycle detection
- `lint_runner.py` - CI docs lint orchestration (used by Phase 6 verification)
- `consistency_lint.py` - stale count and ghost-project checks
- `doc_pair_lint.py` - permanent-template `AGENTS.md` / `README.md` coverage
- `accuracy.py` - accuracy checks
- `completeness.py` - completeness checks
- `quality.py` - quality checks
- `_docs_scan_report.py` - scan report helpers

## Phase 6 verification

`DocumentationScanner.phase6_verification()` delegates to real checks:

| Field | Source | Status vocabulary |
| --- | --- | --- |
| `docs_lint` | `run_docs_lint()` | `passed` / `failed` / `skipped` |
| `markdown_validation` | `validate_markdown()` on `docs/` | `passed` / `failed` / `skipped` |
| `commands_tested` | `verify_commands()` | `passed` / `failed` |
| `circular_references` | `detect_markdown_link_cycles()` | `passed` / `failed` |
| `link_checker` | `run_link_audit()` | `success` + `exit_code` |

Stub statuses such as `basic_validation_passed` and `manual_testing_required` are removed.

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
