# Bash Logging Guide

> **Shell script logging** for consistent pipeline output

**Quick Reference:** [Main Logging Guide](../LOGGING_GUIDE.md) | [Python Logging](PYTHON_LOGGING.md)

---

## Quick Start

```bash
# Source the logging utilities
source scripts/bash_utils.sh

# Basic logging functions
log_success "Operation completed successfully"
log_error "An error occurred"
log_info "General information"
log_warning "Warning about potential issue"
```

**Output:**

```
✓ Operation completed successfully
✗ An error occurred
  General information
⚠ Warning about potential issue
```

---

## Structured Logging with Context

```bash
# Log with timestamp and context
log_with_context "INFO" "Processing started" "pipeline-stage-1"
log_with_context "ERROR" "File not found" "file-loader"

# Output:
# [2025-12-28 13:48:33] [INFO] [pipeline-stage-1] Processing started
# [2025-12-28 13:48:33] [ERROR] [file-loader] File not found
```

---

## Error Context and Troubleshooting

```bash
# Log errors with context and troubleshooting steps
log_error_with_context "Configuration file missing"

# Structured pipeline error logging
log_pipeline_error "PDF Rendering" "LaTeX compilation failed" 1 \
    "Check LaTeX installation: which xelatex" \
    "Verify manuscript files: ls project/manuscript/*.md" \
    "Check figure paths: ls projects/code_project/output/figures/"
```

---

## Resource Usage Logging

```bash
# Log stage completion with timing
log_resource_usage "Setup Environment" 45
log_resource_usage "PDF Rendering" 125 "memory: 2.1GB"

# Output:
# Stage 'Setup Environment' completed in 45s
# Stage 'PDF Rendering' completed in 2m 5s (memory: 2.1GB)
```

---

## Pipeline Progress Logging

```bash
# Stage logging with ETA and resource monitoring
log_stage_progress 2 "Project Tests" 10 "$pipeline_start" "$stage_start"

# Shows progress percentage, elapsed time, and ETA
# [2/10] Project Tests (20%)
#   Elapsed: 1m 30s | ETA: 5m 45s
#   Stage elapsed: 45s
```

---

## File Logging

```bash
# Enable file logging
export PIPELINE_LOG_FILE="output/logs/pipeline.log"

# All logging functions write to both terminal and file
# ANSI color codes are automatically stripped for log files
log_info "This appears in both terminal and log file"
```

---

## Error Handling Patterns

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

---

## Log File Format

```
===========================================================
  RESEARCH PROJECT PIPELINE
===========================================================

Repository: /Users/user/research-project
Python: Python 3.13.11
Log file: output/logs/pipeline_20251228_134833.log
Pipeline started: Sat Dec 28 13:48:33 PST 2025

[1/10] Clean Output Directories (10%)
  Elapsed: 0m 0s | ETA: 0m 0s
✓ Output directories cleaned

[2/10] Environment Setup (20%)
  Elapsed: 0m 5s | ETA: 0m 40s
✓ Environment setup complete

Pipeline completed successfully
Total duration: 5m 42s
```

---

## Best Practices

| Level | When to Use |
|-------|-------------|
| `log_success` | Successful operations |
| `log_info` | General progress information |
| `log_warning` | Non-critical issues |
| `log_error` | Failures requiring attention |

**Include Context:**

- Use `log_with_context` for operations with specific context
- Include function names and line numbers in errors
- Add troubleshooting steps for common failures

**Resource Monitoring:**

- Use `log_resource_usage` for long-running operations
- Include relevant metrics (memory, time, etc.)

---

**Related:** [Python Logging](PYTHON_LOGGING.md) | [Patterns](LOGGING_PATTERNS.md) | [Main Guide](../LOGGING_GUIDE.md)
