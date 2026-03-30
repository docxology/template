# Template Source — Introspection & Metrics Utilities

Repository-aware analysis functions that programmatically examine the Docxology Template's own structure, compute manuscript metrics, and generate publication-quality figures.

## Quick Start

```python
from template import build_infrastructure_report
from pathlib import Path

report = build_infrastructure_report(Path("/path/to/repo"))
print(f"{report.module_count} modules, {report.project_count} projects")
```

## API — Introspection

| Function | Returns | Description |
|----------|---------|-------------|
| `discover_infrastructure_modules(root)` | `list[ModuleInfo]` | Scan `infrastructure/` subpackages |
| `discover_projects(root)` | `list[ProjectInfo]` | Find valid project workspaces |
| `count_pipeline_stages(scripts_dir)` | `list[PipelineStage]` | Enumerate `NN_name.py` scripts |
| `analyze_test_coverage_config(project_dir)` | `CoverageConfig \| None` | Parse testing thresholds |
| `build_infrastructure_report(root)` | `InfrastructureReport` | Aggregate all above |

## API — Metrics

| Function | Returns | Description |
|----------|---------|-------------|
| `build_manuscript_metrics_dict(root)` | `dict` | ~40 live manuscript variables |
| `save_metrics_json(metrics, path)` | `Path` | Serialise metrics to JSON |
| `build_module_inventory_table(modules)` | `str` | Render module inventory as Markdown |

## API — Injection

| Function | Returns | Description |
|----------|---------|-------------|
| `load_metrics(path)` | `dict` | Deserialise flat metrics dict |
| `render_chapter(source, metrics, out)` | `Path` | Substitute `${vars}` in one chapter |
| `render_all_chapters(dir, metrics, out)` | `list[Path]` | Process all chapters + ancillary files |

## API — Visualization

| Function | Returns | Description |
|----------|---------|-------------|
| `generate_all_architecture_figures(root, dir)` | `list[Path]` | Generate all 4 figures |
| `comparative_feature_matrix_data()` | `tuple` | 14×10 data matrix + labels |
