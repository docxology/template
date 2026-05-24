# infrastructure/validation/docs/ - Documentation Validation Docs

## Purpose

The `infrastructure/validation/docs/` package contains repository documentation scanning, quality, discovery, completeness, and accuracy helpers.

## Files

- `models.py` - documentation scan models
- `scanner.py` - documentation scanner (`DocumentationScanner.run_verification_checks()`)
- `discovery.py` - documentation discovery helpers
- `verification.py` - verification checks (lint, markdown, commands, link cycles)
- `scan_scope.py` - shared exclusions for local/generated trees
- `mermaid_lint.py` - fenced Mermaid validation through `mmdc`
- `cross_link_lint.py` - relative Markdown link validation and link-cycle detection
- `lint_runner.py` - CI docs lint orchestration (used by verification checks and `scripts/lint_docs.py`)
- `consistency_lint.py` - stale count and ghost-project checks
- `doc_pair_lint.py` - permanent-template `AGENTS.md` / `README.md` coverage
- `accuracy.py` - accuracy checks
- `completeness.py` - completeness checks
- `quality.py` - quality checks
- `_docs_scan_report.py` - scan report helpers

## Verification checks

`DocumentationScanner.run_verification_checks()` delegates to `run_verification_checks()` in `verification.py`:

| Field | Source | Status vocabulary |
| --- | --- | --- |
| `docs_lint` | `run_docs_lint()` | `passed` / `failed` / `skipped` |
| `markdown_validation` | `validate_markdown()` on `docs/` | `passed` / `failed` / `skipped` |
| `commands_tested` | `verify_commands()` | `passed` / `failed` |
| `circular_references` | `detect_markdown_link_cycles()` | `passed` / `failed` |
| `link_checker` | `run_link_audit()` | `success` + `exit_code` |

Stub statuses such as `basic_validation_passed` and `manual_testing_required` are removed.

## Scanner API (evergreen step names)

| Method | Module helper |
| --- | --- |
| `discover_inventory()` | `discover_documentation()` |
| `verify_accuracy()` | `verify_documentation_accuracy()` |
| `analyze_completeness()` | `analyze_documentation_completeness()` |
| `assess_quality()` | `assess_documentation_quality()` |
| `identify_improvements()` | (scanner-local) |
| `run_verification_checks()` | `run_verification_checks()` |
| `build_scan_report()` | `build_documentation_scan_report()` |

Statistics keys: `discovery`, `accuracy`, `completeness`, `quality`, `improvements`, `verification`.

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
