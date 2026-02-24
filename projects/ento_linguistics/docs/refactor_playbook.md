# Refactor Playbook — Ento-Linguistics

Module dependency map, hotspots, and safe-change recipes for the Ento-Linguistic Domains codebase.

## Module Dependency Map

### `src/analysis/` (Domain-Specific Analysis — 12 modules)

| Module | Size | Dependencies | Role |
|--------|------|-------------|------|
| `domain_analysis.py` | 40 KB | `term_extraction`, `text_analysis` | Six-domain analysis engine with statistics |
| `conceptual_mapping.py` | 37 KB | `term_extraction` | Concept network: Jaccard edges, NetworkX centrality |
| `term_extraction.py` | 20 KB | None (standalone) | Core term extraction from corpora |
| `persuasive_analysis.py` | 15 KB | `discourse_analysis` | Persuasive technique detection |
| `discourse_analysis.py` | 14 KB | `discourse_patterns` | Framing pattern analysis |
| `text_analysis.py` | 14 KB | None (standalone) | TextProcessor + LinguisticFeatureExtractor |
| `rhetorical_analysis.py` | 11 KB | None (standalone) | Rhetorical strategy / narrative framework analysis |
| `cace_scoring.py` | 11 KB | None (standalone) | CACE 4-dimension scoring (Clarity/Appropriateness/Consistency/Evolvability) |
| `performance.py` | 9 KB | None (standalone) | Convergence and scalability metrics |
| `statistics.py` | 7 KB | None (standalone) | t_test, anova_test, CI, correlation — from-scratch implementations |
| `discourse_patterns.py` | 7 KB | None (data definitions) | Discourse pattern definitions |
| `semantic_entropy.py` | ~6 KB | None (standalone) | TF-IDF + KMeans + Shannon entropy per term |

### `src/visualization/` (Visualization — 5 modules)

| Module | Size | Dependencies | Role |
|--------|------|-------------|------|
| `concept_visualization.py` | 39 KB | `visualization` (styling) | Generates all 11 research figures |
| `statistical_visualization.py` | 28 KB | `visualization` (styling) | Forest plots, violin plots, heatmaps |
| `plots.py` | 9 KB | `visualization` (engine) | Publication-quality plot helpers |
| `visualization.py` | 7 KB | None (standalone) | VisualizationEngine, VIZ_CONFIG style config |
| `figure_manager.py` | 3 KB | None (standalone) | Figure registry: JSON tracking + SHA integrity |

### `scripts/` → `src/` Dependencies

```
# Auto-discovered (no _ prefix) — run by pipeline
01_build_corpus.py            → src.data.literature_mining, src.analysis.term_extraction
02_generate_figures.py        → src.visualization.concept_visualization, src.analysis.*,
                                src.data.*, src.core.*

# Manually-run scripts (_ prefix — not auto-discovered)
_analysis_pipeline.py         → src.analysis.*, src.visualization.*
_literature_analysis_pipeline.py → src.analysis.*, src.visualization.*, src.data.*
_conceptual_mapping_script.py → src.analysis.conceptual_mapping, src.visualization.*
_domain_analysis_script.py    → src.analysis.domain_analysis
_discourse_analysis_script.py → src.analysis.discourse_analysis
_generate_domain_figures.py   → src.visualization.concept_visualization, src.analysis.domain_analysis
```

## Hotspots and Risks

### Large Modules (Decomposition Candidates)

1. **`domain_analysis.py`** (40 KB) — Handles domain statistics, term mapping, frequency distribution, co-occurrence, and ambiguity scoring. Could be split into `domain_statistics.py` + `domain_comparison.py`.

2. **`concept_visualization.py`** (39 KB) — Generates all 11 figures: concept map, terminology network, domain comparison, domain overlap heatmap, anthropomorphic framing, concept hierarchy, domain overview grid, domain patterns grid, and 3 per-domain figures. Could be split by figure group.

3. **`conceptual_mapping.py`** (37 KB) — Handles concept extraction, term assignment, and relationship graph construction. Could split NetworkX graph operations into their own module.

### Cross-Module Coupling

- **Visualization font enforcement**: The 16pt font floor is applied in `concept_visualization.py` and `statistical_visualization.py` independently. A shared `VIZ_CONFIG` dict in `visualization.py` centralizes defaults but each module still overrides `plt.rcParams` locally.

- **Shared domain computation**: Both `_literature_analysis_pipeline.py` and `_conceptual_mapping_script.py` compute Jaccard co-occurrence for terminology networks. This is partially centralized in `ConceptualMapper._build_concept_relationships()` but duplicated elsewhere.

- **Script size**: `_generate_domain_figures.py` and `_literature_analysis_pipeline.py` contain substantial orchestration logic — candidates for moving more computation into `src/` modules.

### Clean-Slate Side Effect

`02_generate_figures.py::_setup_directories()` **wipes `output/figures/` and `output/data/`** before every run. Any code that reads from these directories during a pipeline run must run *after* `02_generate_figures.py` completes, not during.

### Path Handling

Scripts compute `PROJECT_ROOT` at import time using `Path(__file__).parent.parent`. All output paths (`output/figures/`, `output/data/`) are absolute, resolved against `PROJECT_ROOT`. Do not alter `PROJECT_ROOT` logic without updating all downstream callers.

## Safe-Change Checklist

1. **Scope**: Identify which modules are affected using the dependency map above
2. **API contract**: Check function signatures and docstrings before modifying public APIs
3. **Tests**: Run `uv run pytest tests/ -x -q` before and after changes (948 tests)
4. **Figures**: After touching visualization code, run `uv run python scripts/02_generate_figures.py` and verify all 11 outputs
5. **Font floor**: If modifying any visualization, verify 16pt minimum font size is preserved
6. **Preflight**: Run `uv run python scripts/_manuscript_preflight.py --strict` to verify figure references

## Quick Recipes

### Add a New Ento-Linguistic Domain

1. Add domain seed lexicon to `TerminologyExtractor` in `src/analysis/term_extraction.py`
2. Add domain-specific analyser method to `DomainAnalyzer` in `src/analysis/domain_analysis.py`
3. Add domain-specific test cases in `tests/test_domain_analysis.py`
4. Wire domain into `scripts/02_generate_figures.py` figure generation
5. Add domain discussion to manuscript section `04_experimental_results.md`

### Modify Term Extraction

1. Edit `src/analysis/term_extraction.py`
2. Run `uv run pytest tests/test_term_extraction.py tests/test_term_extraction_coverage.py -v`
3. Verify downstream: `uv run pytest tests/test_domain_analysis.py tests/test_conceptual_mapping.py -v`
4. Regenerate figures: `uv run python scripts/02_generate_figures.py`

### Modify Semantic Entropy or CACE

1. Edit `src/analysis/semantic_entropy.py` or `src/analysis/cace_scoring.py`
2. Run `uv run pytest tests/test_semantic_entropy.py tests/test_cace_scoring.py -v`
3. Verify `domain_analysis` still passes: `uv run pytest tests/test_domain_analysis.py -v`
4. Regenerate figures — CACE scores feed directly into the domain comparison figure panels

### Extend Visualizations

1. Add plot function to appropriate module (`concept_visualization.py` or `statistical_visualization.py`)
2. Use `VisualizationEngine.STYLE_CONFIG` for consistent styling — avoid raw `plt.subplots()` sizing
3. Enforce 16pt font floor via `plt.rcParams` update
4. Register new figure with `FigureManager` in `02_generate_figures.py`
5. Add tests in `tests/test_concept_visualization.py` or `tests/test_statistical_visualization.py`

### Stabilize Shared Computation

1. Extract Jaccard co-occurrence computation from `_literature_analysis_pipeline.py` and `_conceptual_mapping_script.py` into `ConceptualMapper._build_concept_relationships()` (already partially done) or a new `src/analysis/network_utils.py`
2. Both scripts call the shared function
3. Add unit tests for the extracted function

## See Also

- [development_workflow.md](development_workflow.md) — Environment setup and commands
- [testing_expansion_plan.md](testing_expansion_plan.md) — Test coverage roadmap
- [standards_compliance.md](standards_compliance.md) — Current project metrics
