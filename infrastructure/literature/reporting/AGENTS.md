# Reporting Module - Complete Documentation

## Purpose

The reporting module provides comprehensive reporting capabilities with multiple export formats.

## Components

### LiteratureReporter (reporter.py)

Comprehensive reporter for literature operations.

**Key Methods:**
- `generate_workflow_report()` - Generate workflow report
- `export_library_metadata()` - Export library metadata
- `generate_summary_report()` - Generate summary report

**Export Formats:**
- JSON - Machine-readable format
- CSV - Spreadsheet-compatible
- HTML - Human-readable with styling

## Usage Examples

### Generate Reports

```python
from infrastructure.literature.reporting import LiteratureReporter

reporter = LiteratureReporter("output/reports")

# Workflow report
reporter.generate_workflow_report(
    workflow_result,
    library_entries=entries,
    format="all"  # JSON, CSV, HTML
)

# Library metadata
reporter.export_library_metadata(entries, format="csv")
```

## See Also

- [`README.md`](README.md) - Quick reference
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview


