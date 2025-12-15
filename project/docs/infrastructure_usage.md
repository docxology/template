# Infrastructure Usage Guide

This project leverages the template's infrastructure layer (core, validation, documentation, build, scientific, literature, llm, rendering, publishing, reporting) for reproducible pipelines.

## Common Patterns

- **Logging**: `from infrastructure.core.logging_utils import get_logger`; use `log_substep` and `log_progress_bar` for stage progress.
- **Performance**: `from infrastructure.core.performance import PerformanceMonitor` to measure stage duration and memory.
- **Validation**: `from infrastructure.validation import validate_markdown, validate_figure_registry, verify_output_integrity` for preflight checks.
- **Reporting**: `from infrastructure.reporting import generate_pipeline_report, save_pipeline_report, get_error_aggregator` for structured outputs.
- **Figures**: `from infrastructure.documentation import FigureManager` to register figures and maintain `figure_registry.json`.

## Examples

```python
from infrastructure.core.performance import PerformanceMonitor
from infrastructure.reporting import generate_pipeline_report, save_pipeline_report

perf = PerformanceMonitor()
perf.start()
run_stage()
perf.update_memory()
metrics = perf.stop()

report = generate_pipeline_report(
    stage_results=[{"name": "stage", "exit_code": 0, "duration": metrics.duration}],
    total_duration=metrics.duration,
    repo_root=Path("."),
)
save_pipeline_report(report, Path("output/reports"))
```

```python
from infrastructure.validation import validate_markdown, validate_figure_registry

issues, _ = validate_markdown("project/manuscript", ".")
validate_figure_registry(Path("output/figures/figure_registry.json"))
```

## CLI Shortcuts

- `python3 project/scripts/manuscript_preflight.py --strict` – figures, glossary markers, references.
- `python3 project/scripts/quality_report.py` – readability, integrity, reproducibility snapshot.
- `python3 -m infrastructure.validation.cli markdown project/manuscript/ --strict`
- `python3 -m infrastructure.validation.cli pdf project/output/pdf/`

## Best Practices

- Register every generated figure with `FigureManager`.
- Save reports to `project/output/reports/` and include validation summaries.
- Keep stages resumable via `--only/--resume/--dry-run` flags in scripts.
- Treat output checks (`verify_output_integrity`) as gating steps before rendering.











