# infrastructure/validation/docs/ - Documentation Validation

Repository documentation scanning, quality, completeness, discovery, and accuracy helpers.

## Files

- `models.py` — documentation scan models
- `scanner.py` — documentation scanner (`run_verification_checks()` delegates to real checks)
- `verification.py` — verification checks (lint, markdown, commands, link cycles)
- `discovery.py` — documentation discovery helpers
- `scan_scope.py` — shared exclusions for local/generated trees
- `mermaid_lint.py` — fenced Mermaid validation through `mmdc`
- `cross_link_lint.py` — relative Markdown link validation and link-cycle detection
- `lint_runner.py` — CI docs lint orchestration (used by verification checks and `scripts/lint_docs.py`)
- `consistency_lint.py` — stale count and ghost-project checks
- `doc_pair_lint.py` — permanent-template `AGENTS.md` / `README.md` coverage
- `accuracy.py` — accuracy checks
- `completeness.py` — completeness checks
- `quality.py` — quality checks
- `_docs_scan_report.py` — scan report helpers

## Verification checks

See [`AGENTS.md`](AGENTS.md) for the delegation table (`docs_lint`, `markdown_validation`, `commands_tested`, `circular_references`, `link_checker`).

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
