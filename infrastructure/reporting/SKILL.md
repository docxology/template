---
name: infrastructure-reporting
description: Skill for the reporting infrastructure module providing pipeline reporting, error aggregation, executive summaries, dashboard generation, test reporting, and multi-project reports. Use when generating build reports, aggregating errors, creating visual dashboards, or producing executive summaries across projects.
---

# Reporting Module

Pipeline reporting, error aggregation, and executive dashboard generation.

## Pipeline Reports (`pipeline_reporter.py`)

```python
from infrastructure.reporting import (
    generate_pipeline_report, generate_test_report,
    generate_validation_report, generate_performance_report,
    generate_error_summary, save_pipeline_report,
)

# Generate comprehensive pipeline report
report = generate_pipeline_report(
    test_results=test_data,
    validation_results=validation_data,
    performance_metrics=perf_data,
    errors=error_list,
)

# Save report to file
save_pipeline_report(report, output_dir)

# Individual report sections
test_report = generate_test_report(test_data)
validation_report = generate_validation_report(validation_data)
performance_report = generate_performance_report(perf_data)
error_summary = generate_error_summary(error_list)
```

## Error Aggregation (`error_aggregator.py`)

```python
from infrastructure.reporting import (
    ErrorAggregator, ErrorEntry,
    get_error_aggregator, reset_error_aggregator,
)

# Singleton aggregator
aggregator = get_error_aggregator()
aggregator.add(ErrorEntry(stage="rendering", message="Missing figure"))
aggregator.add(ErrorEntry(stage="validation", message="Broken link"))

# Get summary
summary = aggregator.summarize()
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
metrics = collect_project_metrics(project_path)
```

## Dashboard Generation (`dashboard_generator.py`)

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

## Test Reporting (`test_reporter.py`)

```python
from infrastructure.reporting import parse_pytest_output, save_test_report

# Parse pytest output into structured data
results = parse_pytest_output(pytest_output_text)
save_test_report(results, output_path)
```

## Output Reporting (`output_reporter.py`)

```python
from infrastructure.reporting import collect_output_statistics, generate_output_summary

stats = collect_output_statistics(output_dir)
summary = generate_output_summary(stats)
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

## Test Summary Generation (`test_summary_generator.py`)

```python
from infrastructure.reporting.test_summary_generator import generate_test_summary
summary = generate_test_summary(test_results)
```

## Manuscript Overview (`manuscript_overview.py`)

```python
from infrastructure.reporting.manuscript_overview import generate_manuscript_overview
overview = generate_manuscript_overview(project_path)
```

## Coverage Parsing (`coverage_parser.py`)

```python
from infrastructure.reporting.coverage_parser import parse_coverage_report
coverage = parse_coverage_report(coverage_output)
```
