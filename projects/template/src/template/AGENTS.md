# AGENTS: `src/template/` — Introspection Utilities

Technical specification for the template project's source code package.

## Module Inventory

| File | Purpose | Key Exports |
|------|---------|-------------|
| `__init__.py` | Public API surface | 5 functions, 5 dataclasses |
| `introspection.py` | Repository analysis | `discover_infrastructure_modules`, `discover_projects`, `count_pipeline_stages`, `analyze_test_coverage_config`, `build_infrastructure_report` |

## Data Classes

- **`ModuleInfo`** — name, path, Python file count, documentation status, public symbols
- **`ProjectInfo`** — name, chapter count, test/script counts, parsed config
- **`PipelineStage`** — stage number, human-readable name, script path
- **`CoverageConfig`** — failure tolerances from `config.yaml`
- **`InfrastructureReport`** — aggregated report with computed properties (`module_count`, `project_count`, `stage_count`)

## Patterns

- All functions accept `Path` arguments and return plain dataclasses
- Uses `infrastructure.core.logging_utils.get_logger` for structured logging
- Config parsing via `yaml.safe_load` with graceful error handling
- Module introspection uses `importlib.import_module` with `try/except` fallback
