# AGENTS: `src/template/` — Template Core Modules

Technical specification for the template project's source code package.

## Module Inventory

| File | Purpose | Key Exports |
|------|---------|-------------|
| `__init__.py` | Public API surface | Introspection, metrics, injection, and visualization entrypoints (32 symbols) |
| `introspection.py` | Repository analysis | `discover_infrastructure_modules`, `discover_projects`, `count_pipeline_stages`, `analyze_test_coverage_config`, `build_infrastructure_report` |
| `metrics.py` | Manuscript metrics computation | `build_manuscript_metrics_dict`, `save_metrics_json`, `build_module_inventory_table`, counters, formatting helpers |
| `inject_metrics.py` | Chapter variable injection | `load_metrics`, `render_chapter`, `render_all_chapters` |
| `architecture_viz.py` | Figure orchestration | `generate_all_architecture_figures`; re-exports per-figure generators |
| `viz_palette.py` | Shared colours and label helpers | `ARCH_VIZ_COLORS`, `FONT_FLOOR`, `stage_color`, `short_stage_label`, `doc_badge` |
| `figure_architecture_overview.py` | Two-layer overview PNG | `generate_architecture_overview` |
| `figure_pipeline_stages.py` | Pipeline DAG PNG | `generate_pipeline_stages` |
| `figure_module_inventory.py` | Module inventory bar chart | `generate_module_inventory` |
| `figure_comparative_matrix.py` | Comparative matrix data + PNG | `comparative_feature_matrix_data`, `generate_comparative_feature_matrix` |
| `paths.py` | Repo-root discovery for thin scripts | `locate_repo_root` |

## Data Classes

- **`ModuleInfo`** — name, path, Python file count, documentation status (`has_agents_md`, `has_readme_md`, `has_skill_md`, `has_pai_md`), public symbols
- **`ProjectInfo`** — name, chapter count, test/script counts, parsed config
- **`PipelineStage`** — stage number, human-readable name, script path (used by both introspection and visualization modules)
- **`CoverageConfig`** — failure tolerances from `config.yaml`
- **`InfrastructureReport`** — aggregated report with computed properties (`module_count`, `project_count`, `stage_count`)

## Patterns

- All functions accept `Path` arguments and return plain dataclasses
- Uses `infrastructure.core.logging.utils.get_logger` for structured logging
- Config parsing via `yaml.safe_load` with graceful error handling; catches
  `(OSError, ValueError, yaml.YAMLError)` — the `yaml.YAMLError` catch was
  added 2026-06-25 to handle malformed YAML that pyyaml raises as
  `yaml.parser.ParserError` (a subclass of `yaml.YAMLError`, not `ValueError`)
- Module introspection uses `importlib.import_module` with `try/except` fallback
- Script-facing logic is imported by thin orchestrators in `projects/templates/template_template/scripts/`
- Four-layer doc badges (`has_skill_md`, `has_pai_md`) extend standard A+R coverage
