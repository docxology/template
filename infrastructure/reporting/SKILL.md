---
name: infrastructure-reporting
description: Skill for the reporting infrastructure module providing pipeline reporting, error aggregation, executive summaries, dashboard generation, test reporting, and multi-project reports. Use when generating build reports, aggregating errors, creating visual dashboards, or producing executive summaries across projects.
---

# Reporting Module

Pipeline reporting, error aggregation, and executive dashboard generation.

Public API is defined in [`__init__.py`](__init__.py). Prefer submodule imports when using only one subsystem (see docstring there).

## Pipeline reports (`pipeline_report_model.py`, `pipeline_io.py`)

```python
from pathlib import Path
from infrastructure.reporting import (
    generate_pipeline_report,
    save_pipeline_report,
    save_test_results,
    save_validation_report,
    save_performance_report,
    save_error_summary,
)

report = generate_pipeline_report(
    stage_results=[{"name": "setup", "exit_code": 0, "duration": 1.0}],
    total_duration=1.0,
    repo_root=Path("."),
    test_results={"summary": {"total_tests": 10, "total_passed": 10}},
)
saved = save_pipeline_report(report, Path("output/reports"))

save_test_results(test_results_dict, Path("output/reports"))
save_validation_report(validation_results_dict, Path("output/reports"))
save_performance_report(performance_metrics_dict, Path("output/reports"))
save_error_summary([{"type": "stage_failure", "message": "..."}], Path("output/reports"))
```

Markdown/HTML for the pipeline report are assembled inside `save_pipeline_report` via `pipeline_markdown.py` and `pipeline_html.py`.

## Error aggregation (`error_aggregator.py`)

```python
from infrastructure.reporting import (
    ErrorAggregator,
    get_error_aggregator,
    reset_error_aggregator,
)

aggregator = get_error_aggregator()
aggregator.add_error(
    error_type="validation_error",
    message="Broken link",
    stage="validation",
    suggestions=["Check markdown refs"],
)
summary = aggregator.get_summary()
aggregator.save_report(Path("output/reports"))
reset_error_aggregator()
```

## Executive summaries (`executive_reporter.py`)

```python
from pathlib import Path
from infrastructure.reporting import (
    generate_executive_summary,
    save_executive_summary,
    collect_project_metrics,
    ProjectMetrics,
    ExecutiveSummary,
)

summary = generate_executive_summary(Path("."), ["code_project"])
paths = save_executive_summary(summary, Path("output/executive_summary"))
metrics = collect_project_metrics(Path("."), "code_project")
```

## Dashboard generation (`_dashboard_matplotlib.py` and `_dashboard_*.py`)

```python
from infrastructure.reporting import (
    generate_all_dashboards,
    generate_matplotlib_dashboard,
    generate_plotly_dashboard,
)

# Optional: requires matplotlib (and plotly for HTML); see DASHBOARD_AVAILABLE
files = generate_all_dashboards(summary, Path("output/executive_summary"))
```

## Test suite summaries (`report_builder.py`, `markdown_formatter.py`, `result_loaders.py`)

```python
from infrastructure.reporting import (
    generate_summary_report,
    generate_markdown_report,
    load_test_results,
    load_infrastructure_results,
    run_test_summary_generation,
)

# generate_markdown_report(data) expects a test-suite summary dict, not PipelineReport
```

## Output statistics (`output_statistics.py`)

```python
from pathlib import Path
from infrastructure.reporting import collect_output_statistics, log_output_summary

stats = collect_output_statistics(Path("output/code_project"))
log_output_summary(Path("output/code_project"), stats)
```

## Multi-project reports (`multi_project_reporter.py`)

```python
from pathlib import Path
from infrastructure.reporting import (
    generate_multi_project_report,
    generate_multi_project_summary_report,
)

files = generate_multi_project_report(
    Path("."),
    ["code_project", "template"],
    Path("output/executive_summary"),
)
```

## Manuscript overview (`manuscript_overview.py`)

```python
from pathlib import Path
from infrastructure.reporting.manuscript_overview import (
    generate_manuscript_overview,
    generate_all_manuscript_overviews,
)

generate_manuscript_overview(
    pdf_path=Path("output/code_project/pdf/code_project_combined.pdf"),
    output_dir=Path("output/executive_summary"),
    project_name="code_project",
)
# Used by dashboard generation:
generate_all_manuscript_overviews(summary, output_dir, Path("."))
```

## Coverage helpers (`coverage_parser.py`, `coverage_reporter.py`, …)

Import from the specific module when needed, for example:

```python
from infrastructure.reporting.coverage_parser import parse_coverage_report
```
