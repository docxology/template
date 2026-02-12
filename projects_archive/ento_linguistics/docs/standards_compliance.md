# Standards Compliance — Ento-Linguistics

Current project quality metrics and compliance status.

## Test Suite

| Metric | Value |
|--------|-------|
| **Total tests** | 778 |
| **Passing** | 778 |
| **Skipped** | 7 |
| **Failures** | 0 |
| **Test files** | 37 |
| **Execution time** | ~77 seconds |
| **Mock usage** | None — all tests use real data |

### Test File Coverage

| Subpackage | Test Files | Modules Covered |
|------------|-----------|-----------------|
| `analysis/` | `test_term_extraction.py`, `test_text_analysis.py`, `test_discourse_analysis.py`, `test_domain_analysis.py`, `test_conceptual_mapping.py` + expanded/coverage variants | All 10 analysis modules |
| `visualization/` | `test_concept_visualization.py`, `test_statistical_visualization.py`, `test_visualization.py`, `test_plots.py` + expanded/coverage variants | All 5 visualization modules |
| `core/` | `test_exceptions.py`, `test_metrics.py`, `test_parameters.py`, `test_validation.py`, `test_core_validation.py` | All core modules |
| `data/` | `test_literature_mining.py`, `test_data_generator.py`, `test_data_processing.py` + expanded/coverage variants | All data modules |
| `pipeline/` | `test_simulation.py`, `test_reporting.py`, `test_performance.py` + coverage variants | All pipeline modules |
| Integration | `tests/integration/` (7 files) | Cross-module workflows |

## Code Quality

| Standard | Status | Notes |
|----------|--------|-------|
| **Type hints** | ✅ | All public APIs typed |
| **Docstrings** | ✅ | Google-style on all exported functions/classes |
| **Structured logging** | ✅ | `src/core/logging.py` with `get_logger(__name__)` |
| **Custom exceptions** | ✅ | `src/core/exceptions.py` — `EntoLinguisticError` hierarchy |
| **No mock policy** | ✅ | All 778 tests use real data fixtures |
| **Deterministic seeds** | ✅ | `np.random.default_rng(seed)` used in data generation |

## Manuscript Quality

| Standard | Status | Notes |
|----------|--------|-------|
| **Figure references** | ✅ | `\ref{fig:...}` with matching `\label{fig:...}` |
| **Figure captions** | ✅ | Descriptive, multi-sentence captions on all 5 main figures |
| **16pt font floor** | ✅ | Enforced in `concept_visualization.py` and `statistical_visualization.py` |
| **Figure registry** | ✅ | `output/figures/figure_registry.json` tracks all generated figures |
| **Section numbering** | ✅ | 01–06 main, S01–S04 supplemental, 98–99 references |
| **Config metadata** | ✅ | `config.yaml` with title, author, ORCID, keywords |

## Figure Generation

| Figure | File | Size | Status |
|--------|------|------|--------|
| Concept map | `concept_map.png` | 287 KB | ✅ Real data |
| Terminology network | `terminology_network.png` | 572 KB | ✅ Real Jaccard co-occurrence |
| Domain comparison | `domain_comparison.png` | 511 KB | ✅ All 4 panels populated |
| Domain overlap heatmap | `domain_overlap_heatmap.png` | 204 KB | ✅ Real data |
| Anthropomorphic framing | `anthropomorphic_framing.png` | 260 KB | ✅ Real data |

## Validation Commands

```bash
# Full test suite
uv run pytest tests/ -x -q

# Manuscript preflight (figure refs, glossary, bibliography)
uv run python scripts/manuscript_preflight.py --strict

# Regenerate and verify figures
uv run python scripts/generate_research_figures.py

# Quality report
uv run python scripts/quality_report.py
```

## Known Compliance Items

| Item | Status | Notes |
|------|--------|-------|
| `infrastructure.*` imports | ✅ Removed | All imports use local `src/` modules |
| Mock/fake data in scripts | ✅ Removed | Jaccard co-occurrence, real confidence scores |
| Hardcoded values | ✅ Removed | `avg_confidence` now computed from real data |
| Font size compliance | ✅ | 16pt floor on all visualization modules |

---

**Last Verified:** 2026-02-09
**Test Result:** 778 passed, 7 skipped, 0 failed

## See Also

- [development_workflow.md](development_workflow.md) — Environment and commands
- [validation_guide.md](validation_guide.md) — Validation pipeline details
- [refactor_playbook.md](refactor_playbook.md) — Module dependencies
