# AGENTS: Template Meta-Project

Technical specification for the self-referential documentation project that analyzes and documents the Docxology Template repository.

## Purpose

Programmatic introspection and documentation of the template repository's own architecture, serving as both a live demonstration of pipeline capabilities and a comprehensive technical reference.

## Architecture

```
template/
├── src/template/              # Introspection module (5 functions, 5 dataclasses)
│   ├── __init__.py            # Public API exports
│   └── introspection.py       # Repository analysis functions
├── scripts/                   # Thin orchestrator (3 figures)
│   └── generate_architecture_viz.py
├── tests/                     # 36 tests, 90%+ coverage
│   ├── conftest.py            # Path setup
│   └── test_meta.py           # Comprehensive test suite
├── manuscript/                # 8 chapters (~7500 words)
│   ├── 01_abstract.md         # Dense system summary
│   ├── 02_introduction.md     # Reproducibility crisis + solution
│   ├── 03_methods.md          # Architecture + pipeline detail
│   ├── 04_results.md          # Benchmarks + inventory
│   ├── 05_discussion.md       # Tradeoffs + conclusion
│   ├── 06_infrastructure_modules.md  # 10-module reference
│   ├── 07_security_provenance.md     # Steganography deep-dive
│   ├── 08_appendices.md       # Reference tables
│   └── config.yaml            # Metadata + testing config
└── output/                    # Generated artifacts
```

## Key Subsystems

### 1. Introspection Module (`src/template/introspection.py`)

| Function | Returns | Description |
|----------|---------|-------------|
| `discover_infrastructure_modules` | `list[ModuleInfo]` | Scan infrastructure subpackages |
| `discover_projects` | `list[ProjectInfo]` | Find project workspaces |
| `count_pipeline_stages` | `list[PipelineStage]` | Enumerate pipeline scripts |
| `analyze_test_coverage_config` | `CoverageConfig` | Parse testing thresholds |
| `build_infrastructure_report` | `InfrastructureReport` | Full aggregated report |

### 2. Visualization Script (`scripts/generate_architecture_viz.py`)

| Output | Description |
|--------|-------------|
| `architecture_overview.png` | Two-Layer Architecture diagram |
| `pipeline_stages.png` | 8-stage pipeline waterfall |
| `module_inventory.png` | Module file count bar chart |

### 3. Test Suite (`tests/test_meta.py`)

- 36 tests in 5 classes covering all public functions
- Zero-Mock: all tests run against real repository filesystem
- Minimum-count assertions for forward compatibility

## Patterns

- **Thin Orchestrator**: `scripts/` imports from `src/template/`, contains no domain logic
- **Zero-Mock Testing**: All tests use real paths, real imports, real YAML parsing
- **Documentation Duality**: AGENTS.md + README.md at every directory level
- **Accessibility**: 16pt font floor, colorblind-safe palette, 300 DPI figures
