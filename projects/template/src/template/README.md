# Template Source — Introspection Utilities

Repository-aware analysis functions that programmatically examine the Docxology Template's own structure.

## Quick Start

```python
from template import build_infrastructure_report
from pathlib import Path

report = build_infrastructure_report(Path("/path/to/repo"))
print(f"{report.module_count} modules, {report.project_count} projects")
```

## API

| Function | Returns | Description |
|----------|---------|-------------|
| `discover_infrastructure_modules(root)` | `list[ModuleInfo]` | Scan `infrastructure/` subpackages |
| `discover_projects(root)` | `list[ProjectInfo]` | Find valid project workspaces |
| `count_pipeline_stages(scripts_dir)` | `list[PipelineStage]` | Enumerate `NN_name.py` scripts |
| `analyze_test_coverage_config(project_dir)` | `CoverageConfig \| None` | Parse testing thresholds |
| `build_infrastructure_report(root)` | `InfrastructureReport` | Aggregate all above |
