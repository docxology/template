# Logging Guide - Clear, Documented, Tested, Validated, Streamlined

## Overview

This guide documents the comprehensive logging system used across the research template. The logging infrastructure provides clear, consistent, and well-tested logging functionality at both the infrastructure and project levels.

## Architecture

### Two-Level Logging System

1. **Infrastructure Logging** (`infrastructure.core.logging_utils`)
   - Comprehensive logging utilities
   - Environment-based configuration
   - Context managers and decorators
   - Progress tracking and resource monitoring

2. **Project Logging** (`projects/*/src/utils/logging.py`)
   - Standardized interface for projects
   - Simple, consistent API
   - Graceful fallback when infrastructure unavailable
   - Seamless integration with infrastructure logging

## Quick Start

### For Projects

```python
# Import the standardized logger
from utils.logging import get_logger

# Get a logger for your module
log = get_logger(__name__)

# Basic logging
log.info("Starting analysis")
log.success("Analysis completed!")
log.error("Something went wrong")

# Progress tracking
log.progress(50, 100, "Processing data")
log.stage(2, 5, "Data Analysis")

# Context managers
with log.operation("Running simulation"):
    # Your simulation code
    pass
```

### For Infrastructure Code

```python
# Use the full infrastructure logging
from infrastructure.core.logging_utils import get_logger, log_operation

log = get_logger(__name__)

# Advanced logging features
with log_operation("Complex operation", log):
    # Operation code
    pass

# Resource monitoring
log.resource_usage("After data processing")
```

## Configuration

### Environment Variables

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `LOG_LEVEL` | 0,1,2,3 | 1 | 0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR |
| `NO_EMOJI` | true/false | false | Disable emoji in output |
| `STRUCTURED_LOGGING` | true/false | false | Enable JSON structured logging |

### Setting Log Levels

```bash
# Debug mode (most verbose)
export LOG_LEVEL=0

# Info mode (default)
export LOG_LEVEL=1

# Warnings only
export LOG_LEVEL=2

# Errors only
export LOG_LEVEL=3
```

## Logging Methods

### Standard Methods

```python
log.debug("Detailed diagnostic information")
log.info("General information about execution")
log.warning("Warning about potential issues")
log.error("Error messages for failures")
log.critical("Critical system failures")
```

### Specialized Methods

```python
# Success confirmation
log.success("Operation completed successfully")

# Section headers
log.header("=== ANALYSIS RESULTS ===")

# Progress indicators
log.progress(current=50, total=100, task="Processing data")

# Pipeline stages
log.stage(stage_num=2, total_stages=5, stage_name="Data Analysis")

# Sub-operations
log.substep("Loading dataset...")
log.substep("Running validation...")
```

### Context Managers

```python
# Operation timing and status
with log.operation("Data preprocessing"):
    # Code that gets timed and logged
    preprocess_data()

# Simple timing only
with log.timing("Complex calculation"):
    # Code that gets timed
    complex_calculation()
```

## Advanced Features

### File Logging

```python
from infrastructure.core.logging_utils import setup_project_logging

# Log to file in addition to console
log = setup_project_logging(__name__, log_file="analysis.log")
log.info("This goes to both console and file")
```

### Resource Monitoring

```python
# Log current system resource usage
log.resource_usage("After memory-intensive operation")
```

Output includes CPU usage, memory usage, and system load.

### Structured Logging

```bash
export STRUCTURED_LOGGING=true
```

Enables JSON-formatted log output for log aggregation systems.

## Best Practices

### 1. Logger Naming

```python
# ✅ GOOD: Use __name__ for proper hierarchy
log = get_logger(__name__)

# ❌ BAD: Hardcoded names
log = get_logger("my_script")
```

### 2. Appropriate Log Levels

```python
# ✅ GOOD: Use appropriate levels
log.debug("Variable x = 42")      # Debug: internal state
log.info("Processing 1000 files") # Info: normal operation
log.warning("File not found, using default")  # Warning: recoverable issues
log.error("Failed to connect to database")    # Error: operation failure

# ❌ BAD: Wrong levels
log.info("x = 42")                # Too verbose for info
log.error("File not found")       # Not an error if handled
```

### 3. Context Managers for Operations

```python
# ✅ GOOD: Use context managers for clear operations
with log.operation("Data analysis pipeline"):
    load_data()
    process_data()
    save_results()

# ❌ BAD: Manual start/end logging
log.info("Starting data analysis")
load_data()
process_data()
save_results()
log.info("Completed data analysis")
```

### 4. Progress Tracking

```python
# ✅ GOOD: Progress for long operations
for i, item in enumerate(items):
    process_item(item)
    log.progress(i + 1, len(items), f"Processing {item.name}")

# ✅ GOOD: Stage tracking for pipelines
log.stage(1, 4, "Data Loading")
# ... loading code ...
log.stage(2, 4, "Data Processing")
# ... processing code ...
```

### 5. Error Context

```python
# ✅ GOOD: Include context in error messages
try:
    process_file(filename)
except Exception as e:
    log.error(f"Failed to process {filename}: {e}")
    raise

# ✅ GOOD: Use substep logging for complex operations
log.info("Starting batch processing")
for batch in batches:
    log.substep(f"Processing batch {batch.id}")
    process_batch(batch)
```

## Testing Logging

### Unit Testing

```python
# Test that logging calls don't raise exceptions
def test_logging_no_errors():
    log = get_logger("test_module")

    # These should not raise exceptions
    log.info("Test message")
    log.success("Success message")
    log.progress(50, 100, "Test progress")

    # Context managers should work
    with log.operation("Test operation"):
        pass
```

### Integration Testing

```python
# Test logging in real scenarios
def test_logging_integration(tmp_path):
    log_file = tmp_path / "test.log"
    log = setup_project_logging("test", log_file=str(log_file))

    log.info("Integration test message")

    # Verify log file contains expected content
    content = log_file.read_text()
    assert "Integration test message" in content
```

## Fallback Behavior

The project logging system includes graceful fallback when infrastructure is unavailable:

```python
# If infrastructure import fails, falls back to basic logging
from utils.logging import get_logger  # Still works!

log = get_logger(__name__)  # Uses basic Python logging
log.info("This still works")  # Basic functionality preserved
```

## Examples

### Research Script Logging

```python
#!/usr/bin/env python3
"""Research analysis script with comprehensive logging."""

from utils.logging import get_logger

log = get_logger(__name__)

def main():
    log.header("Research Data Analysis")

    with log.operation("Data preprocessing"):
        log.substep("Loading dataset")
        data = load_dataset()

        log.substep("Cleaning data")
        clean_data = preprocess_data(data)

    log.progress(25, 100, "Preprocessing complete")

    with log.operation("Statistical analysis"):
        log.substep("Running statistical tests")
        results = run_statistics(clean_data)

        log.substep("Generating visualizations")
        create_plots(results)

    log.success("Analysis completed successfully")
    log.resource_usage("Final resource usage")

if __name__ == "__main__":
    main()
```

### Pipeline Stage Logging

```python
from utils.logging import get_logger

log = get_logger(__name__)

def run_pipeline():
    """Complete research pipeline with stage logging."""

    # Stage 1: Data Collection
    log.stage(1, 4, "Data Collection")
    with log.operation("Collecting research data"):
        data = collect_data()
    log.progress(25, 100, "Data collection complete")

    # Stage 2: Data Processing
    log.stage(2, 4, "Data Processing")
    with log.operation("Processing and cleaning data"):
        processed = process_data(data)
    log.progress(50, 100, "Data processing complete")

    # Stage 3: Analysis
    log.stage(3, 4, "Analysis")
    with log.operation("Running statistical analysis"):
        results = analyze_data(processed)
    log.progress(75, 100, "Analysis complete")

    # Stage 4: Reporting
    log.stage(4, 4, "Reporting")
    with log.operation("Generating reports and figures"):
        generate_report(results)
    log.progress(100, 100, "Pipeline complete")

    log.success("Research pipeline completed successfully")
```

## Troubleshooting

### Common Issues

**1. No output visible**
```bash
# Check log level
export LOG_LEVEL=0  # Enable debug output

# Check if NO_EMOJI is set (can hide success messages)
unset NO_EMOJI
```

**2. Import errors**
```python
# For projects, ensure conftest.py adds infrastructure to path
# This is handled automatically in the template
```

**3. File logging not working**
```python
# Ensure directory exists and is writable
import os
os.makedirs(os.path.dirname(log_file), exist_ok=True)
```

**4. Performance impact**
```python
# Logging is designed to be lightweight
# Use appropriate levels to control verbosity
# Resource monitoring only runs when called
```

## Integration with Build System

### Automatic Logging in Scripts

The build system automatically provides logging context:

```python
# scripts/analysis_pipeline.py
from utils.logging import get_logger

log = get_logger(__name__)

def main():
    log.info("Starting analysis pipeline")
    # Your analysis code
    log.success("Pipeline completed")

if __name__ == "__main__":
    main()
```

### Log File Collection

Generated log files are collected in output directories:

```
output/
├── logs/                    # Pipeline execution logs
│   ├── analysis.log        # Analysis script logs
│   └── rendering.log       # Rendering logs
└── reports/                # Include logging in reports
    └── pipeline_report.md  # Contains execution logs
```

## Performance Considerations

### Efficient Logging

- **Lazy evaluation**: Complex formatting only when log level allows
- **Minimal overhead**: Context managers use lightweight timing
- **Resource monitoring**: Only runs when explicitly called
- **Buffering**: File logging uses appropriate buffering

### Memory Usage

- **Context preservation**: Minimal memory overhead for context managers
- **Circular references**: Avoided in logging objects
- **Cleanup**: Automatic cleanup of temporary logging resources

## Validation and Testing

### Logging Validation

All logging functionality is thoroughly tested:

```bash
# Test infrastructure logging
pytest tests/infrastructure/core/test_logging_utils.py -v

# Test project logging
pytest projects/project/tests/test_logging.py -v

# Test integration logging
pytest tests/integration/test_logging.py -v
```

### Coverage Requirements

- **Infrastructure logging**: 100% coverage required
- **Project logging**: 100% coverage required
- **Integration logging**: Full validation of output

## Migration Guide

### From Old Logging

**Before (inconsistent):**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Message")
```

**After (standardized):**
```python
from utils.logging import get_logger
log = get_logger(__name__)
log.info("Message")
```

### Benefits of Migration

1. **Consistency**: Same interface across all projects
2. **Features**: Progress tracking, context managers, resource monitoring
3. **Fallback**: Graceful degradation when infrastructure unavailable
4. **Testing**: Comprehensive test coverage and validation
5. **Documentation**: Well-documented API and best practices

## API Reference

### ProjectLogger Class

```python
class ProjectLogger:
    """Standardized logging interface for projects."""

    def __init__(self, name: str, level: Optional[int] = None)
    def debug(self, message: str, *args, **kwargs) -> None
    def info(self, message: str, *args, **kwargs) -> None
    def warning(self, message: str, *args, **kwargs) -> None
    def error(self, message: str, *args, **kwargs) -> None
    def critical(self, message: str, *args, **kwargs) -> None

    # Specialized methods
    def success(self, message: str) -> None
    def header(self, message: str) -> None
    def progress(self, current: int, total: int, task: str = "") -> None
    def stage(self, stage_num: int, total_stages: int, stage_name: str) -> None
    def substep(self, message: str) -> None

    # Context managers
    def operation(self, operation: str, level: int = logging.INFO) -> ContextManager
    def timing(self, label: str) -> ContextManager

    # Resource monitoring
    def resource_usage(self, stage_name: str = "") -> None
```

### Convenience Functions

```python
def get_logger(name: str, level: Optional[int] = None) -> ProjectLogger:
    """Get a standardized logger for projects."""

def get_project_logger(name: str, level: Optional[int] = None) -> ProjectLogger:
    """Alias for get_logger."""

def setup_project_logging(name: str, level: Optional[int] = None,
                         log_file: Optional[str] = None) -> ProjectLogger:
    """Set up project logging with optional file output."""
```

## See Also

- [Infrastructure Logging Documentation](../infrastructure/core/AGENTS.md)
- [Project Logging Tests](../projects/project/tests/test_logging.py)
- [Infrastructure Logging Tests](../tests/infrastructure/core/test_logging_utils.py)
- [Integration Logging Tests](../tests/integration/test_logging.py)