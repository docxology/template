# Logging Guide

> **Unified logging system** for consistent, informative output across Python and Bash

**Quick Reference:** [Error Handling](ERROR_HANDLING_GUIDE.md) | [Testing](../development/TESTING_GUIDE.md) | [Troubleshooting](TROUBLESHOOTING_GUIDE.md)

## Topic-Specific Guides

| Topic | Guide | Description |
|-------|-------|-------------|
| 🐍 **Python** | [logging/PYTHON_LOGGING.md](logging/PYTHON_LOGGING.md) | Python logging system |
| 🐚 **Bash** | [logging/BASH_LOGGING.md](logging/BASH_LOGGING.md) | Shell script logging |
| 📋 **Patterns** | [logging/LOGGING_PATTERNS.md](logging/LOGGING_PATTERNS.md) | Best practices, progress tracking |

---

## Architecture

### Two-Level Logging System

1. **Infrastructure Logging** (`infrastructure.core.logging_utils`)
   - Logging utilities
   - Environment-based configuration
   - Context managers and decorators
   - Progress tracking and resource monitoring

2. **Project Logging** (`projects/*/src/utils/logging.py`)
   - Standardized interface for projects
   - Simple, consistent API
   - Graceful fallback when infrastructure unavailable
   - Seamless integration with infrastructure logging

---

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

### Shell Scripts

```bash
source scripts/bash_utils.sh

log_success "Operation completed"
log_info "General information"
log_warning "Warning message"
log_error "Error occurred"
```

---

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

---

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

---

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

---

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

### 4. Error Context

```python
# ✅ GOOD: Include context in error messages
try:
    process_file(filename)
except Exception as e:
    log.error(f"Failed to process {filename}: {e}")
    raise
```

---

## Pipeline Logging

**Location:** `projects/{project_name}/output/logs/pipeline.log`

**View logs:**

```bash
cat output/code_project/logs/pipeline.log
grep -i error output/code_project/logs/pipeline.log
```

---

## Fallback Behavior

The project logging system includes graceful fallback when infrastructure is unavailable:

```python
# If infrastructure import fails, falls back to basic logging
from utils.logging import get_logger  # Still works!

log = get_logger(__name__)  # Uses basic Python logging
log.info("This still works")  # Basic functionality preserved
```

---

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

---

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

---

## Testing Logging

### Unit Testing

```python
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

---

## See Also

- [Error Handling Guide](ERROR_HANDLING_GUIDE.md) - Custom exception usage
- [Testing Guide](../development/TESTING_GUIDE.md) - Testing with logging
- [API Reference](../reference/API_REFERENCE.md) - Full API documentation
- [Infrastructure Logging](../../infrastructure/core/AGENTS.md) - Infrastructure implementation
