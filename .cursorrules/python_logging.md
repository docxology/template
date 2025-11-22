# Python Logging Standards

## Unified Logging System

All Python scripts use `infrastructure/logging_utils.py`.

### Import Pattern

```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "infrastructure"))
from logging_utils import get_logger, log_operation, log_success

logger = get_logger(__name__)
```

## Log Levels

| Level | Value | Usage |
|-------|-------|-------|
| DEBUG | 0 | Diagnostics, variable values |
| INFO | 1 | Normal progress (default) |
| WARN | 2 | Potential issues |
| ERROR | 3 | Failures |

### Environment Control

```bash
export LOG_LEVEL=0  # DEBUG
export LOG_LEVEL=1  # INFO (default)
export LOG_LEVEL=2  # WARN
export LOG_LEVEL=3  # ERROR
```

## Usage Patterns

### Basic Logging

```python
logger.debug(f"Value: {x}")
logger.info("Processing started")
logger.warning("File not found, using default")
logger.error("Operation failed", exc_info=True)
```

### Context Managers

```python
with log_operation("Task name", logger):
    do_task()  # Logs start, completion, duration

with log_timing("Operation", logger):
    expensive_operation()  # Logs execution time
```

### Utility Functions

```python
log_success("Build completed", logger)
log_header("STAGE 01", logger)
log_progress(i, total, "Task", logger)
```

## Integration with Bash

Python and Bash logging systems share:
- Same log levels (0-3)
- Same timestamp format
- Same emoji usage
- Same environment variables

## Best Practices

- Use `get_logger(__name__)` for module loggers
- Include context in messages
- Use `exc_info=True` for exceptions
- Don't use print() - use logger
- Respect LOG_LEVEL environment variable

## See Also

- [Logging Guide](../docs/LOGGING_GUIDE.md)
- [Error Handling](error_handling.md)



