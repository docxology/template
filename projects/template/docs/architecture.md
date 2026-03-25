# Template Meta-Project Architecture

## Overview

The `template` meta-project is a self-referential study: it uses the `template/` infrastructure to analyze and document the `template/` infrastructure itself. This creates a unique architectural constraint — all metrics in the manuscript must be computed from the live repository at build time, not hardcoded.

## Two-Layer Alignment

The template project follows the system-wide Two-Layer Architecture:

| Layer | Location | Contents |
|-------|----------|----------|
| **Infrastructure** (Layer 1) | `infrastructure/` (repo root) | 12 subpackages, ~150 modules: logging, rendering, validation, steganography |
| **Project** (Layer 2) | `projects/template/` | 5 src modules, 21 manuscript chapters, 2 scripts, 4 test files |

The project imports from infrastructure (`infrastructure.core.logging.utils`, etc.) but never modifies it.

## Source Module Architecture

```
src/template/
├── __init__.py           # Public API surface
├── introspection.py      # Repository analysis engine (core logic)
├── architecture_viz.py   # Figure generation (matplotlib)
├── metrics.py            # Metric formatting utilities
└── inject_metrics.py     # ${variable} → computed value substitution
```

### `introspection.py` — The Core Engine

The central module. Exports:

- **`build_infrastructure_report(repo_root) → InfrastructureReport`**: Scans the entire repo to produce a dataclass containing:
  - `module_count`: Number of infrastructure subpackages
  - `project_count`: Number of active projects
  - `stage_count`: Number of pipeline stages
  - `total_python_files`: Repository-wide `.py` count
  - `total_test_files`: Repository-wide test file count
  - `modules_data`: Per-module detail (file counts, documentation flags)
  - `projects_data`: Per-project detail (test counts, coverage)

- **`PipelineStage`**: Dataclass representing a single pipeline stage (name, script, description).

Key design decisions:
- Excludes `.venv`, `__pycache__`, `.git` from file counts via `_is_excluded_path()`
- Uses `rglob("*.py")` for per-module file counting
- Counts tests by scanning `test_*.py` filenames in project `tests/` dirs

### `architecture_viz.py` — Figure Generation

Produces 4 publication-quality PNG figures:

| Figure | Function | Description |
|--------|----------|-------------|
| `architecture_overview.png` | `create_architecture_overview()` | Two-Layer Architecture with module boxes |
| `pipeline_stages.png` | `create_pipeline_diagram()` | Sequential 9-stage flow with viridis colours |
| `module_inventory.png` | `create_module_inventory()` | Horizontal bar chart of file counts |
| `comparative_feature_matrix.png` | `create_comparative_matrix()` | 14×10 heatmap (template vs 9 tools) |

All figures enforce:
- 16pt minimum font (accessibility floor)
- Colorblind-safe palettes (IBM Design / Wong)
- 150–300 DPI
- Descriptive axis labels

### `metrics.py` — Metric Formatting

Utility functions for rendering metrics in manuscript-friendly formats:

- `format_count(n)`: Human-readable number formatting (`3083` → `~3,083`)
- `build_module_inventory_table(report)`: Markdown table of module details
- `build_manuscript_metrics_dict(report)`: Dictionary of all `${variable}` → value mappings

### `inject_metrics.py` — Variable Injection

Reads manuscript `*.md` files, replaces `${variable}` tokens with computed values from `metrics.json`, and writes rendered versions to `output/manuscript/`.

Template variables include:

| Variable | Example Value | Source |
|----------|---------------|--------|
| `${module_count}` | `12` | `InfrastructureReport.module_count` |
| `${total_infra_python_files}` | `150` | `InfrastructureReport.total_python_files` |
| `${infra_test_count_approx}` | `3,083` | `InfrastructureReport.total_test_files` |
| `${project_template_test_count}` | `65` | Test file scan |
| `${docs_file_count}` | `170` | Documentation file scan |

## Data Flow

```
                    ┌─────────────────────────┐
                    │  introspection.py        │
                    │  build_infrastructure_   │
                    │  report(repo_root)       │
                    └─────────┬───────────────┘
                              │
                    ┌─────────▼───────────────┐
                    │  InfrastructureReport    │
                    │  (module_count, stages,  │
                    │   python_files, etc.)    │
                    └───┬─────────────────┬───┘
                        │                 │
           ┌────────────▼──┐    ┌────────▼──────────┐
           │ metrics.py    │    │ architecture_viz   │
           │ → metrics.json│    │ → 4 PNG figures    │
           └────────┬──────┘    └───────────────────┘
                    │
           ┌────────▼──────────┐
           │ inject_metrics.py │
           │ manuscript/*.md   │
           │ + metrics.json    │
           │ → output/         │
           │   manuscript/*.md │
           └───────────────────┘
```

## Script Architecture (Thin Orchestrators)

### `generate_architecture_viz.py`

1. Sets up `PYTHONPATH` (repo root + `src/`)
2. Calls `generate_all_architecture_figures(repo_root, project_dir)` from `template/__init__.py`
3. Logs output paths

### `generate_manuscript_metrics.py`

1. Sets up `PYTHONPATH`
2. Calls `build_infrastructure_report()` → `InfrastructureReport`
3. Calls `build_manuscript_metrics_dict(report)` → variable dict
4. Scans `projects/*/tests/` for per-project test counts
5. Writes `output/data/metrics.json`
6. Calls `render_all_chapters()` → `output/manuscript/*.md`

Both scripts contain **zero domain logic** — all computation is in `src/template/`.
