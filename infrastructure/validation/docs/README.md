# infrastructure/validation/docs/ - Documentation Validation

Repository documentation scanning, quality, completeness, discovery, and accuracy helpers.

## Files

- `models.py` — documentation scan models
- `scanner.py` — documentation scanner (`run_verification_checks()` delegates to real checks)
- `verification.py` — verification checks (lint, markdown, commands, link cycles)
- `discovery.py` — documentation discovery helpers
- `scan_scope.py` — shared exclusions for local/generated trees (`output/`, `_generated/`, `_skill-eval/`, …)
- `mermaid_lint.py` — fenced Mermaid validation through `mmdc`
- `cross_link_lint.py` — relative Markdown link validation and link-cycle detection
- `lint_runner.py` — CI docs lint orchestration (used by verification checks and `scripts/lint_docs.py`)
- `public_audit.py` — advisory public documentation RedTeam audit and AST-backed def/class report
- `consistency_lint.py` — module counts, ghost projects, command conventions, stale shell-bootstrap contracts
- `doc_pair_lint.py` — permanent-template `AGENTS.md` / `README.md` coverage
- `accuracy.py` — accuracy checks
- `completeness.py` — completeness checks
- `quality.py` — quality checks
- `_docs_scan_report.py` — scan report helpers

## Verification checks

See [`AGENTS.md`](AGENTS.md) for the delegation table (`docs_lint`, `markdown_validation`, `commands_tested`, `circular_references`, `link_checker`) and lint-scope exclusions (`_skill-eval/`, `_generated/`, `output/`).

## Advisory audit

Use `uv run python scripts/audit_documentation.py --format markdown` for a
source-backed advisory report over public docs, generated-fact grounding,
verifier negative-control claims, and Python `def` / `class` documentation
coverage. This does not replace the blocking `lint_docs.py` gate.

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
