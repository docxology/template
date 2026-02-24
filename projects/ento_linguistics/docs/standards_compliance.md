# Standards Compliance — Ento-Linguistics

Current project quality metrics and compliance status. All values sourced directly from pipeline runs as of 2026-02-23.

## Test Suite

| Metric | Value |
|--------|-------|
| **Total tests collected** | 923 |
| **Passing** | 923 |
| **Skipped** | 0 |
| **Failures** | 0 |
| **Test files** | 40 (35 unit + 5 integration) |
| **Execution time** | ~18 seconds |
| **Mock usage** | None — all tests use real data |

### Test File Coverage

| Subpackage | Test Files | Modules Covered |
|------------|-----------|-----------------|
| `analysis/` | `test_term_extraction.py`, `test_text_analysis.py`, `test_discourse_analysis.py`, `test_domain_analysis.py`, `test_conceptual_mapping.py`, `test_semantic_entropy.py`, `test_cace_scoring.py` + expanded/coverage variants | All 12 analysis modules |
| `visualization/` | `test_concept_visualization.py`, `test_statistical_visualization.py`, `test_visualization.py`, `test_plots.py` + expanded/coverage variants | All 5 visualization modules |
| `core/` | `test_exceptions.py`, `test_metrics.py`, `test_parameters.py`, `test_validation.py`, `test_core_validation.py` | All 7 core modules |
| `data/` | `test_literature_mining.py`, `test_data_generator.py`, `test_data_processing.py` + expanded/coverage variants | All 4 data modules |
| `pipeline/` | `test_simulation.py`, `test_reporting.py`, `test_performance.py` + coverage variants | All 2 pipeline modules |
| Integration | `tests/integration/` (5 files) | Cross-module workflows |

## Code Quality

| Standard | Status | Notes |
|----------|--------|-------|
| **Type hints** | ✅ | All public APIs typed (`from __future__ import annotations`) |
| **Docstrings** | ✅ | Google-style on all exported functions/classes |
| **Structured logging** | ✅ | `src/core/logging.py` with `get_logger(__name__)` |
| **Custom exceptions** | ✅ | `src/core/exceptions.py` — `EntoLinguisticError` hierarchy |
| **No mock policy** | ✅ | All 923 passing tests use real data fixtures |
| **Deterministic seeds** | ✅ | `random_state=42` in KMeans; `np.random.default_rng(seed)` in data generation |
| **Clean-slate output** | ✅ | `output/figures/` and `output/data/` wiped and recreated on every pipeline run |

## Manuscript Quality

| Standard | Status | Notes |
|----------|--------|-------|
| **Figure references** | ✅ | `\ref{fig:...}` with matching `\label{fig:...}` |
| **Figure captions** | ✅ | Descriptive, multi-sentence captions on all 11 generated figures |
| **16pt font floor** | ✅ | Enforced in `concept_visualization.py` and `statistical_visualization.py` |
| **Figure registry** | ✅ | `output/figures/figure_registry.json` tracks all generated figures |
| **Section numbering** | ✅ | 01–06 main, S01–S04 supplemental, 98–99 references |
| **Config metadata** | ✅ | `config.yaml` with title, author, ORCID, keywords |
| **Real corpus stats** | ✅ | All statistics sourced from `output/data/*.json` — no hardcoded values |

## Figure Generation

Current pipeline run generates **11 figures** (all sourced from real data):

| Figure | File | Size | Status |
|--------|------|------|--------|
| Concept map | `concept_map.png` | 466 KB | ✅ Real TF-IDF/KMeans data |
| Terminology network | `terminology_network.png` | 2.6 MB | ✅ Real Jaccard co-occurrence |
| Domain comparison | `domain_comparison.png` | 751 KB | ✅ Real entropy + CACE scores |
| Domain overlap heatmap | `domain_overlap_heatmap.png` | 229 KB | ✅ Real cross-domain data |
| Anthropomorphic framing | `anthropomorphic_framing.png` | 317 KB | ✅ Real LinguisticFeatureExtractor data |
| Concept hierarchy | `concept_hierarchy.png` | 307 KB | ✅ Real NetworkX centrality |
| Domain overview grid | `domain_overview_grid.png` | 691 KB | ✅ 6-panel top-terms grid |
| Domain patterns grid | `domain_patterns_grid.png` | 509 KB | ✅ 6-panel POS donut charts |
| Power & Labor ambiguities | `power_and_labor_ambiguities.png` | 159 KB | ✅ Real ambiguity metrics |
| Power & Labor frequencies | `power_and_labor_term_frequencies.png` | 206 KB | ✅ Real term frequencies |
| Unit of Individuality patterns | `unit_of_individuality_patterns.png` | 166 KB | ✅ Real pattern data |

## Live Corpus Statistics

Sourced from `output/data/corpus_statistics.json`:

| Metric | Value |
|--------|-------|
| Documents | 362 |
| Total tokens | 48,062 |
| Unique token types | 6,971 |
| Type–token ratio | 0.145 |
| Total characters | 529,442 |
| Avg token length | 7.28 chars |
| Extracted terms | 871 total (223 domain-assigned) |
| Concept map nodes | 6 concepts, 8 relationships |

## Validation Commands

```bash
# Full test suite (pipeline entry point — also clears and regenerates output/)
uv run python scripts/02_generate_figures.py

# Tests
uv run pytest tests/ -x -q

# Build corpus (stage 1)
uv run python scripts/01_build_corpus.py

# Manuscript preflight
uv run python scripts/_manuscript_preflight.py --strict

# Quality report
uv run python scripts/_quality_report.py
```

## Known Compliance Items

| Item | Status | Notes |
|------|--------|-------|
| `infrastructure.*` imports | ✅ Removed | All imports use local `src/` modules |
| Mock/fake data in scripts | ✅ Removed | Real Jaccard co-occurrence, real entropy scores |
| Hardcoded corpus statistics | ✅ Removed | `03_methodology.md` uses real pipeline values |
| Font size compliance | ✅ | 16pt floor on all visualization modules |
| Clean-slate execution | ✅ | `_setup_directories()` wipes output before rebuild |
| Stale figures | ✅ | No stale artefacts — wiped on every run |

---

**Last Verified:** 2026-02-24
**Test Result:** 923 passed, 0 skipped, 0 failures

## See Also

- [development_workflow.md](development_workflow.md) — Environment and commands
- [validation_guide.md](validation_guide.md) — Validation pipeline details
- [refactor_playbook.md](refactor_playbook.md) — Module dependencies
