# Reporting Module

> **Pipeline reporting and error aggregation**

**Location:** `infrastructure/reporting/`  
**Quick Reference:** [Modules Guide](../MODULES_GUIDE.md) | [API Reference](../../reference/API_REFERENCE.md)

---

## Key Features

- **Consolidated Pipeline Reports**: Multi-format reports (JSON, HTML, Markdown)
- **Test Results Reporting**: Structured reports with coverage metrics
- **Validation Reports**: Actionable recommendations with priority levels
- **Performance Metrics**: Bottleneck analysis, resource tracking
- **Error Aggregation**: Categorized errors with fixes and documentation links
- **HTML Templates**: Visual reports with responsive design

---

## Usage Examples

### Generate Pipeline Report

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
    test_results={'summary': {'total_tests': 2118, 'total_passed': 2118}},
    validation_results={'checks': {'pdf_validation': True}},
    performance_metrics={'total_duration': 60.5},
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
    message='Test test_example failed with assertion error',
    stage='tests',
    file='tests/test_example.py',
    line=42,
    severity='error',
    suggestions=[
        'Review test output for details',
        'Check test data and fixtures',
    ],
)

# Generate summary
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
        {
            'priority': 'high',
            'issue': 'Missing output directories',
            'action': 'Ensure all analysis scripts completed successfully',
        },
    ],
}

saved_files = generate_validation_report(validation_results, Path("output/reports"))
```

---

## Integration

The reporting module is automatically integrated into:

- `scripts/execute_pipeline.py` - Generates consolidated pipeline report
- `scripts/01_run_tests.py` - Generates structured test reports
- `scripts/04_validate_output.py` - Generates validation reports

Reports are saved to `project/output/reports/` by default.

---

## Report Formats

| Format | Description |
|--------|-------------|
| **JSON** | Machine-readable for programmatic access |
| **HTML** | Visual format with styling for browsers |
| **Markdown** | Human-readable for documentation |

---

**Related:** [Integrity Module](INTEGRITY_MODULE.md) | [Rendering Module](RENDERING_MODULE.md)
