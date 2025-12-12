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

## See Also

- [README.md](README.md) - Quick reference guide
- [`validation/`](../validation/) - Validation & quality assurance

