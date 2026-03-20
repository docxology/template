# docs/ — Template Meta-Project Documentation Hub

## Overview

Technical documentation for the `template` meta-project — the self-referential study that describes the `template/` architecture. This project is built by the same pipeline it documents, serving as a live proof-of-concept for the system's capabilities.

## Files

| File | Purpose |
|------|---------|
| `AGENTS.md` | This file — directory index and agent instructions |
| `VERIFICATION.md` | Sub-minute verification routine (tests, figures, introspection) |
| `architecture.md` | Project architecture: src/ modules, scripts, data flow |
| `testing_philosophy.md` | Zero-mock standard, test categories, coverage targets |
| `manuscript_guide.md` | Manuscript file structure, variable injection, rendering |
| `rendering_pipeline.md` | How Stage 02 + Stage 03 produce the final PDF |

## Project Structure

```text
projects/template/
├── src/template/                  # Domain logic (Layer 2)
│   ├── __init__.py                # Public API (generate_all_architecture_figures)
│   ├── introspection.py           # Repository analysis engine
│   ├── architecture_viz.py        # Matplotlib figure generators
│   ├── metrics.py                 # Metric formatting utilities
│   └── inject_metrics.py          # ${variable} → value substitution
├── scripts/                       # Thin Orchestrators (Stage 02)
│   ├── generate_architecture_viz.py   # Figure generation orchestrator
│   └── generate_manuscript_metrics.py # Metrics + variable injection orchestrator
├── tests/                         # Test suite (65 tests, 90%+ coverage)
│   ├── conftest.py                # Shared fixtures (repo root path)
│   ├── test_meta.py               # Introspection + figure + integration tests
│   ├── test_architecture_viz.py   # Visualization output tests
│   └── test_metrics.py            # Metric formatting + table builder tests
├── manuscript/                    # 21 Markdown chapters + references.bib
├── docs/                          # This directory
├── output/                        # Generated artifacts (figures, PDFs, data)
├── data/                          # Input data (currently empty)
└── pyproject.toml                 # Project metadata
```

## Key Conventions

- **Read-first protocol**: AI agents must read this file before modifying any project file
- **Architecture isolation**: `src/` is pure logic, `scripts/` is orchestration only
- **Zero-mock enforcement**: No `unittest.mock`, `MagicMock`, or `@patch` anywhere
- **Variable injection**: Manuscript files use `${variable}` tokens (e.g., `${module_count}`) that are replaced with live values during Stage 02
- **Self-referential**: This project's manuscript describes the infrastructure it runs on — metrics are computed at build time, not hardcoded

## Key Modules

| Module | Key Exports | Purpose |
|--------|-------------|---------|
| `introspection` | `build_infrastructure_report()`, `InfrastructureReport`, `PipelineStage` | Analyze the live repository structure |
| `architecture_viz` | `create_architecture_overview()`, `create_pipeline_diagram()`, `create_module_inventory()`, `create_comparative_matrix()` | Generate 4 publication-quality figures |
| `metrics` | `format_count()`, `build_module_inventory_table()`, `build_manuscript_metrics_dict()` | Format metrics for manuscript injection |
| `inject_metrics` | `render_all_chapters()` | Substitute `${variable}` tokens in manuscript chapters |

## Data Flow

```
introspection.py → metrics.json → inject_metrics.py → output/manuscript/*.md
                 ↘ architecture_viz.py → output/figures/*.png
```

## Reading Order

1. This file — Understand project structure and conventions
2. `architecture.md` — Understand module boundaries and data flow
3. `testing_philosophy.md` — Understand test requirements before writing code
4. `manuscript_guide.md` — Understand the 21-file manuscript structure
5. `rendering_pipeline.md` — Understand how manuscript becomes PDF
6. `VERIFICATION.md` — Run the verification routine after making changes

## See Also

- [../AGENTS.md](../AGENTS.md) — Project-level technical documentation
- [../manuscript/AGENTS.md](../manuscript/AGENTS.md) — Manuscript chapter index
- [../src/template/AGENTS.md](../src/template/AGENTS.md) — Source code documentation
- [../../AGENTS.md](../../AGENTS.md) — Root template documentation
