# Validation Guide

This guide summarizes the validation pipeline and quality gates used in the project.

## Preflight
- `python3 project/scripts/manuscript_preflight.py --strict`
  - Checks figure existence from manuscript references
  - Ensures glossary markers and bibliography commands are present
  - Emits JSON for CI when `--json` is used

## Markdown & PDF
- `python3 -m infrastructure.validation.cli markdown project/manuscript/ --strict`
- `python3 -m infrastructure.validation.cli pdf project/output/pdf/`
- Detects unresolved references, missing citations, equation/anchor issues.

## Figures
- `validate_figure_registry output/figures/figure_registry.json` ensures registered figures match outputs.
- `MarkdownIntegration.validate_manuscript()` scans figure anchors and sections.

## Output Integrity
- `verify_output_integrity output/` checks hashes, structure, and cross-references of generated artifacts.

## Quality Metrics
- `analyze_document_quality(project/manuscript)` reports readability and structural metrics.
- `project/scripts/quality_report.py` aggregates markdown issues, integrity, and reproducibility.

## Reproducibility
- `generate_reproducibility_report output/` captures environment/dependency snapshots.

## CI Recommendations
- Run preflight + markdown validation on PRs.
- Fail on missing figures or bibliography blocks; warn on readability deltas.
- Persist `project/output/reports/` artifacts for inspection (JSON/HTML/Markdown).














