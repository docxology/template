---
name: infrastructure-reporting
description: Skill for the reporting infrastructure module providing pipeline reporting, error aggregation, executive summaries, dashboard generation, test reporting, and multi-project reports. Use when generating build reports, aggregating errors, creating visual dashboards, or producing executive summaries across projects.
---

# Reporting Module

Pipeline reporting, error aggregation, and executive dashboard generation.

## Pipeline Reports (`pipeline_report_model.py`, `pipeline_io.py`)

```python
from infrastructure.reporting import (
    generate_pipeline_report, save_pipeline_report,
    save_validation_report, save_test_results,
    save_performance_report, save_error_summary,
)
from infrastructure.reporting.report_generator import generate_test_report

# Generate comprehensive pipeline report
report = generate_pipeline_report(
    stage_results=stage_results,
    total_duration=total_duration,
    repo_root=Path("."),
    test_results=test_data,
    validation_results=validation_data,
    performance_metrics=perf_data,
    error_summary=error_summary,
)

# Save report to file
save_pipeline_report(report, output_dir)

# Individual report sections
test_report = generate_test_report(test_data)
saved_files = save_validation_report(validation_data, output_dir)
```

## Error Aggregation (`error_aggregator.py`)

```python
from infrastructure.reporting import (
    ErrorAggregator, ErrorEntry,
    get_error_aggregator, reset_error_aggregator,
)

# Singleton aggregator
aggregator = get_error_aggregator()
aggregator.add_error(error_type="rendering", message="Missing figure", stage="rendering")
aggregator.add_error(error_type="validation", message="Broken link", stage="validation")

# Construct ErrorEntry directly (type and message are required)
entry = ErrorEntry(type="rendering", message="Missing figure", stage="rendering")

# Get summary and save report
summary = aggregator.get_summary()
saved = aggregator.save_report(output_dir)
reset_error_aggregator()
```

## Executive Summaries (`executive_reporter.py`)

```python
from infrastructure.reporting import (
    generate_executive_summary, save_executive_summary,
    collect_project_metrics, ProjectMetrics, ExecutiveSummary,
)

# Generate cross-project executive summary
summary = generate_executive_summary(repo_root, project_names)
files = save_executive_summary(summary, output_dir)

# Collect metrics for a single project
metrics = collect_project_metrics(repo_root, project_name)
```

## Dashboard Generation (`_dashboard_matplotlib.py`)

```python
from infrastructure.reporting import (
    generate_all_dashboards,
    generate_matplotlib_dashboard,
    generate_plotly_dashboard,
)

# Generate all dashboard formats (PNG, PDF, HTML)
files = generate_all_dashboards(executive_summary, output_dir)

# Individual dashboard types
generate_matplotlib_dashboard(summary, output_dir)
generate_plotly_dashboard(summary, output_dir)
```

## Test Reporting (`pytest_output_parser.py`, `report_generator.py`)

```python
from infrastructure.reporting.pytest_output_parser import parse_pytest_output
from infrastructure.reporting.report_generator import save_test_report_to_files

# Parse pytest output into structured data (stdout, stderr, exit_code all required)
results = parse_pytest_output(stdout_text, stderr_text, exit_code)
save_test_report_to_files(results, output_path)
```

## Output Reporting (`output_statistics.py`)

```python
from infrastructure.reporting import (
    collect_output_statistics,
    log_output_summary,
    write_output_statistics_reports,
)

stats = collect_output_statistics(output_dir)
log_output_summary(stats)
write_output_statistics_reports(output_dir, stats)
```

## Multi-Project Reports

```python
from infrastructure.reporting import generate_multi_project_report

# Full workflow: executive summary + dashboards + CSV exports
files = generate_multi_project_report(
    repo_root=Path("."),
    project_names=["project_a", "project_b"],
    output_dir=Path("output/executive_summary"),
)
```

## Test Summary Generation (`markdown_formatter.py`)

```python
from infrastructure.reporting.markdown_formatter import run_test_summary_generation
run_test_summary_generation()
```

## Manuscript Overview (`manuscript_overview.py`)

```python
from infrastructure.reporting.manuscript_overview import generate_manuscript_overview
overview = generate_manuscript_overview(pdf_path, output_dir, project_name)
```

## Coverage Parsing (`coverage_parser.py`)

```python
from infrastructure.reporting.coverage_parser import extract_coverage_percentage
passed, pct = extract_coverage_percentage(stdout_text, coverage_json_paths)
```
