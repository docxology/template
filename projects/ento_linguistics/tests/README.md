# tests/ — Ento-Linguistic Test Suite

Test suite for `src/` scientific code. **923 tests**, **90%+ coverage**, **no mocks**.

## Quick Start

```bash
# All tests with coverage
uv run pytest tests/ -x -q
uv run pytest tests/ --cov=src --cov-report=html

# Integration tests only
uv run pytest tests/integration/ -v
```

## Test Files (35 unit + 5 integration = 40 total)

### analysis/

| File | Module |
|------|--------|
| `test_term_extraction.py` | `analysis/term_extraction.py` |
| `test_domain_analysis.py` | `analysis/domain_analysis.py` |
| `test_semantic_entropy.py` | `analysis/semantic_entropy.py` |
| `test_cace_scoring.py` | `analysis/cace_scoring.py` |
| `test_conceptual_mapping.py` | `analysis/conceptual_mapping.py` |
| `test_discourse_analysis.py` | `analysis/discourse_analysis.py` |
| `test_discourse_patterns.py` | `analysis/discourse_patterns.py` |
| `test_rhetorical_analysis.py` | `analysis/rhetorical_analysis.py` |
| `test_persuasive_analysis.py` | `analysis/persuasive_analysis.py` |
| `test_statistics.py` | `analysis/statistics.py` |
| `test_text_analysis.py` | `analysis/text_analysis.py` |
| `test_performance.py` | `analysis/performance.py` |

### visualization/

| File | Module |
|------|--------|
| `test_concept_visualization.py` | `visualization/concept_visualization.py` |
| `test_statistical_visualization.py` | `visualization/statistical_visualization.py` |
| `test_visualization.py` | `visualization/visualization.py` |
| `test_plots.py` | `visualization/plots.py` |
| `test_figure_manager.py` | `visualization/figure_manager.py` |

### core/

| File | Module |
|------|--------|
| `test_exceptions.py` | `core/exceptions.py` |
| `test_logging.py` | `core/logging.py` |
| `test_metrics.py` | `core/metrics.py` |
| `test_parameters.py` | `core/parameters.py` |
| `test_validation.py` | `core/validation.py` |
| `test_core_validation.py` | `core/validation.py` (extended coverage) |
| `test_markdown_integration.py` | `core/markdown_integration.py` |
| `test_example.py` | `core/example.py` |

### data/

| File | Module |
|------|--------|
| `test_literature_mining.py` | `data/literature_mining.py` |
| `test_data_generator.py` | `data/data_generator.py` |
| `test_data_processing.py` | `data/data_processing.py` |
| `test_loader.py` | `data/loader.py` |

### pipeline/

| File | Module |
|------|--------|
| `test_simulation.py` | `pipeline/simulation.py` |
| `test_reporting.py` | `pipeline/reporting.py` |
| `test_pipeline_init.py` | `pipeline/__init__.py` |

### other

| File | Purpose |
|------|---------|
| `test_package_imports.py` | Import smoke tests for all modules |

### integration/ (5 files)

| File | Purpose |
|------|---------|
| `test_integration_pipeline.py` | Full analysis pipeline end-to-end |
| `test_example_figure.py` | Figure generation and file output |
| `test_generate_research_figures.py` | Multi-figure pipeline |

## Testing Philosophy

- **No mocks** — all tests use real data, real algorithms
- **Deterministic** — fixed seeds (`random_state=42`, `np.random.default_rng(seed)`)
- **90%+ coverage** — required across all `src/` modules

## See Also

- [`AGENTS.md`](AGENTS.md) — full documentation
- [`../src/README.md`](../src/README.md) — source code overview
- [`../docs/development_workflow.md`](../docs/development_workflow.md) — test commands
