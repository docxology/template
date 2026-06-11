# Reporting Module - Quick Reference

Pipeline reporting and error aggregation utilities.

## Overview

The reporting module provides reporting capabilities for pipeline execution, including:

- Consolidated pipeline reports (JSON, HTML, Markdown)
- Test results reporting
- Validation reports with actionable recommendations
- Performance metrics and analysis
- Error aggregation and categorization
- **Executive cross-project summaries and visual dashboards**
- **Unified output organization system**
- **Interactive simulation dashboards** (`interactive_dashboard.py`) — project-agnostic builder for self-contained Plotly dashboards with multi-view linked panels, live controls, and plaintext invariants. See [`AGENTS.md`](AGENTS.md#interactive-simulation-dashboard-interactive_dashboardpy).

## Architecture

```mermaid
graph TD
    subgraph InputSources["Input Sources"]
        PIPELINE[Pipeline Execution<br/>Stage results, durations]
        TESTS[Test Results<br/>Coverage, pass/fail]
        VALIDATION[Validation Results<br/>PDF, markdown checks]
        ERRORS[Error Events<br/>Failures, warnings]
        PROJECTS[Project Metrics<br/>Multi-project data]
    end

    subgraph ReportingModules["Reporting Modules"]
        PIPELINE_REP[report_generator.py<br/>Pipeline report generation]
        ERROR_AGG[error_aggregator.py<br/>Error collection & categorization]
        EXEC_REP[executive_reporter.py<br/>Cross-project summaries]
        DASHBOARD[_dashboard_matplotlib.py<br/>Visual dashboards]
        OUTPUT_ORG[output_organizer.py<br/>File organization]
    end

    subgraph OutputFormats["Output Formats"]
        JSON[JSON Reports<br/>Machine-readable]
        HTML[HTML Reports<br/>Styled visual format]
        MARKDOWN[Markdown Reports<br/>Human-readable]
        PNG[PNG Dashboards<br/>Static charts]
        PDF[PDF Dashboards<br/>Vector graphics]
        CSV[CSV Data Tables<br/>Metrics export]
    end

    PIPELINE --> PIPELINE_REP
    TESTS --> PIPELINE_REP
    VALIDATION --> PIPELINE_REP
    ERRORS --> ERROR_AGG
    PROJECTS --> EXEC_REP

    PIPELINE_REP --> JSON
    PIPELINE_REP --> HTML
    PIPELINE_REP --> MARKDOWN

    ERROR_AGG --> JSON
    ERROR_AGG --> HTML

    EXEC_REP --> JSON
    EXEC_REP --> HTML
    EXEC_REP --> MARKDOWN

    EXEC_REP --> DASHBOARD
    DASHBOARD --> PNG
    DASHBOARD --> PDF
    DASHBOARD --> HTML
    DASHBOARD --> CSV

    OUTPUT_ORG --> JSON
    OUTPUT_ORG --> HTML
    OUTPUT_ORG --> PNG
    OUTPUT_ORG --> PDF
    OUTPUT_ORG --> CSV

    class InputSources input
    class ReportingModules module
    class OutputFormats output
```

## Output Organization

The reporting module includes a unified output organization system that ensures consistent file placement across all reporting operations.

### File Organization

```python
from infrastructure.reporting.output_organizer import OutputOrganizer, FileType

organizer = OutputOrganizer()

# Get organized path for any file type
png_path = organizer.get_output_path("chart.png", output_dir, FileType.PNG)
# Result: output_dir/png/chart.png

csv_path = organizer.get_output_path("data.csv", output_dir, FileType.CSV)
# Result: output_dir/csv/data.csv
```

### Directory Structure

All executive reports are organized by file type:

```mermaid
flowchart LR
    EX[/output/executive_summary//]
    EX --> PNG[/png<br/>visualisations/]
    EX --> PDF[/pdf<br/>charts &amp; reports/]
    EX --> CSV[/csv<br/>data exports/]
    EX --> HTML[/html<br/>interactive dashboards/]
    EX --> JSON[/json<br/>machine-readable reports/]
    EX --> MD[/md<br/>human-readable reports/]
    EX --> CB[/combined_pdfs<br/>all project manuscripts/]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    class EX,PNG,PDF,CSV,HTML,JSON,MD,CB d
```

### Reorganization

Reorganize existing outputs with the provided script:

```bash
# Preview changes
uv run python scripts/maintenance/organize_executive_outputs.py --dry-run

# Apply organization
uv run python scripts/maintenance/organize_executive_outputs.py
```

## Quick Start

### Generate Pipeline Report

```python
from infrastructure.reporting import generate_pipeline_report, save_pipeline_report
from pathlib import Path

# Collect stage results
stage_results = [
    {'name': 'setup', 'exit_code': 0, 'duration': 2.5},
    {'name': 'tests', 'exit_code': 0, 'duration': 45.2},
]

# Generate report
report = generate_pipeline_report(
    stage_results=stage_results,
    total_duration=47.7,
    repo_root=Path("."),
    test_results={'summary': {'total_tests': 878, 'total_passed': 878}},
)

# Save in multiple formats
saved_files = save_pipeline_report(report, Path("output/reports"))
# Returns: {'json': Path(...), 'html': Path(...), 'markdown': Path(...)}
```

### Aggregate Errors

```python
from infrastructure.reporting import get_error_aggregator

aggregator = get_error_aggregator()

# Add errors during pipeline execution
aggregator.add_error(
    error_type='test_failure',
    message='Test test_example failed',
    stage='tests',
    suggestions=['Review test output', 'Check test data'],
)

# Generate error summary
summary = aggregator.get_summary()
aggregator.save_report(Path("output/reports"))
```

### Generate Executive Report

```python
from infrastructure.reporting import generate_executive_summary, save_executive_summary
from pathlib import Path

repo_root = Path(".")
project_names = ["template_code_project"]

# Generate cross-project summary
summary = generate_executive_summary(repo_root, project_names)

print(f"Total projects: {summary.total_projects}")
print(f"Total manuscript words: {summary.aggregate_metrics['manuscript']['total_words']:,}")
print(f"Average test coverage: {summary.aggregate_metrics['tests']['average_coverage']:.1f}%")

# Save reports
saved_files = save_executive_summary(summary, Path("output/executive_summary"))
# Returns: {'json': Path(...), 'html': Path(...), 'markdown': Path(...)}
```

### Generate Visual Dashboard

```python
from infrastructure.reporting import generate_all_dashboards

# Create visual dashboards (PNG, PDF, HTML) + CSV data exports
dashboard_files = generate_all_dashboards(summary, Path("output/executive_summary"))
# Returns: {'png': Path(...), 'pdf': Path(...), 'html': Path(...), 'metrics': Path(...), ...}

print(f"Generated {len(dashboard_files)} dashboard and data files")
```

### Multi-Project Reporting

```python
from infrastructure.reporting import generate_multi_project_report

# One-line executive reporting workflow
files = generate_multi_project_report(
    Path("."), ["project1", "project2"], Path("output/executive_summary")
)
# Automatically generates:
# - Executive summary (JSON, HTML, Markdown)
# - Visual dashboards (PNG, PDF, HTML)
# - CSV data tables (metrics, aggregates, health scores)

print(f"Generated {len(files)} report files")
for fmt, path in files.items():
    print(f"  {fmt}: {path.name}")
```

### Generate Validation Report

```python
from infrastructure.reporting import save_validation_report

validation_results = {
    'checks': {
        'pdf_validation': True,
        'markdown_validation': True,
        'output_structure': False,
    },
    'recommendations': [
        {'priority': 'high', 'issue': 'Missing output directories', 'action': '...'},
    ],
}

saved_files = save_validation_report(validation_results, Path("output/reports"))
```

## Module Functions

### Pipeline Reporting

- `generate_pipeline_report()` - Create consolidated pipeline report
- `save_pipeline_report()` - Save report in multiple formats (JSON, HTML, Markdown)
- `generate_test_report()` - Generate test results report
- `save_validation_report()` - Save validation report
- `save_performance_report()` - Save performance metrics report
- `save_error_summary()` - Save error summary report

### Executive Reporting

- `generate_executive_summary()` - Generate cross-project metrics and summary
- `save_executive_summary()` - Save executive summary in multiple formats
- `collect_project_metrics()` - Collect all metrics for a single project
- `calculate_project_health_score()` - Calculate project health score
- `ProjectMetrics` - project metrics dataclass
- `ExecutiveSummary` - Executive summary dataclass with health scores

### Multi-Project Orchestration

- `generate_multi_project_report()` - executive reporting workflow
- `generate_csv_data_tables()` - Export metrics as CSV tables

### Dashboard Generation

- `generate_all_dashboards()` - Generate dashboards in all formats (PNG, PDF, HTML)
- `generate_matplotlib_dashboard()` - Generate static charts (PNG/PDF)
- `generate_plotly_dashboard()` - Generate interactive HTML dashboard

### Error Aggregation

- `ErrorAggregator` - Main error aggregation class
- `get_error_aggregator()` - Get global error aggregator instance
- `ErrorEntry` - Single error/warning entry dataclass

### Coverage Trend Dashboard (`coverage_history.py`)

Generates a static `docs/_generated/coverage_history.md` with a 30-day rolling
table and ASCII sparklines per suite. Imported from a thin orchestrator at
`scripts/generate_coverage_history.py`.

- `CoveragePoint` — frozen dataclass: `(date, suite, percentage, lines_covered, lines_total)`
- `parse_coverage_xml(path) -> CoveragePoint` — Cobertura XML → point (uses `defusedxml`)
- `collect_history_from_dir(directory) -> list[CoveragePoint]` — recursive offline parse
- `collect_history_via_gh(workflow="ci.yml", *, days=30, repo_root=None) -> list[CoveragePoint]` —
  real `gh run list` + `gh run download` (raises `RuntimeError` if `gh` is missing)
- `build_history_markdown(points, *, days=30, today=None) -> str` — pure, deterministic Markdown

## Report Formats

All reports are generated in multiple formats:

- **JSON**: Machine-readable format for programmatic access
- **HTML**: Visual format with styling for browser viewing
- **Markdown**: Human-readable format for documentation

## Integration

The reporting module is automatically integrated into:

- `scripts/execute_pipeline.py` - Generates pipeline report at end
- `scripts/01_run_tests.py` - Generates test reports
- `scripts/04_validate_output.py` - Generates validation reports

Reports are saved to `project/output/reports/` by default.

## Features (v2.1)

### Executive Reporting

- **Project Health Scoring**: Automated assessment based on test coverage, manuscript quality, test reliability, and output completeness
- **Statistical Aggregates**: Min/max/median calculations for cross-project comparisons
- **Actionable Recommendations**: Intelligent suggestions based on metrics analysis and best practices
- **Dashboards**: 9 charts including complexity analysis, performance metrics, and health scores

### Multi-Project Integration

- **Automatic Executive Reporting**: Triggered automatically in `run.sh` multi-project options (a, b, c, d)
- **CSV Data Export**: Machine-readable data tables for further analysis
- **Workflow Orchestration**: `generate_multi_project_report()` handles the entire reporting pipeline

### Manuscript Overview Generation

**Visual manuscript previews** for executive reporting. Automatically extracts all pages from each project's manuscript PDF and arranges them as thumbnails in a 4-column grid layout.

```python
from infrastructure.reporting.manuscript_overview import generate_all_manuscript_overviews

# Generate manuscript overviews for all projects
overview_files = generate_all_manuscript_overviews(summary, output_dir, repo_root)
# Creates: manuscript_overview_{project_name}.png/pdf for each project
```

**Features:**

- **Page Thumbnails**: High-quality page previews with page numbers
- **Grid Layout**: 4-column arrangement with automatic row calculation
- **Dual Output**: Both PNG (raster) and PDF (vector) formats
- **Error Resilience**: Gracefully handles missing PDFs or rendering failures

### Output Structure

Executive reports are saved to `output/executive_summary/`:

```mermaid
flowchart TB
    EX[/output/executive_summary//]
    EX --> CR[consolidated_report<br/>.json · .html · .md]
    EX --> DB[dashboard<br/>.png · .pdf · .html<br/>9-chart dashboard]
    EX --> MO[manuscript_overview_&lt;project&gt;<br/>.png · .pdf<br/>page grid]
    EX --> PM[project_metrics.csv<br/>detailed project data]
    EX --> AM[aggregate_metrics.csv<br/>cross-project statistics]
    EX --> HS[health_scores.csv<br/>health-score breakdowns]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef f fill:#0f766e,stroke:#0f172a,color:#fff
    class EX d
    class CR,DB,MO,PM,AM,HS f
```

## See Also

- [`AGENTS.md`](AGENTS.md) - reporting module documentation
- [`../README.md`](../README.md) - Infrastructure layer overview
- [`../AGENTS.md`](../AGENTS.md) - infrastructure documentation
