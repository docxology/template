# Refactor Playbook — Ento-Linguistics

Module dependency map, hotspots, and safe-change recipes for the Ento-Linguistic Domains codebase.

## Module Dependency Map

### `src/analysis/` (Domain-Specific Analysis)

| Module | Size | Dependencies | Role |
|--------|------|-------------|------|
| `domain_analysis.py` | 40 KB | `term_extraction`, `text_analysis` | Cross-domain comparison engine |
| `conceptual_mapping.py` | 37 KB | `term_extraction`, `domain_analysis` | Relationship modeling and mapping |
| `term_extraction.py` | 20 KB | None (standalone) | Core term extraction from corpora |
| `persuasive_analysis.py` | 15 KB | `discourse_analysis` | Persuasive technique detection |
| `discourse_analysis.py` | 14 KB | `discourse_patterns` | Framing pattern analysis |
| `text_analysis.py` | 14 KB | None (standalone) | NLP for scientific texts |
| `rhetorical_analysis.py` | 11 KB | None (standalone) | Rhetorical strategy analysis |
| `performance.py` | 9 KB | None (standalone) | Convergence and scalability metrics |
| `statistics.py` | 7 KB | None (standalone) | Statistical hypothesis testing |
| `discourse_patterns.py` | 7 KB | None (data definitions) | Discourse pattern definitions |

### `src/visualization/` (Visualization)

| Module | Size | Dependencies | Role |
|--------|------|-------------|------|
| `concept_visualization.py` | 39 KB | `visualization` (styling) | Network plots, domain comparison |
| `statistical_visualization.py` | 28 KB | `visualization` (styling) | Statistical result visualization |
| `plots.py` | 9 KB | `visualization` (engine) | Publication-quality plot helpers |
| `visualization.py` | 7 KB | None (standalone) | VisualizationEngine, style config |
| `figure_manager.py` | 3 KB | None (standalone) | Figure registry and tracking |

### `scripts/` → `src/` Dependencies

```
analysis_pipeline.py          → src.analysis.*, src.visualization.*
literature_analysis_pipeline.py → src.analysis.*, src.visualization.*, src.data.*
generate_research_figures.py   → src.visualization.concept_visualization, src.analysis.*
conceptual_mapping_script.py   → src.analysis.conceptual_mapping, src.visualization.*
domain_analysis_script.py      → src.analysis.domain_analysis
discourse_analysis_script.py   → src.analysis.discourse_analysis
```

## Hotspots and Risks

### Large Modules (Decomposition Candidates)

1. **`domain_analysis.py`** (40 KB) — Handles domain statistics, term mapping, cross-domain comparison, and ambiguity scoring. Could be split into `domain_statistics.py` + `domain_comparison.py`.

2. **`concept_visualization.py`** (39 KB) — Combines network visualization, domain comparison plots, heatmaps, and hierarchy diagrams. Could be split by plot type.

3. **`conceptual_mapping.py`** (37 KB) — Handles both concept extraction and relationship graph construction. Could split graph operations into their own module.

### Cross-Module Coupling

- **Visualization font enforcement**: The 16pt font floor is applied in `concept_visualization.py` and `statistical_visualization.py` independently. A shared `VIZ_CONFIG` dict in `visualization.py` centralizes defaults but each module still overrides `plt.rcParams` locally.

- **Shared domain computation**: Both `literature_analysis_pipeline.py` and `conceptual_mapping_script.py` compute Jaccard co-occurrence for terminology networks. This could be extracted into a shared utility in `src/analysis/`.

- **Script size**: `generate_research_figures.py` (31 KB) and `literature_analysis_pipeline.py` (29 KB) contain substantial logic — candidates for moving more computation into `src/` modules.

### Path Handling

Scripts use relative paths (`output/figures/`, `output/data/`). All paths are computed relative to `PROJECT_ROOT`, which is resolved at import time. Changing the script's working directory without adjusting `PROJECT_ROOT` will break figure output.

## Safe-Change Checklist

1. **Scope**: Identify which modules are affected using the dependency map above
2. **API contract**: Check function signatures and docstrings before modifying public APIs
3. **Tests**: Run `uv run pytest tests/ -x -q` before and after changes (778 tests)
4. **Figures**: After touching visualization code, regenerate figures with `uv run python scripts/generate_research_figures.py` and verify outputs
5. **Font floor**: If modifying any visualization, verify 16pt minimum font size is preserved
6. **Preflight**: Run `uv run python scripts/manuscript_preflight.py --strict` to verify figure references

## Quick Recipes

### Add a New Ento-Linguistic Domain

1. Define domain terms and patterns in the domain analysis configuration
2. Add domain-specific test cases in `tests/test_domain_analysis.py`
3. Run `uv run python scripts/domain_analysis_script.py` to verify analysis
4. Generate domain figures with `uv run python scripts/generate_domain_figures.py`
5. Add domain discussion to manuscript section `04_experimental_results.md`

### Modify Term Extraction

1. Edit `src/analysis/term_extraction.py`
2. Run `uv run pytest tests/test_term_extraction.py tests/test_term_extraction_coverage.py -v`
3. Verify downstream: `uv run pytest tests/test_domain_analysis.py tests/test_conceptual_mapping.py -v`
4. Regenerate figures to verify visual output

### Extend Visualizations

1. Add plot function to appropriate module (`concept_visualization.py` or `statistical_visualization.py`)
2. Use `VisualizationEngine.STYLE_CONFIG` for consistent styling — avoid raw `plt.subplots()` sizing
3. Enforce 16pt font floor via `plt.rcParams` update
4. Register new figure with `FigureManager` in the calling script
5. Add tests in `tests/test_concept_visualization.py` or `tests/test_statistical_visualization.py`

### Stabilize Shared Computation

1. Extract Jaccard co-occurrence computation from both `literature_analysis_pipeline.py` and `conceptual_mapping_script.py` into `src/analysis/term_extraction.py` (or a new `src/analysis/network_utils.py`)
2. Both scripts call the shared function
3. Add unit tests for the extracted function

## See Also

- [development_workflow.md](development_workflow.md) — Environment setup and commands
- [testing_expansion_plan.md](testing_expansion_plan.md) — Test coverage roadmap
- [standards_compliance.md](standards_compliance.md) — Current project metrics
