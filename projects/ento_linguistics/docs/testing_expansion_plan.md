# Testing Expansion Plan — Ento-Linguistics

Targeted additions to strengthen regression, integration, and performance coverage across the 948-test suite (946 passing, 40 test files as of 2026-02-23).

## Current Coverage

| Category | Test Files | Tests (approx) | Modules Covered |
|----------|-----------|-----------------|-----------------|
| Term extraction | 2 files | ~47 | `term_extraction.py` |
| Semantic entropy | 1 file | ~25 | `semantic_entropy.py` |
| CACE scoring | 1 file | ~25 | `cace_scoring.py` |
| Conceptual mapping | 3 files | ~65 | `conceptual_mapping.py` |
| Domain analysis | 1 file | ~20 | `domain_analysis.py` |
| Discourse analysis | 2 files | ~38 | `discourse_analysis.py`, `discourse_patterns.py` |
| Text analysis | 1 file | ~21 | `text_analysis.py` |
| Concept visualization | 3 files | ~55 | `concept_visualization.py` |
| Statistical visualization | 1 file | ~44 | `statistical_visualization.py` |
| Literature mining | 3 files | ~50 | `literature_mining.py` |
| Core utilities | 5 files | ~90 | `exceptions`, `metrics`, `parameters`, `validation`, `validation_utils` |
| Data/Pipeline | 5 files | ~110 | `data_generator`, `data_processing`, `loader`, `simulation`, `reporting`, `performance` |
| Integration | 5 files | ~50 | Cross-module workflows |
| Other | 4 files | ~88 | `plots`, `visualization`, `example`, `package_imports` |

## Proposed Additions

### 1. Pipeline Script Integration Tests

**Target**: End-to-end validation that the full clean-slate rebuild completes successfully.

```bash
# Verify clean-slate rebuild works
uv run python scripts/02_generate_figures.py
# Expected: exits 0, creates 11 PNG files, logs "✅ Output directories initialised (clean slate)"
```

Add `tests/integration/test_pipeline_scripts.py`:

- Execute `scripts/02_generate_figures.py` via `subprocess.run` and assert exit code 0
- Verify all 11 expected PNG files exist under `output/figures/` after execution
- Validate `output/figures/figure_registry.json` contains 9 registered entries with valid SHA hashes
- Verify `output/data/corpus_statistics.json`, `domain_statistics.json`, `concept_map_summary.json` are present

### 2. Property Tests for Data Modules

**Target**: Shape and NaN guards for data generation and term extraction.

Add `tests/property/test_data_properties.py`:

- `data_generator.generate_synthetic_data`: output shape matches requested dimensions, no NaN/Inf
- `data_processing.normalize_data`: output in [0,1] range, idempotent on already-normalized data
- `term_extraction.TerminologyExtractor`: extracted terms have non-empty text, valid confidence ≥ 0
- `semantic_entropy.calculate_semantic_entropy`: `entropy_bits ≥ 0`, `0 ≤ n_clusters ≤ max_clusters`, `sum(cluster_distribution) ≈ 1.0`

### 3. Visualization Regression Tests — 11 Figures

**Target**: Detect formatting regressions for all 11 generated figures without pixel-level comparison.

Add `tests/test_visualization_regression.py`:

- Verify each of the 11 generated figures has minimum file size (not empty/placeholder):
  - `concept_map.png` > 100 KB
  - `terminology_network.png` > 200 KB
  - `domain_comparison.png` > 200 KB
  - `domain_overview_grid.png` > 100 KB
  - `domain_patterns_grid.png` > 100 KB
  - `concept_hierarchy.png` > 100 KB
  - `anthropomorphic_framing.png` > 100 KB
  - `domain_overlap_heatmap.png` > 100 KB
  - `power_and_labor_ambiguities.png` > 50 KB
  - `power_and_labor_term_frequencies.png` > 50 KB
  - `unit_of_individuality_patterns.png` > 50 KB
- Check `figure_registry.json` contains metadata for all registered figures
- Verify 16pt font floor by inspecting `plt.rcParams["font.size"]` after figure generation

### 4. Cross-Domain Consistency Tests

**Target**: Ensure all six Ento-Linguistic domains produce consistent analysis results.

Add `tests/test_domain_consistency.py`:

- Each domain analysis produces non-empty `key_terms` list
- Confidence scores are non-negative for all domains (unbounded but ≥ 0)
- Ambiguity scores are non-negative for all domains
- Domain statistics dictionaries have consistent key sets across all 6 domains
- Bridging term counts are non-negative integers

### 5. CACE + Entropy Integration Tests

**Target**: Validate the end-to-end flow from contexts → entropy → CACE scoring.

Add `tests/test_cace_entropy_integration.py`:

- `calculate_semantic_entropy` with known test cases: uniform distribution → H = log2(k), single cluster → H = 0
- `score_clarity`: terms in `ANTHROPOMORPHIC_TERMS` (e.g., "queen") score lower than neutral terms
- `evaluate_term_cace` returns `CACEScore` with all fields in [0,1] for any valid term/context input
- `compare_terms_cace` returns a sorted list with highest-aggregate term first

### 6. Performance Smoke Tests

**Target**: Bounded execution time for analysis modules.

Add `tests/test_performance_bounds.py` (marked `@pytest.mark.slow`):

- `term_extraction.TerminologyExtractor.extract()` completes within 5s on standard corpus
- `domain_analysis.DomainAnalyzer.analyze_all_domains()` completes within 30s
- Full `02_generate_figures.py` clean-slate run completes within 300s

## Expected Outcomes

- Pipeline failures (exit code ≠ 0) caught before manuscript builds
- All 11 figure outputs verified to be non-empty after every regeneration
- Data corruption (NaN, wrong shapes) caught via property tests
- CACE/entropy boundary conditions validated
- Domain analysis consistency ensured across all six domains
- Performance regressions detected via bounded smoke tests

## See Also

- [development_workflow.md](development_workflow.md) — Test commands and environment
- [standards_compliance.md](standards_compliance.md) — Current test metrics
- [validation_guide.md](validation_guide.md) — Validation pipeline
