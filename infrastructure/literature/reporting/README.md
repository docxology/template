# Reporting Module

Comprehensive reporting with JSON/CSV/HTML export.

## Components

- **reporter.py**: `LiteratureReporter` for generating reports

## Quick Start

```python
from infrastructure.literature.reporting import LiteratureReporter

reporter = LiteratureReporter("output/reports")
reporter.generate_workflow_report(workflow_result, format="all")
```

## Features

- Multiple export formats (JSON, CSV, HTML)
- Workflow statistics
- Paper metadata export
- Summary reports

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../AGENTS.md`](../AGENTS.md) - Literature module overview


