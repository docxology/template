# Logging Guide

> **Unified Python logging system** for consistent, informative output across all scripts

**Quick Reference:** [Error Handling Guide](ERROR_HANDLING_GUIDE.md) | [Testing Guide](TESTING_GUIDE.md) | [Troubleshooting](TROUBLESHOOTING_GUIDE.md)

This guide explains how to use the unified logging system in the Research Project Template. The logging system provides consistent formatting, log levels, and integration across Python and bash scripts.

## Overview

The template uses two complementary logging systems:
- **Python logging** (`infrastructure/logging_utils.py`) - For Python scripts
- **Bash logging** (`repo_utilities/logging.sh`) - For shell scripts

Both systems share:
- Consistent log levels (DEBUG, INFO, WARN, ERROR)
- Matching timestamp formats
- Environment-based configuration
- Emoji support (when appropriate)

##Quick Start

### Python Scripts

```python
from logging_utils import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Log messages
logger.info("Processing started")
logger.warning("File not found, using default")
logger.error("Failed to load data")
logger.debug("Variable value: {value}")
```

### Bash Scripts

```bash
#!/bin/bash

# Source logging library
source "$REPO_ROOT/repo_utilities/logging.sh"

# Log messages
log_info "Starting process"
log_warn "Potential issue detected"
log_error "Process failed"
log_debug "Debug information"
```

## Python Logging System

### Basic Usage

```python
from logging_utils import get_logger, log_operation, log_success

# Set up logger
logger = get_logger(__name__)

# Log different levels
logger.debug("Detailed diagnostic information")
logger.info("General information about progress")
logger.warning("Warning about potential issues")
logger.error("Error that occurred")

# Log success
log_success("Operation completed successfully", logger)
```

### Context Managers

Use context managers for automatic operation tracking:

```python
from logging_utils import log_operation, log_timing

# Log operation start and completion
with log_operation("Processing data", logger):
    process_data()
    # Automatically logs start, completion, and duration

# Time operations
with log_timing("Expensive calculation", logger):
    result = expensive_calculation()
    # Logs execution time
```

### Function Decorators

Decorate functions for automatic call logging:

```python
from logging_utils import log_function_call

@log_function_call(logger)
def process_file(filename: str) -> bool:
    """Process a file."""
    return True

# Automatically logs:
# - Function call with arguments
# - Return value
# - Execution time
# - Exceptions (if any)
```

### Utility Functions

```python
from logging_utils import log_header, log_progress, log_success

# Section headers
log_header("STAGE 01: Setup", logger)

# Progress tracking
for i in range(total):
    log_progress(i+1, total, "Processing files", logger)

# Success messages
log_success("All files processed", logger)
```

## Log Levels

### When to Use Each Level

| Level | Value | Usage | Example |
|-------|-------|-------|---------|
| **DEBUG** | 0 | Detailed diagnostics, variable values | `logger.debug(f"Value: {x}")` |
| **INFO** | 1 | General progress, normal operations | `logger.info("Processing started")` |
| **WARN** | 2 | Potential issues, fallback behavior | `logger.warning("File not found, using default")` |
| **ERROR** | 3 | Errors, failures | `logger.error("Failed to load data")` |

### Setting Log Level

**Environment Variable:**
```bash
# In terminal
export LOG_LEVEL=0  # DEBUG (most verbose)
export LOG_LEVEL=1  # INFO (default)
export LOG_LEVEL=2  # WARN
export LOG_LEVEL=3  # ERROR (least verbose)

# Run scripts with specific level
LOG_LEVEL=0 python3 scripts/run_all.py
```

**In Code:**
```python
import logging
from logging_utils import setup_logger, set_global_log_level

# For specific logger
logger = setup_logger(__name__, level=logging.DEBUG)

# For all loggers
set_global_log_level(logging.DEBUG)
```

## Advanced Features

### Log Files

Write logs to file in addition to console:

```python
from pathlib import Path
from logging_utils import setup_logger

log_file = Path("output/logs/build.log")
logger = setup_logger(__name__, log_file=log_file)

logger.info("This goes to console AND file")
```

### Custom Formatting

The logging system automatically formats messages:

```
ℹ️ [2025-11-21 12:00:00] [INFO] Processing started
⚠️ [2025-11-21 12:00:05] [WARN] File not found
❌ [2025-11-21 12:00:10] [ERROR] Processing failed
```

Format: `[emoji] [YYYY-MM-DD HH:MM:SS] [LEVEL] message`

### Disable Emojis

For plain text environments:

```bash
# Environment variable
export NO_EMOJI=1

# Or in CI/CD
NO_EMOJI=1 python3 scripts/run_all.py
```

## Integration with Infrastructure

### Using with Exceptions

Combine logging with custom exceptions:

```python
from logging_utils import get_logger
from exceptions import ValidationError, raise_with_context

logger = get_logger(__name__)

def validate_data(data):
    try:
        check_data(data)
        logger.info("Validation passed")
    except ValueError as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise_with_context(
            ValidationError,
            "Data validation failed",
            file="data.csv",
            reason=str(e)
        )
```

### Pipeline Orchestration

In pipeline scripts:

```python
from logging_utils import get_logger, log_header, log_success, log_operation

logger = get_logger(__name__)

def main():
    log_header("STAGE 02: Run Analysis", logger)
    
    try:
        with log_operation("Execute analysis scripts", logger):
            run_scripts()
        log_success("Analysis complete", logger)
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1
```

## Best Practices

### Do's ✅

- **Use appropriate log levels** - DEBUG for diagnostics, INFO for progress, WARN for issues, ERROR for failures
- **Include context** - Add relevant information (file names, line numbers, values)
- **Use context managers** - Automatic timing and error handling
- **Log exceptions with context** - Use `exc_info=True` for stack traces
- **Consistent logger names** - Use `__name__` for module-level loggers
- **Progress indicators** - Use `log_progress()` for long-running operations

### Don'ts ❌

- **Don't use print()** - Use logger instead
- **Don't log sensitive data** - Passwords, tokens, personal information
- **Don't log in tight loops** - Log at appropriate intervals
- **Don't mix logging systems** - Use unified logging consistently
- **Don't ignore log levels** - Respect LOG_LEVEL environment variable
- **Don't duplicate messages** - Log once at the right level

## Common Patterns

### Script Entry Point

```python
#!/usr/bin/env python3
"""Script description."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "infrastructure"))
from logging_utils import get_logger, log_header, log_success

logger = get_logger(__name__)

def main() -> int:
    log_header("SCRIPT NAME", logger)
    
    try:
        # Script logic here
        logger.info("Processing...")
        log_success("Complete", logger)
        return 0
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
```

### Function with Error Handling

```python
def process_file(file_path: Path) -> dict:
    """Process a file and return results."""
    logger.info(f"Processing: {file_path}")
    
    try:
        with log_operation(f"Load {file_path.name}", logger):
            data = load_file(file_path)
        
        with log_timing("Process data", logger):
            result = process_data(data)
        
        log_success(f"Processed {file_path.name}", logger)
        return result
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
```

### Progress Reporting

```python
def process_files(files: list[Path]) -> None:
    """Process multiple files with progress reporting."""
    logger.info(f"Processing {len(files)} files")
    
    for i, file_path in enumerate(files, 1):
        log_progress(i, len(files), f"Processing {file_path.name}", logger)
        process_file(file_path)
    
    log_success(f"Processed all {len(files)} files", logger)
```

## Troubleshooting

### No Log Output

**Problem:** Logs not appearing

**Solutions:**
1. Check log level: `LOG_LEVEL=0 python3 script.py`
2. Ensure logger is set up: `logger = get_logger(__name__)`
3. Check if using print() instead of logger

### Too Verbose

**Problem:** Too many log messages

**Solutions:**
1. Increase log level: `export LOG_LEVEL=1` (or 2, 3)
2. Review DEBUG messages - are they necessary?
3. Use appropriate levels for each message

### No Emoji/Colors

**Problem:** Plain text only

**Solutions:**
- Expected in non-TTY environments (pipes, redirects)
- Set `NO_EMOJI=1` explicitly if desired
- Check terminal supports UTF-8

### Log File Not Created

**Problem:** Log file not being written

**Solutions:**
1. Check directory exists: `Path(log_file).parent.mkdir(parents=True, exist_ok=True)`
2. Check permissions
3. Use absolute paths

## Examples

### Complete Script Example

```python
#!/usr/bin/env python3
"""Analysis script with comprehensive logging."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "infrastructure"))

from logging_utils import (
    get_logger,
    log_header,
    log_operation,
    log_timing,
    log_progress,
    log_success
)
from exceptions import ValidationError, raise_with_context

logger = get_logger(__name__)

def validate_input(data_path: Path) -> None:
    """Validate input data exists and is readable."""
    if not data_path.exists():
        raise_with_context(
            ValidationError,
            "Input file not found",
            file=str(data_path)
        )
    logger.info(f"Input validated: {data_path}")

def process_data(data_path: Path) -> dict:
    """Process data file."""
    with log_operation(f"Process {data_path.name}", logger):
        # Simulated processing
        result = {"processed": True, "file": str(data_path)}
    return result

def main() -> int:
    """Execute analysis with logging."""
    log_header("DATA ANALYSIS PIPELINE", logger)
    
    try:
        # Inputs
        data_files = list(Path("data").glob("*.csv"))
        logger.info(f"Found {len(data_files)} files to process")
        
        # Validate
        with log_timing("Validation", logger):
            for data_file in data_files:
                validate_input(data_file)
        
        # Process
        results = []
        for i, data_file in enumerate(data_files, 1):
            log_progress(i, len(data_files), "Processing", logger)
            result = process_data(data_file)
            results.append(result)
        
        log_success(f"Processed {len(results)} files successfully", logger)
        return 0
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
```

## See Also

- [Error Handling Guide](ERROR_HANDLING_GUIDE.md) - Custom exception usage
- [Testing Guide](TESTING_GUIDE.md) - Testing with logging
- [Troubleshooting](TROUBLESHOOTING_GUIDE.md) - Common issues
- [Build System](BUILD_SYSTEM.md) - Pipeline logging
- [API Reference](API_REFERENCE.md) - Full API documentation

## Quick Reference Card

```python
# Setup
from logging_utils import get_logger, log_operation, log_success
logger = get_logger(__name__)

# Levels
logger.debug("Diagnostic")    # LOG_LEVEL=0
logger.info("Progress")        # LOG_LEVEL=1 (default)
logger.warning("Issue")        # LOG_LEVEL=2
logger.error("Failure")        # LOG_LEVEL=3

# Context managers
with log_operation("Task", logger):
    do_task()

with log_timing("Operation", logger):
    expensive_operation()

# Utilities
log_success("Done", logger)
log_header("SECTION", logger)
log_progress(i, total, "Task", logger)

# Configuration
export LOG_LEVEL=0  # Environment
logger = setup_logger(__name__, level=logging.DEBUG)  # Code
```

---

**Key Takeaways:**
- Use unified logging for consistency
- Choose appropriate log levels
- Include context in messages
- Use context managers for operations
- Follow best practices










