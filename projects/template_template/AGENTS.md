# AGENTS: Template Meta-Project

Technical specification for the self-referential documentation project that analyzes and documents the Docxology Template repository.

**Location:** `projects/passive/template/` (symlinked as `projects_in_progress/template/` in the public template checkout).

## Purpose

Programmatic introspection and documentation of the template repository's own architecture, serving as both a live demonstration of pipeline capabilities and a comprehensive technical reference.

## Architecture

```text
template/
├── src/template/              # Core modules
│   ├── introspection.py       # YAML + filesystem repository analysis
│   ├── metrics.py             # Manuscript metrics + token dict
│   ├── inject_metrics.py      # ${variable} substitution
│   └── architecture_viz.py    # Four publication figures
├── scripts/                   # Thin orchestrators (metrics, figures)
├── tests/                     # 75 tests, 90%+ coverage on src/template/
├── manuscript/                # 21 chapters + config + references
├── docs/                      # Project-level technical docs
└── output/                    # Generated figures, metrics, manuscript, PDF
```

## Key Subsystems

### Introspection (`src/template/introspection.py`)

| Function | Returns | Description |
|----------|---------|-------------|
| `discover_infrastructure_modules` | `list[ModuleInfo]` | Scan `infrastructure/` subpackages |
| `discover_projects` | `list[ProjectAnalysis]` | Manuscript workspaces (`projects/` wins over WIP) |
| `load_pipeline_stages_from_yaml` | `list[PipelineStage]` | Parse `pipeline.yaml` (12 declared stages) |
| `enumerate_numbered_scripts` / `count_pipeline_stages` | `list[PipelineStage]` | `scripts/NN_*.py` inventory only |
| `resolve_template_repo_root` | `Path` | Locate Layer-1 repo from WIP/private paths |
| `build_infrastructure_report` | `InfrastructureReport` | Full aggregated report |

`InfrastructureReport` properties: `pipeline_stages_declared` (12), `pipeline_stages_default_full` (10), `pipeline_stages_core_only` (8).

### Metrics (`src/template/metrics.py`)

| Function | Description |
|----------|-------------|
| `build_manuscript_metrics_dict` | All `${variable}` values from live repo + archive exemplars |
| `build_module_inventory_table` | Markdown table for chapter 06 |
| `save_metrics_json` | Write `output/data/metrics.json` |

Key tokens: `${module_count}`, `${pipeline_stages_declared}`, `${pipeline_stages_default_full}`, `${pipeline_stages_core_only}`, `${public_exemplar_list}`, `${stage_count}` (numbered scripts only).

### Injection (`src/template/inject_metrics.py`)

| Function | Description |
|----------|-------------|
| `load_metrics` | Flatten `metrics.json` for substitution |
| `render_chapter` / `render_all_chapters` | Write `output/manuscript/` |

### Visualization (`src/template/architecture_viz.py`)

| Output | Description |
|--------|-------------|
| `architecture_overview.png` | Two-layer overview, dynamic module grid |
| `pipeline_stages.png` | YAML DAG with tag colouring |
| `module_inventory.png` | Per-module Python file counts |
| `comparative_feature_matrix.png` | Tool capability heatmap |

## Verification

From the public template repo root:

```bash
cd /path/to/template
uv run pytest projects_in_progress/template/tests/ \
  --cov=projects_in_progress/template/src/template --cov-fail-under=90 -v
uv run python projects_in_progress/template/scripts/generate_manuscript_metrics.py
uv run python projects_in_progress/template/scripts/generate_architecture_viz.py
```

## Patterns

- **Thin orchestrator:** scripts delegate to `src/template/`
- **Zero-mock testing:** real filesystem, real YAML, real imports
- **Measured prose:** inject counts via `${...}`; do not hard-code rotating facts
