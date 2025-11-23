# Python Logging Standards

## Unified Logging System

All Python scripts use `infrastructure/core/logging_utils.py`.

### Import Pattern

```python
from infrastructure.core.logging_utils import get_logger, log_operation, log_success

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

## Advanced Logging Patterns

### Context Managers for Logging

```python
from contextlib import contextmanager
from infrastructure.core.logging_utils import get_logger
import time

logger = get_logger(__name__)

@contextmanager
def log_operation(operation_name: str):
    """Context manager for logging operations.
    
    Usage:
        with log_operation("Data processing"):
            process_data()
    """
    logger.info(f"Starting: {operation_name}")
    start_time = time.time()
    try:
        yield
        elapsed = time.time() - start_time
        logger.info(f"Completed: {operation_name} ({elapsed:.2f}s)")
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed: {operation_name} ({elapsed:.2f}s)", exc_info=True)
        raise

# Usage
with log_operation("Data validation"):
    validate_all_data()
```

### Structured Logging Pattern

```python
import json
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

def log_structured(message: str, **context):
    """Log with structured context.
    
    Args:
        message: Log message
        **context: Structured context data
    """
    log_entry = {
        "message": message,
        **context
    }
    logger.info(json.dumps(log_entry))

# Usage
log_structured(
    "User created",
    user_id=123,
    email="alice@example.com",
    timestamp="2025-01-01T12:00:00Z"
)
```

### Progress Logging Pattern

```python
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

def process_items(items: list, callback):
    """Process items with progress logging.
    
    Args:
        items: Items to process
        callback: Callback for each item
    """
    total = len(items)
    logger.info(f"Processing {total} items")
    
    for i, item in enumerate(items, 1):
        callback(item)
        
        # Log progress every 10%
        if i % max(1, total // 10) == 0:
            logger.info(f"Progress: {i}/{total} ({100*i//total}%)")
    
    logger.info(f"Completed: processed {total} items")

# Usage
def process_user(user):
    # Process user...
    pass

process_items(users, process_user)
```

### Conditional Logging

```python
from infrastructure.core.logging_utils import get_logger
import os

logger = get_logger(__name__)

def debug_function():
    """Function with debug logging."""
    is_debug = os.getenv("DEBUG", "0") == "1"
    
    if is_debug:
        logger.debug("Debug mode enabled")
        logger.debug(f"Variable x = {x}")
        logger.debug(f"Function input: {input_data}")
    
    result = perform_calculation()
    
    if is_debug:
        logger.debug(f"Result: {result}")
    
    return result
```

## Log Message Guidelines

### Good Log Messages

```python
# ✅ GOOD: Clear, actionable
logger.info("User registration completed: alice@example.com")

# ✅ GOOD: With context
logger.warning(f"Database connection slow: {duration:.2f}s")

# ✅ GOOD: Error with details
logger.error(f"Failed to parse config: {file}", exc_info=True)

# ❌ BAD: Too vague
logger.info("Something happened")

# ❌ BAD: No context
logger.warning("Timeout")

# ❌ BAD: Print statements instead of logging
print(f"Processing {count} items")
```

### Formatting Best Practices

```python
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

# ✅ GOOD: Use f-strings
count = 100
logger.info(f"Processing {count} items")

# ✅ GOOD: Include relevant context
user_id = 123
logger.info(f"User login: id={user_id}, timestamp={timestamp}")

# ✅ GOOD: Use appropriate log level
logger.debug("Variable state: x=10, y=20")     # Development details
logger.info("User created successfully")        # Normal progress
logger.warning("Retrying connection attempt")   # Potential issue
logger.error("Failed to save data", exc_info=True)  # Error occurred
```

## Integrating with Error Handling

```python
from infrastructure.core.logging_utils import get_logger
from infrastructure.core.exceptions import ValidationError

logger = get_logger(__name__)

def validate_and_log(data: dict) -> bool:
    """Validate data with logging.
    
    Args:
        data: Data to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If invalid
    """
    try:
        logger.debug(f"Starting validation of {len(data)} items")
        result = validate_data(data)
        logger.info(f"Validation successful: {result['valid_count']} valid")
        return True
    except ValueError as e:
        logger.warning(f"Validation failed: {e}")
        raise ValidationError("Data validation failed") from e
    except Exception as e:
        logger.error(f"Unexpected error during validation", exc_info=True)
        raise ValidationError("Validation error") from e
```

## Log Levels Guide

### DEBUG (Level 0)

Use for development and troubleshooting:

```python
logger.debug("Entering function validate_user()")
logger.debug(f"Loaded config from: {config_path}")
logger.debug(f"Function parameters: {locals()}")
```

### INFO (Level 1, Default)

Use for normal operation progress:

```python
logger.info("Application started")
logger.info("Configuration loaded successfully")
logger.info(f"Processing {count} items")
```

### WARNING (Level 2)

Use for potentially problematic situations:

```python
logger.warning("Config file not found, using defaults")
logger.warning(f"Slow database query: {duration:.2f}s")
logger.warning("Deprecated function used, will be removed")
```

### ERROR (Level 3)

Use for errors that occurred:

```python
logger.error("Failed to connect to database", exc_info=True)
logger.error(f"Invalid configuration: {config_path}")
logger.error("User authentication failed")
```

## Testing Logging

```python
import pytest
from infrastructure.core.logging_utils import get_logger

def test_operation_logs_correctly(caplog):
    """Test that operation logs expected messages."""
    import logging
    caplog.set_level(logging.INFO)
    
    perform_operation()
    
    assert "Operation started" in caplog.text
    assert "Operation completed" in caplog.text
    assert "ERROR" not in caplog.text

def test_error_logging(caplog):
    """Test error logging."""
    import logging
    caplog.set_level(logging.ERROR)
    
    with pytest.raises(Exception):
        failing_operation()
    
    assert "failed" in caplog.text.lower()
```

## See Also

- [Logging Guide](../docs/LOGGING_GUIDE.md) - Comprehensive logging documentation
- [Error Handling](error_handling.md) - Error handling patterns
- [testing_standards.md](testing_standards.md) - Testing logging
- [documentation_standards.md](documentation_standards.md) - Documenting logging



