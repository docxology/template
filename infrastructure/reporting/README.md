# Reporting Module - Quick Reference

Pipeline reporting and error aggregation utilities.

## Overview

The reporting module provides comprehensive reporting capabilities for pipeline execution, including:
- Consolidated pipeline reports (JSON, HTML, Markdown)
- Test results reporting
- Validation reports with actionable recommendations
- Performance metrics and analysis
- Error aggregation and categorization

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

### Generate Validation Report

```python
from infrastructure.reporting import generate_validation_report

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

saved_files = generate_validation_report(validation_results, Path("output/reports"))
```

## Module Functions

### Pipeline Reporting

- `generate_pipeline_report()` - Create consolidated pipeline report
- `save_pipeline_report()` - Save report in multiple formats (JSON, HTML, Markdown)
- `generate_test_report()` - Generate test results report
- `generate_validation_report()` - Generate enhanced validation report
- `generate_performance_report()` - Generate performance metrics report
- `generate_error_summary()` - Generate error summary report

### Error Aggregation

- `ErrorAggregator` - Main error aggregation class
- `get_error_aggregator()` - Get global error aggregator instance
- `ErrorEntry` - Single error/warning entry dataclass

## Report Formats

All reports are generated in multiple formats:

- **JSON**: Machine-readable format for programmatic access
- **HTML**: Visual format with styling for browser viewing
- **Markdown**: Human-readable format for documentation

## Integration

The reporting module is automatically integrated into:
- `scripts/run_all.py` - Generates pipeline report at end
- `scripts/01_run_tests.py` - Generates test reports
- `scripts/04_validate_output.py` - Generates validation reports

Reports are saved to `project/output/reports/` by default.

## See Also

- [`AGENTS.md`](AGENTS.md) - Comprehensive reporting module documentation
- [`../README.md`](../README.md) - Infrastructure layer overview
- [`../AGENTS.md`](../AGENTS.md) - Complete infrastructure documentation












