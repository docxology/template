# Logging Patterns & Best Practices

> **Patterns, troubleshooting, and best practices** for the logging system

**Quick Reference:** [Main Logging Guide](../logging-guide.md) | [Python](python-logging.md) | [Bash](bash-logging.md)

---

## Progress Tracking

### Simple Progress

```python
from infrastructure.core.logging_utils import log_progress, log_progress_bar

# Simple progress
for i, file_path in enumerate(files, 1):
    log_progress(i, len(files), f"Processing {file_path.name}", logger)
    process_file(file_path)

# Progress bar with ETA
log_progress_bar(current=15, total=100, message="Processing files")
```

### Advanced Progress with ETA

```python
from infrastructure.core.progress import SubStageProgress, ProgressBar

# Sub-stage progress with EMA-based ETA
progress = SubStageProgress(
    total=10,
    stage_name="Rendering PDFs",
    use_ema=True  # Smoother ETA estimates
)

for i, file in enumerate(files, 1):
    progress.start_substage(i, file.name)
    render_file(file)
    progress.complete_substage()

# Get ETA with confidence intervals
realistic, optimistic, pessimistic = progress.get_eta_with_confidence()
```

### LLM Progress Tracking

```python
from infrastructure.core.progress import LLMProgressTracker

tracker = LLMProgressTracker(
    total_tokens=1000,
    task="Generating review",
    show_throughput=True  # Show tokens/sec
)

for chunk in llm_stream:
    tokens = estimate_tokens(chunk)
    tracker.update_tokens(tokens)
tracker.finish()
```

---

## ETA Calculation Methods

```python
from infrastructure.core.logging_utils import (
    calculate_eta,            # Simple linear ETA
    calculate_eta_ema,        # Exponential moving average
    calculate_eta_with_confidence  # With confidence intervals
)

# Simple linear
eta = calculate_eta(elapsed=30.0, completed=3, total=10)

# EMA (smoother)
eta = calculate_eta_ema(elapsed=30.0, completed=3, total=10, previous_eta=70.0, alpha=0.3)

# With confidence intervals
realistic, optimistic, pessimistic = calculate_eta_with_confidence(
    elapsed=30.0, completed=3, total=10, item_durations=[8.0, 12.0, 10.0]
)
```

---

## Best Practices

### Do's ✅

- **Use appropriate log levels** - DEBUG for diagnostics, INFO for progress
- **Include context** - Add file names, line numbers, values
- **Use context managers** - Automatic timing and error handling
- **Log exceptions with context** - Use `exc_info=True`
- **Consistent logger names** - Use `__name__`
- **Progress indicators** - Use `log_progress()` for long operations

### Don'ts ❌

- **Don't use print() for status** - Use logger instead
- **Don't log sensitive data** - Passwords, tokens
- **Don't log in tight loops** - Log at intervals
- **Don't mix logging systems** - Use unified logging
- **Don't duplicate messages** - Log once at right level

---

## When to Use print() vs logger

| Use logger for: | Use print() for: |
|-----------------|------------------|
| Status messages | Interactive CLI prompts |
| Error messages | CLI command results |
| Debug information | Test debugging |
| All production code | Documentation examples |

```python
# ✅ GOOD: Use logger for status
logger.info("Processing started")

# ✅ GOOD: Use print() for interactive prompts
print("Enter your choice [y/N]: ", end="")
choice = input()

# ❌ BAD: Don't use print() for status
print("Processing started")  # Should use logger.info()
```

---

## Troubleshooting

### Missing Log Files

**Symptoms:** No `pipeline.log` in output directory

**Solutions:**

```bash
# Check if log directory exists
ls -la projects/{project_name}/output/logs/

# Check archived logs
ls -la projects/{project_name}/output/logs/archive/
```

### No Log Output

**Solutions:**

1. Check log level: `LOG_LEVEL=0 python3 script.py`
2. Ensure logger is set up: `logger = get_logger(__name__)`
3. Check if using print() instead of logger

### Too Verbose

**Solutions:**

1. Increase log level: `export LOG_LEVEL=1` (or 2, 3)
2. Review DEBUG messages
3. Use appropriate levels

### No Emoji/Colors

- Expected in non-TTY environments
- Set `NO_EMOJI=1` explicitly
- Check terminal supports UTF-8

### Log File Not Created

1. Check directory exists
2. Check permissions
3. Use absolute paths

---

## Pipeline Logging

**Location:**

- During execution: `projects/{project_name}/output/logs/pipeline.log`
- After copy stage: `output/{project_name}/logs/pipeline.log`

**Content:**

- All bash script output (colors stripped in file)
- All Python script output
- Error messages and stack traces
- Progress indicators and ETAs
- Stage completion status

**Viewing Logs:**

```bash
cat output/code_project/logs/pipeline.log
grep -i error output/code_project/logs/pipeline.log
grep "Stage 5" output/code_project/logs/pipeline.log
```

---

**Related:** [Python Logging](python-logging.md) | [Bash Logging](bash-logging.md) | [Main Guide](../logging-guide.md)
