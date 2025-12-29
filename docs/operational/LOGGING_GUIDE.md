# Logging Guide

> **Unified Python logging system** for consistent, informative output across all scripts

**Quick Reference:** [Error Handling Guide](../operational/ERROR_HANDLING_GUIDE.md) | [Testing Guide](../development/TESTING_GUIDE.md) | [Troubleshooting](../operational/TROUBLESHOOTING_GUIDE.md)

This guide explains how to use the unified logging system in the Research Project Template. The logging system provides consistent formatting, log levels, and integration across Python and bash scripts.

## Overview

The template uses a unified Python logging system:
- **Python logging** (`infrastructure/core/logging_utils.py`) - For all scripts

The logging system provides:
- Consistent log levels (DEBUG, INFO, WARN, ERROR)
- Structured timestamp formats
- Environment-based configuration
- Emoji support (when appropriate)
- TTY-aware color output

## Quick Start

### Python Scripts

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

### Shell Scripts

The template includes comprehensive bash script logging through `scripts/bash_utils.sh` and the `run.sh` orchestrator. Bash scripts use structured logging functions for consistent output and error handling.

#### Basic Logging Functions

```bash
# Source the logging utilities
source scripts/bash_utils.sh

# Basic logging functions
log_success "Operation completed successfully"
log_error "An error occurred"
log_info "General information"
log_warning "Warning about potential issue"

# Example output:
# ✓ Operation completed successfully
# ✗ An error occurred
#   General information
# ⚠ Warning about potential issue
```

#### Structured Logging with Context

```bash
# Log with timestamp and context
log_with_context "INFO" "Processing started" "pipeline-stage-1"
log_with_context "ERROR" "File not found" "file-loader"

# Example output:
# [2025-12-28 13:48:33] [INFO] [pipeline-stage-1] Processing started
# [2025-12-28 13:48:33] [ERROR] [file-loader] File not found
```

#### Error Context and Troubleshooting

```bash
# Log errors with context and troubleshooting steps
log_error_with_context "Configuration file missing"

# Or with custom context
log_error_with_context "Database connection failed" "db-connection"

# Structured pipeline error logging
log_pipeline_error "PDF Rendering" "LaTeX compilation failed" 1 \
    "Check LaTeX installation: which xelatex" \
    "Verify manuscript files: ls project/manuscript/*.md" \
    "Check figure paths: ls projects/project/output/figures/"
```

#### Resource Usage Logging

```bash
# Log stage completion with timing
log_resource_usage "Setup Environment" 45
log_resource_usage "PDF Rendering" 125 "memory: 2.1GB"

# Example output:
# Stage 'Setup Environment' completed in 45s
# Stage 'PDF Rendering' completed in 2m 5s (memory: 2.1GB)
```

#### Pipeline Progress Logging

```bash
# Enhanced stage logging with ETA and resource monitoring
log_stage_progress 2 "Project Tests" 9 "$pipeline_start" "$stage_start"

# Shows progress percentage, elapsed time, and ETA
# [2/9] Project Tests (22% complete)
#   Elapsed: 1m 30s | ETA: 5m 45s
#   Stage elapsed: 45s
```

#### File Logging

Bash scripts automatically log to files when `PIPELINE_LOG_FILE` is set:

```bash
# Enable file logging
export PIPELINE_LOG_FILE="output/logs/pipeline.log"

# All logging functions write to both terminal and file
# ANSI color codes are automatically stripped for log files
log_info "This appears in both terminal and log file"
```

#### Error Handling Patterns

```bash
# Standard error handling with troubleshooting
if ! python3 scripts/03_render_pdf.py; then
    log_pipeline_error "PDF Rendering" "PDF generation failed" $? \
        "Check LaTeX installation" \
        "Verify manuscript files exist" \
        "Check figure references"
    return 1
fi

# Success logging with resource tracking
local stage_end=$(date +%s)
local duration=$((stage_end - stage_start))
log_resource_usage "PDF Rendering" "$duration"
```

#### Log File Format

Pipeline logs include comprehensive information:

```
===========================================================
  COMPLETE RESEARCH PROJECT PIPELINE
===========================================================

Repository: /Users/user/research-project
Python: Python 3.13.11
Log file: output/logs/pipeline_20251228_134833.log
Pipeline started: Sat Dec 28 13:48:33 PST 2025

[1/9] Setup Environment (11% complete)
  Elapsed: 0m 5s | ETA: 0m 40s
✓ Environment setup complete

[2/9] Infrastructure Tests (22% complete)
  Elapsed: 0m 25s | ETA: 1m 25s
✓ Infrastructure tests passed

[... continues for all stages ...]

Pipeline completed successfully
Total duration: 5m 42s
```

#### Testing Bash Script Logging

Bash script logging is tested in `tests/integration/test_logging.py` and `tests/integration/test_bash_utils.sh`:

```bash
# Run bash logging tests
bash tests/integration/test_bash_utils.sh

# Run Python logging integration tests
python -m pytest tests/integration/test_logging.py -v
```

#### Best Practices

**Use Appropriate Log Levels:**
- `log_success`: Successful operations
- `log_info`: General progress information
- `log_warning`: Non-critical issues
- `log_error`: Failures requiring attention

**Include Context:**
- Use `log_with_context` for operations with specific context
- Include function names and line numbers in errors
- Add troubleshooting steps for common failures

**Resource Monitoring:**
- Use `log_resource_usage` for long-running operations
- Include relevant metrics (memory, time, etc.)
- Enable automatic resource tracking in pipelines

**Error Recovery:**
- Use `log_pipeline_error` for structured error reporting
- Provide actionable troubleshooting steps
- Include relevant file paths and commands

## Python Logging System

### Basic Usage

```python
from infrastructure.core.logging_utils import get_logger, log_operation, log_success

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

### Structured Logging (JSON Format)

For machine-readable logs, enable structured logging:

```bash
# Enable JSON logging
export STRUCTURED_LOGGING=true
python3 scripts/run_all.py
```

This outputs logs in JSON format for programmatic parsing:
```json
{"timestamp": "2025-12-04T14:01:30", "level": "INFO", "logger": "scripts.run_all", "message": "Starting pipeline"}
```

### Context Managers

Use context managers for automatic operation tracking:

```python
from infrastructure.core.logging_utils import log_operation, log_timing, log_operation_silent, log_with_spinner

# Log operation start and completion
# Completion message suppressed for operations < 0.1s
with log_operation("Processing data", logger):
    process_data()
    # Automatically logs start, completion (if duration >= 0.1s), and duration

# Silent operation (no completion message)
with log_operation_silent("Quick check", logger):
    quick_check()
    # Only logs start, no completion message

# Operation with spinner (for long-running operations)
with log_with_spinner("Loading model...", logger):
    load_model()
    # Shows animated spinner during operation
```

### Function Decorators

Decorate functions for automatic call logging:

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

### Pipeline Terminal Output Logging

The pipeline automatically captures all terminal output to log files:

**Location**: `project/output/logs/` (during execution) → `output/logs/` (after copy stage)

**Naming**: `pipeline_YYYYMMDD_HHMMSS.log` (e.g., `pipeline_20251205_074830.log`)

**Content**: Complete terminal output including:
- All bash script output (ANSI colors stripped in file, preserved in terminal)
- All Python script output
- Error messages and stack traces
- Progress indicators and ETAs
- Stage completion status

**Usage**:
```bash
# Run pipeline - log file is automatically created
./run.sh --pipeline

# Log file location is displayed in pipeline summary
# Example: output/logs/pipeline_20251205_074830.log
```

**Viewing Logs**:
```bash
# View latest log file
ls -t output/logs/*.log | head -1 | xargs cat

# Search for errors in logs
grep -i error output/logs/pipeline_*.log

# View logs from specific stage
grep "Stage 5" output/logs/pipeline_*.log
```

**Log File Management**:
- Old log files are automatically archived to `output/logs/archive/` before cleanup
- Log files are preserved during pipeline cleanup (not deleted)
- Log files are copied to root `output/logs/` during the copy outputs stage

### Log Files (Python Scripts)

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

- **Don't use print() for status messages** - Use logger instead (see exceptions below)
- **Don't log sensitive data** - Passwords, tokens, personal information
- **Don't log in tight loops** - Log at appropriate intervals
- **Don't mix logging systems** - Use unified logging consistently
- **Don't ignore log levels** - Respect LOG_LEVEL environment variable
- **Don't duplicate messages** - Log once at the right level

### When to Use print() vs logger

**Use logger for:**
- Status messages and progress updates
- Error messages and warnings
- Debug information
- All production code output

**Use print() for (acceptable exceptions):**
- Interactive CLI prompts (user input requests)
- CLI command results (user-facing output in CLI tools)
- Test debugging output (when tests fail)
- Documentation examples (in docstrings, not executed code)

**Examples:**

```python
# ✅ GOOD: Use logger for status
logger.info("Processing started")
logger.error("Operation failed", exc_info=True)

# ✅ GOOD: Use print() for interactive prompts
print("Enter your choice [y/N]: ", end="")
choice = input()

# ✅ GOOD: Use print() for CLI output
print(f"Result: {result}")  # In CLI tool main()

# ❌ BAD: Don't use print() for status in production code
print("Processing started")  # Should use logger.info()
```

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

The template provides multiple progress tracking utilities for different use cases:

#### Simple Progress Tracking

```python
from infrastructure.core.logging_utils import log_progress, log_progress_bar, StreamingProgress, Spinner

# Simple progress
def process_files(files: list[Path]) -> None:
    """Process multiple files with progress reporting."""
    logger.info(f"Processing {len(files)} files")
    
    for i, file_path in enumerate(files, 1):
        log_progress(i, len(files), f"Processing {file_path.name}", logger)
        process_file(file_path)
    
    log_success(f"Processed all {len(files)} files", logger)

# Progress bar with ETA
log_progress_bar(current=15, total=100, message="Processing files")

# Streaming progress (for real-time updates)
progress = StreamingProgress(total=1000, message="Generating tokens")
for chunk in stream:
    progress.update(len(chunk))
progress.finish("Generation complete")

# Spinner for long-running operations
with log_with_spinner("Loading model...", logger):
    load_model()
```

#### Advanced Progress Tracking with ETA

The template includes enhanced progress tracking with exponential moving average (EMA) for more accurate ETA estimates:

```python
from infrastructure.core.progress import SubStageProgress, ProgressBar, LLMProgressTracker

# Sub-stage progress with EMA-based ETA
progress = SubStageProgress(
    total=10,
    stage_name="Rendering PDFs",
    use_ema=True  # Use EMA for smoother ETA estimates
)

for i, file in enumerate(files, 1):
    progress.start_substage(i, file.name)
    render_file(file)
    progress.complete_substage()
    
    # Log progress with ETA every few items
    if i % 3 == 0:
        progress.log_progress()

# Get ETA with confidence intervals
realistic, optimistic, pessimistic = progress.get_eta_with_confidence()
logger.info(f"ETA: {format_duration(realistic)} (range: {format_duration(optimistic)} - {format_duration(pessimistic)})")

# Progress bar with EMA
bar = ProgressBar(
    total=100,
    task="Processing items",
    use_ema=True  # Smoother ETA estimates
)
for i in range(100):
    bar.update(i + 1)
bar.finish()

# LLM-specific progress tracking (token-based)
tracker = LLMProgressTracker(
    total_tokens=1000,  # Optional: None for unknown total
    task="Generating review",
    show_throughput=True  # Show tokens/sec
)

for chunk in llm_stream:
    tokens = estimate_tokens(chunk)
    tracker.update_tokens(tokens)
tracker.finish()
```

#### ETA Calculation Methods

The template provides three ETA calculation methods:

```python
from infrastructure.core.logging_utils import (
    calculate_eta,           # Simple linear ETA
    calculate_eta_ema,        # Exponential moving average
    calculate_eta_with_confidence  # With confidence intervals
)

# Simple linear (fast, but can be inaccurate with variable durations)
eta = calculate_eta(elapsed=30.0, completed=3, total=10)

# EMA (smoother, adapts to changing performance)
eta = calculate_eta_ema(
    elapsed=30.0,
    completed=3,
    total=10,
    previous_eta=70.0,  # Previous estimate
    alpha=0.3  # Smoothing factor (0-1, higher = more responsive)
)

# With confidence intervals (optimistic/pessimistic)
realistic, optimistic, pessimistic = calculate_eta_with_confidence(
    elapsed=30.0,
    completed=3,
    total=10,
    item_durations=[8.0, 12.0, 10.0]  # Optional: actual durations for accuracy
)
```

#### Progress Display Best Practices

1. **Use SubStageProgress for multi-step operations** - Provides better ETA tracking
2. **Enable EMA for variable-duration operations** - More accurate estimates
3. **Log progress periodically** - Don't log on every iteration for fast operations
4. **Use LLMProgressTracker for token generation** - Specialized for LLM operations
5. **Show throughput when relevant** - tokens/sec, items/sec, etc.

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

- [Error Handling Guide](../operational/ERROR_HANDLING_GUIDE.md) - Custom exception usage
- [Testing Guide](../development/TESTING_GUIDE.md) - Testing with logging
- [Troubleshooting](../operational/TROUBLESHOOTING_GUIDE.md) - Common issues
- [Build System](../operational/BUILD_SYSTEM.md) - Pipeline logging
- [API Reference](../reference/API_REFERENCE.md) - Full API documentation

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









