# Logging Guide

> **Unified logging system** for consistent, informative output across Python and Bash

**Quick Reference:** [Error Handling](../error-handling-guide.md) | [Testing](../../development/testing/testing-guide.md) | [Troubleshooting](../troubleshooting/)

## Topic-Specific Guides

| Topic | Guide | Description |
|-------|-------|-------------|
| 🐍 **Python** | [python-logging.md](python-logging.md) | Python logging system |
| 🐚 **Bash** | [bash-logging.md](bash-logging.md) | Shell script logging |
| 📋 **Patterns** | [logging-patterns.md](logging-patterns.md) | Best practices, progress tracking |
| 📐 **Output design** | [output-design.md](output-design.md) | Visual contract — terminal vs file, summary schema, verbosity dial |

---

## Architecture

### One Shared Logging Layer, Used Two Ways

1. **Infrastructure logging** (`infrastructure.core.logging.utils`) — the single
   source of truth. `get_logger(name)` returns a standard `logging.Logger`
   configured with the template's handlers/formatters; module-level functions
   (`log_success`, `log_stage`, `log_progress`, `log_operation`, …) add the
   pipeline-specific conventions on top of that logger.
2. **Project usage** — `src/` modules import `get_logger` (and whichever
   convenience functions they need) directly from
   `infrastructure.core.logging.utils`. There is no separate
   `projects/*/src/utils/logging.py` shim; projects that want to avoid a hard
   `infrastructure.*` import at the top of `src/` (some exemplars keep `src/`
   infrastructure-independent) instead write a small local `get_logger()`
   wrapper that tries the infrastructure import and falls back to a bare
   `logging.getLogger(name)` on `ImportError` — see
   `projects/templates/template_code_project/src/_runtime.py` for a worked
   example of that pattern.

---

## Quick Start

### Everyday project usage

```python
from infrastructure.core.logging.utils import get_logger, log_success, log_progress, log_stage

log = get_logger(__name__)

# Basic logging (log is a standard logging.Logger)
log.info("Starting analysis")
log.error("Something went wrong")

# Convenience functions add pipeline conventions on top of the same logger
log_success("Analysis completed!", log)
log_progress(50, 100, "Processing data", log)
log_stage(2, 5, "Data Analysis", log)
```

### Context managers and decorators

```python
from infrastructure.core.logging.utils import get_logger, log_operation, log_timing, log_function_call

log = get_logger(__name__)

# Logs start/completion/failure automatically
with log_operation("Running simulation", log):
    run_simulation()

# Logs only elapsed time
with log_timing("Complex calculation", log):
    complex_calculation()

# Decorator: logs call/return/duration at DEBUG level
@log_function_call(log)
def process_batch(items):
    ...
```

### Resource monitoring

```python
from infrastructure.core.logging.utils import get_logger, log_live_resource_usage

log = get_logger(__name__)
log_live_resource_usage("After data processing", log)
```

### Shell Scripts

```bash
source scripts/shell/bash_utils.sh

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
| `NO_EMOJI` | true/false | false | Disable emoji in output (emoji is also auto-disabled whenever stdout isn't a TTY, e.g. piped/redirected output, regardless of this variable) |
| `STRUCTURED_LOGGING` | true/false | false | Enable JSON structured logging |
| `LOG_TERMINAL_VERBOSE` | true/false | false | Restore full `[ts] [LEVEL] name:` prefix on console (matches file format) — see [output-design.md](output-design.md) |

> Console handler is **prefix-less by default**; the file handler in `pipeline.log` always uses the full `[ts] [LEVEL] message` format. Set `LOG_TERMINAL_VERBOSE=1` to make the terminal match the file.

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

### Specialized Functions

These are free functions (not logger methods) — pass the logger explicitly, or
omit it to fall back to a module-named logger:

```python
from infrastructure.core.logging.utils import (
    log_success, log_header, log_progress, log_stage, log_substep,
)

# Success confirmation
log_success("Operation completed successfully", log)

# Section headers
log_header("=== ANALYSIS RESULTS ===", log)

# Progress indicators
log_progress(current=50, total=100, task="Processing data", logger=log)

# Pipeline stages
log_stage(stage_num=2, total_stages=5, stage_name="Data Analysis", logger=log)

# Sub-operations
log_substep("Loading dataset...", log)
log_substep("Running validation...", log)
```

### Context Managers

```python
from infrastructure.core.logging.utils import log_operation, log_timing

# Operation start/completion/failure logging
with log_operation("Data preprocessing", log):
    preprocess_data()

# Simple timing only
with log_timing("Complex calculation", log):
    complex_calculation()
```

---

## Advanced Features

### File Logging

```python
from infrastructure.core.logging.utils import setup_logger
from pathlib import Path

# Log to file in addition to console
log = setup_logger(__name__, log_file=Path("analysis.log"))
log.info("This goes to both console and file")
```

### Resource Monitoring

```python
from infrastructure.core.logging.utils import log_live_resource_usage

# Log current system resource usage
log_live_resource_usage("After memory-intensive operation", log)
```

Output includes process memory (RSS) and CPU percent. Requires `psutil`;
degrades to a DEBUG-level skip message when it isn't installed.

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
with log_operation("Data analysis pipeline", log):
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

## API Reference

`get_logger()` returns a standard `logging.Logger` — there is no custom
`ProjectLogger` class. `debug`/`info`/`warning`/`error`/`critical` are the
logger's own stdlib methods; everything pipeline-specific is a free function
in `infrastructure.core.logging.utils` that takes the logger as its last
argument (or defaults to a module-named logger when omitted).

```python
def get_logger(name: str) -> logging.Logger:
    """Return a logger configured with the template's standard handlers."""

def setup_logger(name: str, level: int | None = None, log_file: Path | str | None = None) -> logging.Logger:
    """Configure and return a logger with console handler and optional file handler."""

# Specialized functions (infrastructure.core.logging.utils / pipeline_logging)
def log_success(message: str, logger: logging.Logger | None = None) -> None: ...
def log_header(message: str, logger: logging.Logger | None = None) -> None: ...
def log_progress(current: int, total: int, task: str, logger: logging.Logger | None = None) -> None: ...
def log_stage(stage_num: int, total_stages: int, stage_name: str, logger: logging.Logger | None = None) -> None: ...
def log_substep(message: str, logger: logging.Logger | None = None) -> None: ...
def log_live_resource_usage(stage_name: str = "", logger: logging.Logger | None = None) -> None: ...

# Context managers / decorator
def log_operation(operation: str, logger: logging.Logger | None = None, level: int = logging.INFO,
                   min_duration_to_log: float = 0.1, log_completion: bool = True) -> ContextManager[None]: ...
def log_timing(label: str, logger: logging.Logger | None = None) -> ContextManager[None]: ...
def log_function_call(logger: logging.Logger | None = None) -> Callable: ...  # decorator factory
```

---

## Pipeline Logging

**During execution:** `projects/{project_name}/output/logs/pipeline.log`

**After copy stage (stage 9):** the same file is also under `output/{project_name}/logs/pipeline.log`
via [`copy_final_deliverables`](../../../infrastructure/core/files/operations.py).

Canonical format and verbosity dial: [output-design.md](output-design.md).

**View logs:**

```bash
# During or after a run (working tree)
cat projects/{project_name}/output/logs/pipeline.log
grep -i error projects/{project_name}/output/logs/pipeline.log

# After copy stage (final deliverables tree)
cat output/{project_name}/logs/pipeline.log
grep -i error output/{project_name}/logs/pipeline.log
```

---

## Fallback Behavior

There is no shared fallback shim — projects that want `src/` to stay
infrastructure-independent write a small local wrapper that tries the
infrastructure import and falls back to a bare stdlib logger on
`ImportError`. Real example:
[`template_code_project/src/_runtime.py`](../../../projects/templates/template_code_project/src/_runtime.py):

```python
def get_logger(module_name: str | None = None) -> logging.Logger:
    try:
        from infrastructure.core.logging.utils import get_logger as infra_get_logger

        return infra_get_logger(module_name or __name__)
    except ImportError:
        logger = logging.getLogger(module_name or __name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
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
    log_success("Success message", log)
    log_progress(50, 100, "Test progress", log)

    # Context managers should work
    with log_operation("Test operation", log):
        pass
```

---

## See Also

- [Error Handling Guide](../error-handling-guide.md) - Custom exception usage
- [Testing Guide](../../development/testing/testing-guide.md) - Testing with logging
- [API Reference](../../reference/api-reference.md) - Full API documentation
- [Infrastructure Logging](../../../infrastructure/core/AGENTS.md) - Infrastructure implementation
