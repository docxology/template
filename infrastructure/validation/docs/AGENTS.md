# infrastructure/validation/docs/ - Documentation Validation Docs

## Purpose

The `infrastructure/validation/docs/` package contains repository documentation scanning, quality, discovery, completeness, and accuracy helpers.

## Files

- `models.py` - documentation scan models
- `scanner.py` - documentation scanner (`DocumentationScanner.run_verification_checks()`)
- `discovery.py` - documentation discovery helpers
- `verification.py` - verification checks (lint, markdown, commands, link cycles)
- `scan_scope.py` - shared exclusions for local/generated trees (`output/`, `_generated/`, `_skill-eval/`, …)
- `mermaid_lint.py` - fenced Mermaid validation through `mmdc`
- `cross_link_lint.py` - relative Markdown link validation and link-cycle detection
- `lint_runner.py` - CI docs lint orchestration (used by verification checks and `scripts/lint_docs.py`)
- `public_audit.py` - advisory public documentation RedTeam audit; inventories docs, generated-fact grounding, verifier negative-control claims, and `def`/`class` documentation coverage
- `consistency_lint.py` - facade re-exporting consistency checks (module counts, ghost projects, command conventions, doc imports, stale shell-bootstrap contracts)
- `consistency/` - implementation package for consistency linters
- `doc_pair_lint.py` - permanent-template `AGENTS.md` / `README.md` coverage (skips generated fixture payloads under `tests/fixtures/`)
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

## Advisory RedTeam audit

`scripts/audit_documentation.py` emits `public_audit.py` reports in Markdown or
JSON. The audit reuses `doc_roots()` and shared scan exclusions, then adds
advisory findings for stale project roster/count prose, verifier claims without
nearby negative controls, missing decision-memory rule links, and public
`def`/`class` documentation gaps. It is source-backed but not a replacement for
the blocking `lint_docs.py` gate.

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

## Lint scope exclusions

Shared via [`scan_scope.py`](scan_scope.py) (`DEFAULT_EXCLUDE_PARTS`, `SKILL_EVAL_DIR_NAME`):

| Path component | Rationale |
| --- | --- |
| `output/`, `projects/archive/`, `projects/working/` | Regenerated or non-executed trees |
| `_generated/` | Machine-generated snippets |
| `_skill-eval/` | Regenerated skill-eval harness fixtures under `docs/prompts/_skill-eval/` |

Cross-link lint also skips `**/_skill-eval/**` via `_DEFAULT_EXCLUDE_GLOBS`.

## Consistency checks

`check_stale_shell_contracts()` (via `consistency_lint.py`) flags post-refactor doc drift:

- PIPELINE_MODE export claims tied to `run.sh` (bash-local only, not exported)
- claims that `secure_run.sh` owns `--deterministic` parsing (Python `secure` subcommand owns the flag)
- unconditional `projects/template_search_project/` without `projects/archive/` or local-only copy context

## Mermaid lint (`mermaid_lint.py`)

Fenced Mermaid blocks are validated by invoking `mmdc` (Mermaid CLI). Batch rendering
reduces subprocess churn; a repo-wide total timeout caps wall time on large doc trees.

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `TEMPLATE_MERMAID_LINT_TIMEOUT` | `30` | Per-file `mmdc` timeout (seconds) |
| `TEMPLATE_MERMAID_LINT_TOTAL_TIMEOUT` | `120` | Total budget across all files in one lint run |
| `TEMPLATE_MERMAID_LINT_BATCH_SIZE` | `20` | Max diagrams per batch `mmdc` invocation |

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
