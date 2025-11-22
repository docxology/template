# Core Module - Quick Reference

Foundation utilities: exceptions, logging, and configuration.

## Quick Start

```python
from infrastructure.core import (
    get_logger,
    TemplateError,
    load_config,
    log_operation
)

# Logging
logger = get_logger(__name__)
logger.info("Starting analysis")

# Exception handling
try:
    result = operation()
except Exception as e:
    raise TemplateError("Operation failed") from e

# Configuration
config = load_config(Path("config.yaml"))
env_vars = get_config_as_dict(Path("."))

# Operation tracking
with log_operation("Processing", logger):
    process_data()
```

## Modules

- **exceptions** - Exception hierarchy and context preservation
- **logging_utils** - Unified Python logging system
- **config_loader** - Configuration file and environment loading

## Key Classes & Functions

### Exception Handling
- `TemplateError` - Base exception class
- `ConfigurationError` - Configuration issues
- `ValidationError` - Validation failures
- `BuildError` - Build process failures
- `LiteratureSearchError` - Literature search errors
- `LLMError` - LLM operation errors
- `RenderingError` - Rendering failures
- `PublishingError` - Publishing errors
- `raise_with_context()` - Raise with keyword context
- `chain_exceptions()` - Chain with original exception
- `format_file_context()` - Format file/line context

### Logging
- `setup_logger()` - Create logger with configuration
- `get_logger()` - Get or create logger
- `log_operation()` - Context manager for operation tracking
- `log_timing()` - Context manager for timing
- `log_function_call()` - Decorator for function logging
- `log_success()` - Log success message with emoji
- `log_header()` - Log section header
- `log_progress()` - Log progress with percentage
- `set_global_log_level()` - Set level for all loggers

### Configuration
- `load_config()` - Load YAML config file
- `get_config_as_dict()` - Get config as key-value dict
- `get_config_as_env_vars()` - Get config as env vars
- `find_config_file()` - Find config in standard locations

## Environment Variables

```bash
# Set logging level (0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR)
export LOG_LEVEL=0

# Disable emoji output
export NO_EMOJI=1
```

## Testing

```bash
pytest tests/infrastructure/test_core/
```

For detailed documentation, see [AGENTS.md](AGENTS.md).

