# Python Logging Guide

> **Python logging system** for consistent script output

**Quick Reference:** [Main Logging Guide](../logging-guide.md) | [Bash Logging](bash-logging.md)

---

## Quick Start

```python
from infrastructure.core.logging_utils import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Log messages
logger.info("Processing started")
logger.warning("File not found, using default")
logger.error("Failed to load data")
logger.debug("Variable value: {value}")
```

---

## Log Levels

| Level | Value | Usage | Example |
|-------|-------|-------|---------|
| **DEBUG** | 0 | Detailed diagnostics | `logger.debug(f"Value: {x}")` |
| **INFO** | 1 | General progress | `logger.info("Processing started")` |
| **WARN** | 2 | Potential issues | `logger.warning("Using default")` |
| **ERROR** | 3 | Errors, failures | `logger.error("Failed to load")` |

**Setting Log Level:**

```bash
export LOG_LEVEL=0  # DEBUG (most verbose)
export LOG_LEVEL=1  # INFO (default)
export LOG_LEVEL=2  # WARN
export LOG_LEVEL=3  # ERROR (least verbose)

LOG_LEVEL=0 python3 scripts/execute_pipeline.py --core-only
```

---

## Context Managers

```python
from infrastructure.core.logging_utils import log_operation, log_timing, log_with_spinner

# Log operation start and completion
with log_operation("Processing data", logger):
    process_data()
    # Automatically logs start, completion, and duration

# Silent operation (no completion message)
with log_operation_silent("Quick check", logger):
    quick_check()

# Operation with spinner (for long-running operations)
with log_with_spinner("Loading model...", logger):
    load_model()
```

---

## Function Decorators

```python
from infrastructure.core.logging_utils import log_function_call

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

---

## Utility Functions

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

---

## Structured Logging (JSON)

```bash
# Enable JSON logging
export STRUCTURED_LOGGING=true
python3 scripts/execute_pipeline.py --core-only
```

Output:

```json
{"timestamp": "2025-12-04T14:01:30", "level": "INFO", "logger": "scripts.run_all", "message": "Starting pipeline"}
```

---

## Log Files

```python
from pathlib import Path
from logging_utils import setup_logger

log_file = Path("output/logs/build.log")
logger = setup_logger(__name__, log_file=log_file)

logger.info("This goes to console AND file")
```

---

## Custom Formatting

Default format:

```
ℹ️ [2025-11-21 12:00:00] [INFO] Processing started
⚠️ [2025-11-21 12:00:05] [WARN] File not found
❌ [2025-11-21 12:00:10] [ERROR] Processing failed
```

**Disable Emojis:**

```bash
export NO_EMOJI=1
```

---

## Script Entry Point Pattern

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
        logger.info("Processing...")
        log_success("Complete", logger)
        return 0
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
```

---

## Error Handling Pattern

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
```

---

## Quick Reference Card

```python
# Setup
from logging_utils import get_logger, log_operation, log_success
logger = get_logger(__name__)

# Levels
logger.debug("Diagnostic")    # LOG_LEVEL=0
logger.info("Progress")       # LOG_LEVEL=1 (default)
logger.warning("Issue")       # LOG_LEVEL=2
logger.error("Failure")       # LOG_LEVEL=3

# Context managers
with log_operation("Task", logger):
    do_task()

# Utilities
log_success("Done", logger)
log_header("SECTION", logger)
log_progress(i, total, "Task", logger)
```

---

**Related:** [Bash Logging](bash-logging.md) | [Patterns](logging-patterns.md) | [Main Guide](../logging-guide.md)
