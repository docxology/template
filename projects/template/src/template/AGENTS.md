# AGENTS: `src/template/` — Template Core Modules

Technical specification for the template project's source code package.

## Module Inventory

| File | Purpose | Key Exports |
|------|---------|-------------|
| `__init__.py` | Public API surface | Introspection, metrics, injection, and visualization entrypoints (32 symbols) |
| `introspection.py` | Repository analysis | `discover_infrastructure_modules`, `discover_projects`, `count_pipeline_stages`, `analyze_test_coverage_config`, `build_infrastructure_report` |
| `metrics.py` | Manuscript metrics computation | `build_manuscript_metrics_dict`, `save_metrics_json`, `build_module_inventory_table`, counters, formatting helpers |
| `inject_metrics.py` | Chapter variable injection | `load_metrics`, `render_chapter`, `render_all_chapters` |
| `architecture_viz.py` | Figure generation | `generate_all_architecture_figures`, per-figure generators, `comparative_feature_matrix_data` |

## Data Classes

- **`ModuleInfo`** — name, path, Python file count, documentation status (`has_agents_md`, `has_readme_md`, `has_skill_md`, `has_pai_md`), public symbols
- **`ProjectInfo`** — name, chapter count, test/script counts, parsed config
- **`PipelineStage`** — stage number, human-readable name, script path (used by both introspection and visualization modules)
- **`CoverageConfig`** — failure tolerances from `config.yaml`
- **`InfrastructureReport`** — aggregated report with computed properties (`module_count`, `project_count`, `stage_count`)

## Patterns

- All functions accept `Path` arguments and return plain dataclasses
- Uses `infrastructure.core.logging_utils.get_logger` for structured logging
- Config parsing via `yaml.safe_load` with graceful error handling
- Module introspection uses `importlib.import_module` with `try/except` fallback
- Script-facing logic is imported by thin orchestrators in `projects/template/scripts/`
- Four-layer doc badges (`has_skill_md`, `has_pai_md`) extend standard A+R coverage
