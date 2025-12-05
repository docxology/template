# Core Module

## Purpose

The Core module provides fundamental foundation utilities used across the entire infrastructure layer. It includes configuration management, unified logging, and a comprehensive exception hierarchy with context preservation.

## Architecture

### Core Components

**exceptions.py**
- Base exception hierarchy (TemplateError and subclasses)
- Context preservation with exception chaining
- Module-specific exceptions (Literature, LLM, Rendering, Publishing)
- Exception utility functions for context formatting

**logging_utils.py**
- Unified Python logging with consistent formatting
- Environment-based configuration (LOG_LEVEL 0-3)
- Context managers for operation tracking and timing
- Decorators for function call logging
- Integration with bash logging.sh format
- Emoji support for TTY output

**config_loader.py**
- YAML configuration file loading
- Environment variable support with priority
- Author and metadata formatting
- Configuration file discovery
- Environment variable export

## Key Features

### Exception Handling
```python
from infrastructure.core import (
    TemplateError,
    raise_with_context,
    chain_exceptions
)

try:
    risky_operation()
except ValueError as e:
    raise chain_exceptions(
        TemplateError("Operation failed"),
        e
    )
```

### Logging
```python
from infrastructure.core import get_logger, log_operation, log_timing

logger = get_logger(__name__)
logger.info("Starting process")

with log_operation("Data processing", logger):
    process_data()

with log_timing("Algorithm execution", logger):
    run_algorithm()
```

### Configuration
```python
from infrastructure.core import load_config, get_config_as_dict

config = load_config(Path("project/manuscript/config.yaml"))
env_dict = get_config_as_dict(Path("."))
```

## Testing

Run core tests with:
```bash
pytest tests/infrastructure/test_core/
```

## Configuration

Environment variables (used by logging_utils):
- `LOG_LEVEL` - 0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR (default: 1)
- `NO_EMOJI` - Disable emoji output (default: enabled for TTY)

## Integration

Core module is imported by all other infrastructure modules for:
- Exception handling and context preservation
- Logging and progress tracking
- Configuration loading and management

## See Also

- [README.md](README.md) - Quick reference guide
- [`build/`](../build/) - Build & reproducibility
- [`validation/`](../validation/) - Validation & quality assurance

