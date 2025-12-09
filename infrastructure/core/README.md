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
- **progress** - Progress tracking utilities
- **checkpoint** - Pipeline checkpoint management
- **retry** - Retry logic with backoff
- **performance** - Performance monitoring
- **environment** - Environment setup and validation
- **script_discovery** - Script discovery and execution
- **file_operations** - File management utilities

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
- `get_config_as_dict()` - Get config as key-value dict from `project/manuscript/config.yaml`
- `get_config_as_env_vars()` - Get config as env vars
- `find_config_file()` - Find config file at `project/manuscript/config.yaml`
- `get_translation_languages()` - Get translation languages from config

### Progress Tracking
- `ProgressBar` - Visual progress indicators
- `SubStageProgress` - Nested progress tracking

### Checkpoint Management
- `CheckpointManager` - Save/restore pipeline state
- `PipelineCheckpoint` - Checkpoint data structures
- `StageResult` - Individual stage result

### Retry Logic
- `retry_with_backoff()` - Exponential backoff retries
- `retry_on_transient_failure()` - Retry on transient errors
- `RetryableOperation` - Retryable operation wrapper

### Performance Monitoring
- `PerformanceMonitor` - Resource usage tracking
- `PerformanceMetrics` - Performance metrics dataclass
- `ResourceUsage` - Resource usage dataclass
- `monitor_performance()` - Context manager for performance monitoring
- `get_system_resources()` - System resource queries

### Environment Setup
- `check_python_version()` - Verify Python version
- `check_dependencies()` - Check required dependencies
- `install_missing_packages()` - Install missing packages
- `check_build_tools()` - Verify build tools availability
- `setup_directories()` - Create required directories
- `verify_source_structure()` - Validate project structure
- `set_environment_variables()` - Set environment variables

### Script Discovery
- `discover_analysis_scripts()` - Find project analysis scripts
- `discover_orchestrators()` - Find orchestrator scripts
- `verify_analysis_outputs()` - Verify script outputs

### File Operations
- `clean_output_directory()` - Clean output directory
- `clean_output_directories()` - Clean multiple output directories
- `copy_final_deliverables()` - Copy final outputs

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

