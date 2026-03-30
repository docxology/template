# AGENTS: Template Meta-Project

Technical specification for the self-referential documentation project that analyzes and documents the Docxology Template repository.

## Purpose

Programmatic introspection and documentation of the template repository's own architecture, serving as both a live demonstration of pipeline capabilities and a comprehensive technical reference.

## Architecture

```text
template/
├── src/template/              # Core modules (5 files, 6 dataclasses)
│   ├── __init__.py            # Public API exports
│   ├── introspection.py       # Repository analysis functions
│   ├── metrics.py             # Manuscript metrics computation
│   ├── inject_metrics.py      # ${variable} substitution in chapters
│   └── architecture_viz.py    # 4-figure generation from introspection data
├── scripts/                   # Thin orchestrators
│   ├── generate_architecture_viz.py   # Generates 4 architecture PNGs
│   └── generate_manuscript_metrics.py # Builds metrics + renders chapters
├── tests/                     # 65 tests, 90%+ coverage
│   ├── conftest.py            # Path setup
│   ├── test_meta.py           # 49 tests across 6 classes
│   ├── test_metrics.py        # 10 tests for metrics helpers
│   └── test_architecture_viz.py  # 6 tests for figure generation
├── manuscript/                # 21 chapters + config + preamble + references
│   ├── 01_abstract.md         # Dense system summary
│   ├── 02_introduction.md     # Reproducibility crisis + solution
│   ├── 03a_architecture.md    # Two-Layer patterns
│   ├── 03b_pipeline.md        # 10-stage DAG pipeline + orchestrators
│   ├── 03c_documentation.md   # Documentation Duality + Agentskills, MCP mapping
│   ├── 03d_fair_iac.md        # FAIR4RS alignment, IaC
│   ├── 03e_quality.md         # Zero-Mock, visualization standards
│   ├── 04_results.md          # Benchmarks + inventory + figures
│   ├── 05a_zeromock_tradeoff.md # Zero-Mock tradeoff analysis
│   ├── 05b_scalability.md     # 1-to-N project scaling
│   ├── 05c_comparison.md      # Tool comparison + FAIR4RS update
│   ├── 05d_ai_collaboration.md # AI model, limitations
│   ├── 05e_future_conclusion.md # Future + conclusion
│   ├── 06_infrastructure_modules.md  # 13-module reference
│   ├── 07_security_provenance.md     # Steganography deep-dive
│   ├── 08a_appendix_pipeline.md   # Appendix A: Pipeline reference
│   ├── 08b_appendix_config.md     # Appendix B: Configuration
│   ├── 08c_appendix_directory.md  # Appendix C: Directory tree
│   ├── 08d_appendix_exemplars.md  # Appendix D: Exemplar projects
│   ├── 08e_appendix_docs.md       # Appendix E: Documentation map
│   ├── 08f_appendix_matrix.md     # Appendix F: Comparative matrix
│   └── config.yaml            # Metadata + rendering config
├── docs/                      # 7 technical documentation files
└── output/                    # Generated artifacts (figures, manuscripts, PDF)
```

## Key Subsystems

### 1. Introspection Module (`src/template/introspection.py`)

| Function                       | Returns                 | Description                            |
|--------------------------------|-------------------------|----------------------------------------|
| `discover_infrastructure_modules` | `list[ModuleInfo]`   | Scan infrastructure subpackages        |
| `discover_projects`            | `list[ProjectInfo]`     | Find project workspaces                |
| `count_pipeline_stages`        | `list[PipelineStage]`   | Enumerate pipeline scripts             |
| `analyze_test_coverage_config` | `CoverageConfig`        | Parse testing thresholds               |
| `build_infrastructure_report`  | `InfrastructureReport`  | Full aggregated report                 |

### 2. Metrics Module (`src/template/metrics.py`)

| Function                       | Returns  | Description                                 |
|--------------------------------|----------|---------------------------------------------|
| `count_test_functions`         | `int`    | Count `def test_` definitions               |
| `count_docs_markdown_files`    | `int`    | Count `.md` files under `docs/`             |
| `count_docs_subdirs`           | `int`    | Count `docs/` subdirectories                |
| `format_count`                 | `str`    | Format count with optional `~` prefix       |
| `build_manuscript_metrics_dict`| `dict`   | Full metrics from live repo data            |
| `save_metrics_json`            | `Path`   | Serialise metrics to JSON                   |
| `build_module_inventory_table` | `str`    | Render module inventory as Markdown         |

### 3. Injection Module (`src/template/inject_metrics.py`)

| Function             | Returns  | Description                                    |
|----------------------|----------|------------------------------------------------|
| `load_metrics`       | `dict`   | Deserialise `metrics.json` to flat dict        |
| `render_chapter`     | `Path`   | Substitute `${vars}` in one chapter            |
| `render_all_chapters`| `list[Path]` | Process all chapters + copy ancillary files|

### 4. Visualization Module (`src/template/architecture_viz.py`)

| Output                          | Description                                                |
|---------------------------------|------------------------------------------------------------|
| `architecture_overview.png`     | Two-Layer architecture and 13 modules                      |
| `pipeline_stages.png`           | 10-stage DAG pipeline flow with descriptions               |
| `module_inventory.png`          | Complexity/size chart for all infrastructure with doc badges|
| `comparative_feature_matrix.png`| 14×10 tool capability heatmap                              |

### 5. Test Suite (`tests/`)

- 65 tests across 3 files and 6 classes covering all public functions
- Zero-Mock: all tests run against real repository filesystem
- Minimum-count assertions for forward compatibility

## Patterns

- **Thin Orchestrator**: `scripts/` imports from `src/template/`, contains no domain logic
- **Zero-Mock Testing**: All tests use real paths, real imports, real YAML parsing
- **Documentation Duality**: AGENTS.md + README.md at every directory level
- **Accessibility**: 16 pt font floor, colorblind-safe palette, 200 DPI figures
- **Four-Layer Doc Badges**: A (AGENTS.md) · R (README.md) · S (SKILL.md) · P (PAI.md)
