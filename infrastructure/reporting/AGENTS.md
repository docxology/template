# Reporting Module - Complete Documentation

## Overview

The reporting module provides comprehensive reporting capabilities for pipeline execution, test results, validation outcomes, performance metrics, and error aggregation. It generates structured reports in multiple formats (JSON, HTML, Markdown) for both human review and machine processing.

## Architecture

### Module Structure

```
infrastructure/reporting/
├── __init__.py              # Public API exports
├── pipeline_reporter.py     # Pipeline report generation
├── error_aggregator.py      # Error collection and categorization
├── html_templates.py        # HTML report templates
├── README.md                # Quick reference
└── AGENTS.md                # This file
```

### Design Principles

1. **Multi-Format Output**: All reports generated in JSON, HTML, and Markdown
2. **Structured Data**: Machine-readable formats for programmatic access
3. **Actionable Insights**: Reports include recommendations and fixes
4. **Integration**: Seamlessly integrated into pipeline stages
5. **Error Categorization**: Intelligent error grouping and prioritization

## Core Components

### Pipeline Reporter (`pipeline_reporter.py`)

Generates consolidated reports from pipeline execution data.

#### Key Functions

**`generate_pipeline_report()`**
- Creates a `PipelineReport` dataclass from stage results
- Includes test results, validation results, performance metrics
- Supports error summaries and output statistics

**`save_pipeline_report()`**
- Saves reports in multiple formats (JSON, HTML, Markdown)
- Returns dictionary mapping format to file path
- Creates output directory if needed

**`generate_markdown_report()`**
- Generates human-readable Markdown report
- Includes summary statistics, stage details, recommendations

**`generate_html_report()`**
- Generates styled HTML report
- Includes visual indicators (status badges, summary cards)
- Responsive design for browser viewing

#### Usage Example

```python
from infrastructure.reporting import generate_pipeline_report, save_pipeline_report
from pathlib import Path

# Collect stage results
stage_results = [
    {'name': 'setup', 'exit_code': 0, 'duration': 2.5},
    {'name': 'tests', 'exit_code': 0, 'duration': 45.2},
    {'name': 'analysis', 'exit_code': 0, 'duration': 12.8},
]

# Generate report
report = generate_pipeline_report(
    stage_results=stage_results,
    total_duration=60.5,
    repo_root=Path("."),
    test_results={'summary': {'total_tests': 878, 'total_passed': 878}},
    validation_results={'checks': {'pdf_validation': True}},
    performance_metrics={'total_duration': 60.5},
)

# Save reports
saved_files = save_pipeline_report(report, Path("output/reports"))
# Returns: {'json': Path(...), 'html': Path(...), 'markdown': Path(...)}
```

### Error Aggregator (`error_aggregator.py`)

Collects, categorizes, and provides actionable fixes for errors and warnings.

#### Key Classes

**`ErrorAggregator`**
- Main class for error collection
- Categorizes errors by type
- Generates actionable fixes with priority levels
- Saves reports in JSON and Markdown formats

**`ErrorEntry`**
- Dataclass representing a single error or warning
- Includes type, message, stage, file, line, severity
- Supports suggestions and context

#### Usage Example

```python
from infrastructure.reporting import get_error_aggregator
from pathlib import Path

aggregator = get_error_aggregator()

# Add errors during pipeline execution
aggregator.add_error(
    error_type='test_failure',
    message='Test test_example failed with assertion error',
    stage='tests',
    file='tests/test_example.py',
    line=42,
    severity='error',
    suggestions=[
        'Review test output for details',
        'Check test data and fixtures',
        'Verify recent code changes',
    ],
)

aggregator.add_error(
    error_type='validation_error',
    message='PDF validation failed: missing figures',
    stage='validation',
    severity='error',
    suggestions=[
        'Check figure generation scripts',
        'Verify figure paths in manuscript',
    ],
)

# Generate summary
summary = aggregator.get_summary()
# Returns: {
#     'total_errors': 2,
#     'errors_by_type': {'test_failure': 1, 'validation_error': 1},
#     'actionable_fixes': [...],
#     ...
# }

# Save reports
aggregator.save_report(Path("output/reports"))
# Creates: error_summary.json and error_summary.md
```

#### Error Types

Common error types:
- `test_failure` - Test execution failures
- `validation_error` - Validation check failures
- `stage_failure` - Pipeline stage failures
- `build_error` - Build process errors
- `configuration_error` - Configuration issues

### HTML Templates (`html_templates.py`)

Reusable HTML templates for report generation.

#### Key Functions

**`get_base_html_template()`**
- Base HTML template with styling
- Responsive design
- Professional appearance

**`render_summary_cards()`**
- Renders summary statistics as cards
- Grid layout for multiple metrics

**`render_table()`**
- Renders data tables
- Supports headers and rows

## Integration Points

### Pipeline Integration

The reporting module is integrated into:

1. **`scripts/run_all.py`**
   - Generates consolidated pipeline report at end
   - Includes all stage results, test results, validation results
   - Saves to `project/output/reports/pipeline_report.{json,html,md}`

2. **`scripts/01_run_tests.py`**
   - Generates structured test reports
   - Includes test counts, coverage metrics, execution times
   - Saves to `project/output/reports/test_results.{json,md}`

3. **`scripts/04_validate_output.py`**
   - Generates enhanced validation reports
   - Includes actionable recommendations
   - Saves to `project/output/reports/validation_report.{json,md}`

### Error Aggregation Integration

Error aggregator can be used throughout the pipeline:

```python
from infrastructure.reporting import get_error_aggregator

aggregator = get_error_aggregator()

try:
    run_stage()
except Exception as e:
    aggregator.add_error(
        error_type='stage_failure',
        message=str(e),
        stage='analysis',
        suggestions=['Check stage logs', 'Verify inputs'],
    )
```

## Report Structure

### Pipeline Report

```python
@dataclass
class PipelineReport:
    timestamp: str
    total_duration: float
    stages: List[StageResult]
    test_results: Optional[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]]
    performance_metrics: Optional[Dict[str, Any]]
    error_summary: Optional[Dict[str, Any]]
    output_statistics: Optional[Dict[str, Any]]
```

### Error Summary

```python
{
    'timestamp': '2025-12-04T14:01:30',
    'total_errors': 2,
    'total_warnings': 1,
    'errors_by_type': {'test_failure': 1, 'validation_error': 1},
    'warnings_by_type': {'performance': 1},
    'errors': [...],  # List of ErrorEntry dictionaries
    'warnings': [...],  # List of ErrorEntry dictionaries
    'actionable_fixes': [
        {
            'priority': 'high',
            'issue': '1 test failure(s)',
            'actions': [...],
            'documentation': 'docs/TESTING_GUIDE.md',
        },
    ],
}
```

## Best Practices

### Error Reporting

1. **Categorize Errors**: Use consistent error types for better aggregation
2. **Provide Context**: Include file, line, stage information when available
3. **Actionable Suggestions**: Provide specific steps to fix issues
4. **Priority Levels**: Use appropriate severity levels (error, warning, info)

### Report Generation

1. **Multiple Formats**: Always generate JSON, HTML, and Markdown
2. **Structured Data**: Use consistent data structures for machine processing
3. **Human-Readable**: Ensure Markdown reports are clear and actionable
4. **Visual Indicators**: Use status badges and color coding in HTML reports

### Integration

1. **Non-Blocking**: Report generation should not fail the pipeline
2. **Graceful Degradation**: Handle missing data gracefully
3. **Performance**: Report generation should be fast (< 1s)
4. **Location**: Save all reports to `project/output/reports/`

## Testing

The reporting module has comprehensive test coverage:

```bash
# Run reporting module tests
pytest tests/infrastructure/reporting/ -v

# With coverage
pytest tests/infrastructure/reporting/ --cov=infrastructure.reporting
```

## See Also

- [`README.md`](README.md) - Quick reference guide
- [`../README.md`](../README.md) - Infrastructure layer overview
- [`../AGENTS.md`](../AGENTS.md) - Complete infrastructure documentation
- [`../../docs/ADVANCED_MODULES_GUIDE.md`](../../docs/ADVANCED_MODULES_GUIDE.md) - Advanced modules guide



