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
- Configuration file discovery at `project/manuscript/config.yaml`
- Environment variable export
- Translation language configuration

**credentials.py**
- Credential management from .env and YAML config files
- Environment variable loading
- YAML configuration with environment variable substitution
- **Optional dependency**: `python-dotenv` (graceful fallback if not installed)
- Supports credential access from multiple sources

**progress.py**
- Progress bar utilities for long-running operations
- Sub-stage progress tracking
- Visual progress indicators

**checkpoint.py**
- Pipeline checkpoint management
- Save/restore pipeline state
- Stage result tracking

**retry.py**
- Retry logic with exponential backoff
- Transient failure handling
- Retryable operation wrappers

**performance.py**
- Performance monitoring and resource tracking
- System resource queries
- Performance metrics collection

**environment.py**
- Environment setup and validation
- Dependency checking and installation
- Build tool verification
- Directory structure setup

**script_discovery.py**
- Script discovery and execution
- Analysis script finding
- Orchestrator script discovery

**file_operations.py**
- File management utilities
- Output directory cleanup
- Final deliverable copying

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
from infrastructure.core import load_config, get_config_as_dict, get_translation_languages, find_config_file

config = load_config(Path("project/manuscript/config.yaml"))
env_dict = get_config_as_dict(Path("."))  # Loads from project/manuscript/config.yaml
config_path = find_config_file(Path("."))  # Returns project/manuscript/config.yaml if found
languages = get_translation_languages(Path("."))
```

### Credential Management
```python
from infrastructure.core.credentials import CredentialManager

# Initialize with optional .env and YAML config files
# Note: python-dotenv is optional - system works without it
manager = CredentialManager(
    env_file=Path(".env"),
    config_file=Path("config.yaml")
)

# Get credentials from environment or config
api_key = manager.get("API_KEY", default="default_key")
```

**Optional Dependency**: The `CredentialManager` uses `python-dotenv` for `.env` file support, but gracefully falls back if not installed. Install with:
```bash
pip install python-dotenv
# or
uv add python-dotenv
```

### Progress Tracking
```python
from infrastructure.core import ProgressBar, SubStageProgress

with ProgressBar(total=100, desc="Processing") as pbar:
    for i in range(100):
        pbar.update(1)
```

### Checkpoint Management
```python
from infrastructure.core import CheckpointManager, StageResult

checkpoint = CheckpointManager()
if checkpoint.checkpoint_exists():
    state = checkpoint.load_checkpoint()
else:
    # Run pipeline stages
    checkpoint.save_checkpoint(stage_results)
```

### Retry Logic
```python
from infrastructure.core import retry_with_backoff

@retry_with_backoff(max_attempts=3, base_delay=1.0)
def risky_operation():
    # Operation that may fail
    pass
```

### Performance Monitoring
```python
from infrastructure.core import PerformanceMonitor, get_system_resources

with PerformanceMonitor() as monitor:
    # Your code here
    pass

resources = get_system_resources()
print(f"CPU: {resources.cpu_percent}%, Memory: {resources.memory_percent}%")
```

### Environment Setup
```python
from infrastructure.core import check_python_version, check_dependencies, setup_directories

check_python_version(min_version=(3, 8))
check_dependencies(["pandas", "numpy"])
setup_directories(["output", "output/figures"])
```

### Script Discovery
```python
from infrastructure.core import discover_analysis_scripts, discover_orchestrators

scripts = discover_analysis_scripts(Path("project/scripts"))
orchestrators = discover_orchestrators(Path("scripts"))
```

### File Operations
```python
from infrastructure.core import clean_output_directory, copy_final_deliverables

clean_output_directory(Path("output"))
copy_final_deliverables(Path("project/output"), Path("output"))
```

## Testing

Run core tests with:
```bash
pytest tests/infrastructure/test_core/
```

## Configuration

Environment variables:
- `LOG_LEVEL` - 0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR (default: 1)
- `NO_EMOJI` - Disable emoji output (default: enabled for TTY)

**Optional Dependencies:**
- `python-dotenv` - For `.env` file support in `credentials.py` (graceful fallback if not installed)

## Integration

Core module is imported by all other infrastructure modules for:
- Exception handling and context preservation
- Logging and progress tracking
- Configuration loading and management

## Troubleshooting

### Configuration Not Loading

**Issue**: `load_config()` returns None or empty configuration.

**Solutions**:
- Verify `project/manuscript/config.yaml` exists and is valid YAML
- Check file permissions (read access required)
- Review YAML syntax for errors
- Use `find_config_file()` to locate config file
- Fall back to environment variables if config file missing

### Logging Not Appearing

**Issue**: Log messages not visible or formatted incorrectly.

**Solutions**:
- Check `LOG_LEVEL` environment variable (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR)
- Verify logger is initialized with `get_logger(__name__)`
- Check if output is redirected (TTY detection)
- Disable emoji with `NO_EMOJI=1` if terminal doesn't support them

### Exception Context Lost

**Issue**: Exception chaining doesn't preserve context.

**Solutions**:
- Use `chain_exceptions()` for proper chaining
- Use `raise_with_context()` to add context
- Check that original exception is passed as `from_exception`
- Review exception hierarchy (use TemplateError subclasses)

### Credential Loading Fails

**Issue**: `CredentialManager` can't load credentials.

**Solutions**:
- Verify `.env` file exists and is readable (if using)
- Check YAML config file format and syntax
- Ensure `python-dotenv` is installed for `.env` support (optional)
- Check environment variable names match expected keys
- Review credential file paths are correct

### Progress Bar Not Displaying

**Issue**: Progress bars don't appear or update.

**Solutions**:
- Verify `tqdm` is installed (required dependency)
- Check if output is redirected (progress bars need TTY)
- Ensure `update()` is called with correct increment
- Use context manager (`with ProgressBar(...)`) for proper cleanup

### Checkpoint Corruption

**Issue**: Checkpoint file is corrupted or unreadable.

**Solutions**:
- Verify checkpoint file path is writable
- Check disk space availability
- Review JSON syntax in checkpoint file
- Use `checkpoint_exists()` before loading
- Handle `JSONDecodeError` gracefully

## Best Practices

### Exception Handling

- **Use TemplateError Hierarchy**: Use appropriate exception types
- **Preserve Context**: Always chain exceptions with context
- **Provide Details**: Include file paths, line numbers, and operation context
- **Fail Gracefully**: Handle errors without crashing entire pipeline

### Logging

- **Use Appropriate Levels**: DEBUG for details, INFO for progress, WARN for issues, ERROR for failures
- **Include Context**: Log operation names, file paths, and relevant data
- **Use Decorators**: `@log_operation` and `@log_timing` for automatic logging
- **Consistent Format**: Use structured logging for parsing

### Configuration

- **Version Control**: Commit `config.yaml.example` but not `config.yaml` (may contain secrets)
- **Environment Variables**: Use for sensitive data (tokens, keys)
- **Defaults**: Provide sensible defaults for all configuration options
- **Validation**: Validate configuration on load

### Credential Management

- **Never Commit Secrets**: Use `.env` or environment variables
- **Use CredentialManager**: Centralized credential access
- **Graceful Fallback**: Handle missing credentials gracefully
- **Document Requirements**: Document required credentials clearly

### Performance

- **Monitor Resources**: Use `PerformanceMonitor` for long operations
- **Track Timing**: Use `log_timing` for performance-critical sections
- **Optimize Hot Paths**: Profile and optimize frequently called functions
- **Resource Limits**: Check system resources before heavy operations

### Checkpointing

- **Save Frequently**: Checkpoint after each successful stage
- **Validate Before Resume**: Always validate checkpoint integrity
- **Handle Corruption**: Gracefully handle corrupted checkpoints
- **Clean Up**: Remove checkpoints after successful completion

## See Also

- [README.md](README.md) - Quick reference guide
- [`validation/`](../validation/) - Validation & quality assurance

