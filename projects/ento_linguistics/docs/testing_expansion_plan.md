# Testing Expansion Plan — Ento-Linguistics

Targeted additions to strengthen regression, integration, and performance coverage across the 778-test suite.

## Current Coverage

| Category | Test Files | Tests | Modules Covered |
|----------|-----------|-------|-----------------|
| Term extraction | 2 files | ~47 | `term_extraction.py` |
| Conceptual mapping | 3 files | ~65 | `conceptual_mapping.py` |
| Domain analysis | 1 file | ~20 | `domain_analysis.py` |
| Discourse analysis | 2 files | ~38 | `discourse_analysis.py`, `discourse_patterns.py` |
| Text analysis | 1 file | ~21 | `text_analysis.py` |
| Concept visualization | 3 files | ~55 | `concept_visualization.py` |
| Statistical visualization | 1 file | ~44 | `statistical_visualization.py` |
| Literature mining | 3 files | ~50 | `literature_mining.py` |
| Core utilities | 5 files | ~90 | `exceptions`, `metrics`, `parameters`, `validation`, `validation_utils` |
| Data/Pipeline | 5 files | ~110 | `data_generator`, `data_processing`, `simulation`, `reporting`, `performance` |
| Integration | 7 files | ~50 | Cross-module workflows |
| Other | 4 files | ~88 | `plots`, `visualization`, `example`, `package_imports` |

## Proposed Additions

### 1. Pipeline Script Integration Tests

**Target**: End-to-end validation of the main scripts.

```bash
# Verify these scripts complete without error
uv run python scripts/generate_research_figures.py
uv run python scripts/analysis_pipeline.py
uv run python scripts/manuscript_preflight.py --strict
```

Add `tests/integration/test_pipeline_scripts.py`:

- Execute each script via `subprocess.run` and assert exit code 0
- Verify expected output files exist after execution
- Validate `output/figures/figure_registry.json` contains expected entries

### 2. Property Tests for Data Modules

**Target**: Shape and NaN guards for data generation and term extraction.

Add `tests/property/test_data_properties.py`:

- `data_generator.generate_synthetic_data`: output shape matches requested dimensions, no NaN/Inf
- `data_processing.normalize_data`: output in [0,1] range, idempotent on already-normalized data
- `term_extraction.TerminologyExtractor`: extracted terms have non-empty text, valid confidence in [0,1]

### 3. Visualization Regression Tests

**Target**: Detect formatting regressions without pixel-level comparison.

Add `tests/test_visualization_regression.py`:

- Verify each generated figure has minimum file size (not empty/placeholder)
- Check `figure_registry.json` contains metadata for all registered figures
- Verify 16pt font floor by inspecting `plt.rcParams` after figure generation

### 4. Cross-Domain Consistency Tests

**Target**: Ensure all six Ento-Linguistic domains produce consistent analysis results.

Add `tests/test_domain_consistency.py`:

- Each domain analysis produces non-empty `key_terms` list
- Confidence scores are in valid [0,1] range for all domains
- Ambiguity scores are non-negative for all domains
- Domain statistics dictionaries have consistent key sets

### 5. Performance Smoke Tests

**Target**: Bounded execution time for analysis modules.

Add `tests/test_performance_bounds.py` (marked `@pytest.mark.slow`):

- `term_extraction.TerminologyExtractor.extract()` completes within 5s on standard corpus
- `domain_analysis.DomainAnalysis.analyze()` completes within 10s per domain
- Figure generation completes within 30s for all 5 main figures

## Expected Outcomes

- Pipeline script failures caught before manuscript builds
- Data corruption (NaN, wrong shapes) caught via property tests
- Visualization regressions caught without brittle image diffs
- Domain analysis consistency ensured across all six domains
- Performance regressions detected via bounded smoke tests

## See Also

- [development_workflow.md](development_workflow.md) — Test commands and environment
- [standards_compliance.md](standards_compliance.md) — Current test metrics
- [validation_guide.md](validation_guide.md) — Validation pipeline
