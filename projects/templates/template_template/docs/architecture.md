# Template Meta-Project Architecture

## Overview

The `template` meta-project is a self-referential study: it uses the `template/` infrastructure to analyze and document the `template/` infrastructure itself. All metrics in the manuscript are computed from the live repository at build time.

## Two-Layer Alignment

| Layer | Location | Contents |
|-------|----------|----------|
| **Infrastructure** (Layer 1) | `infrastructure/` (repo root) | Live module inventory via `discover_infrastructure_modules()` |
| **Project** (Layer 2) | `projects/templates/template_template/` | `src/template_template/`, manuscript, scripts, tests |

The project imports from infrastructure but never modifies it.

## Source Module Architecture

```
src/template_template/
├── __init__.py           # Public API surface
├── introspection.py      # Repository analysis engine
├── architecture_viz.py   # Figure generation (matplotlib)
├── metrics.py            # Metric formatting + token dict
└── inject_metrics.py     # ${variable} substitution
```

### `introspection.py`

Exports:

- **`build_infrastructure_report(repo_root) → InfrastructureReport`**: modules, projects, YAML pipeline stages, numbered scripts, file counts
- **`load_pipeline_stages_from_yaml(repo_root)`**: parses `infrastructure/core/pipeline/pipeline.yaml`
- **`enumerate_numbered_scripts(scripts_dir)`** / **`count_pipeline_stages`**: `scripts/NN_*.py` inventory only
- **`resolve_template_repo_root(project_dir)`**: finds Layer-1 repo from WIP/private paths
- **`discover_projects(repo_root)`**: manuscript workspaces across flat children plus typed subfolders (`templates/`, `active/`, `working/`, `published/`, `archive/`, `other/`), returning bare leaf names

`InfrastructureReport` properties:

- `pipeline_stages_declared` — YAML stage count (12)
- `pipeline_stages_default_full` — default full run (10)
- `pipeline_stages_core_only` — `--core-only` (8)

### `architecture_viz.py`

| Figure | Function | Description |
|--------|----------|-------------|
| `architecture_overview.png` | `generate_architecture_overview()` | Two-layer overview with dynamic module grid |
| `pipeline_stages.png` | `generate_pipeline_stages()` | YAML DAG with tag colouring |
| `module_inventory.png` | `generate_module_inventory()` | Horizontal bar chart |
| `comparative_feature_matrix.png` | `generate_comparative_feature_matrix()` | Heatmap vs peer tools |

### `metrics.py`

- `build_manuscript_metrics_dict(repo_root)` — all `${variable}` mappings
- `build_module_inventory_table(modules)` — Markdown table for chapter 06
- Pipeline tokens: `pipeline_stages_declared`, `pipeline_stages_default_full`, `pipeline_stages_core_only`, `public_exemplar_list`

### `inject_metrics.py`

Reads `manuscript/*.md`, substitutes tokens from `metrics.json`, writes `output/manuscript/`.

## Data Flow

```
introspection.py → InfrastructureReport
        ├─ metrics.py → metrics.json → inject_metrics.py → output/manuscript/
        └─ architecture_viz.py → output/figures/*.png
```

## Script Architecture (Thin Orchestrators)

Both `generate_architecture_viz.py` and `generate_manuscript_metrics.py` resolve the Layer-1 repo via `_locate_repo_root()` (works from `projects/templates/template_template/`), then delegate to `src/template_template/`.

## Verification

From the public template repo root:

```bash
cd /Users/4d/Documents/GitHub/template
uv run pytest projects/templates/template_template/tests/ \
  --cov=projects/templates/template_template/src/template_template --cov-fail-under=90 -v
uv run python projects/templates/template_template/scripts/generate_manuscript_metrics.py
uv run python projects/templates/template_template/scripts/generate_architecture_viz.py
```
