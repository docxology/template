# Logging Standards

## Unified Logging Module

All scripts use the unified logging library at `repo_utilities/logging.sh`.

### Import and Initialization

```bash
#!/bin/bash

# Source unified logging library
LOGGING_SCRIPT="$REPO_ROOT/repo_utilities/logging.sh"
if [ -f "$LOGGING_SCRIPT" ]; then
    source "$LOGGING_SCRIPT"
else
    # Fallback basic logging if library not available
    log_info() { echo "[INFO] $1"; }
    log_error() { echo "[ERROR] $1" >&2; }
fi
```

## Log Levels

Consistent across all scripts:

| Level | Value | Usage | Output |
|-------|-------|-------|--------|
| DEBUG | 0 | Detailed diagnostics | Verbose output |
| INFO | 1 | General information | Normal operation |
| WARN | 2 | Warnings | Potential issues |
| ERROR | 3 | Errors | Failures and problems |

### Set Log Level

```bash
# Via environment variable
export LOG_LEVEL=0  # DEBUG (most verbose)
export LOG_LEVEL=1  # INFO (default)
export LOG_LEVEL=2  # WARN
export LOG_LEVEL=3  # ERROR (least verbose)

# Or via command-line flags
./script.sh --verbose      # Sets LOG_LEVEL=0
./script.sh --debug        # Sets LOG_LEVEL=0
./script.sh --no-color     # Disable colors
```

## Logging Functions

### Basic Functions

```bash
# Info-level logging
log_info "Processing file $filename"

# Warning
log_warn "File not found, using default"

# Error
log_error "Failed to compile PDF"

# Debug (only shown with LOG_LEVEL=0)
log_debug "Current value: $value"
```

### Specialized Functions

```bash
# Section headers
log_header "PDF GENERATION PIPELINE"

# Step indicators
log_step "1/3" "Running Tests"

# Success messages
log_success "PDF generated successfully"

# Dimmed messages (for details)
log_dim "Processing 50 files..."

# Progress tracking
log_progress 15 100 "Compiling PDF"

# Timing information
log_timing "$start" "$end" "Compilation"
```

## Message Format

### Standard Format

```
[TIMESTAMP] [LEVEL] MESSAGE
```

Example output:
```
[2025-11-21 09:08:51] [INFO] PDF generation complete
[2025-11-21 09:08:51] [WARN] No output files found
[2025-11-21 09:08:51] [ERROR] Compilation failed
```

### With Colors and Emojis

When terminal supports it:
```
ℹ️ [2025-11-21 09:08:51] [INFO] PDF generation complete
⚠️ [2025-11-21 09:08:51] [WARN] No output files found
❌ [2025-11-21 09:08:51] [ERROR] Compilation failed
```

### Automatic Format Downgrade

- Colors disabled if not a TTY (pipe, redirect)
- NO_COLOR environment variable respected
- Plain text fallback available
- Always works in CI/CD

## Log File Support

### Save to File

```bash
# Enable log file
export LOG_FILE=build.log

# Or specify in script
LOG_FILE="build_$(date +%Y%m%d).log" ./render_pdf.sh
```

### Log File Contents

- Plain text format (no colors/emojis)
- Complete timestamp information
- All messages (including DEBUG)
- Useful for debugging and auditing

## Logging Best Practices

### 1. Clear Messages

```bash
# ✅ GOOD - Clear, specific
log_info "Compiling PDF: $pdf_name"
log_warn "Test coverage below 80%"

# ❌ BAD - Vague, unclear
log_info "Processing"
log_warn "Problem detected"
```

### 2. Include Context

```bash
# ✅ GOOD - Context provided
log_error "Failed to compile $tex_file: see $compile_log for details"

# ❌ BAD - No context
log_error "Compilation failed"
```

### 3. Appropriate Levels

```bash
# ✅ GOOD - Correct level
log_debug "Testing configuration..."  # Detail for debugging
log_info "Starting build pipeline"    # Important step
log_warn "Output directory exists"    # Potential issue
log_error "Failed to read config"     # Actual failure

# ❌ BAD - Wrong level
log_info "x=$value"                   # Too detailed (should be debug)
log_error "File not found"            # Expected condition (should be warn)
```

### 4. Progress Information

```bash
# ✅ GOOD - Track progress
for file in *.md; do
    current=$((current + 1))
    log_progress "$current" "$total" "Processing $file"
    
    log_step "1/3" "Compiling LaTeX"
    log_success "LaTeX compiled"
done

# Show timing
start=$(date +%s)
do_work
end=$(date +%s)
log_timing "$start" "$end" "Total time"
```

### 5. Error Context

```bash
# ✅ GOOD - Error with actionable advice
if ! xelatex -interaction=batchmode file.tex > "$compile_log" 2>&1; then
    log_error "LaTeX compilation failed"
    log_dim "Check $compile_log for details"
    log_info "Common issues: missing packages, invalid syntax"
    exit 1
fi

# ❌ BAD - Generic error
if ! xelatex file.tex; then
    log_error "Error"
    exit 1
fi
```

## Configuration

### Environment Variables

```bash
# Log level (0-3)
export LOG_LEVEL=1

# Log file path (optional)
export LOG_FILE=build.log

# Disable colors
export NO_COLOR=1

# Manual flags override these
./script.sh --debug        # LOG_LEVEL=0
./script.sh --no-color     # NO_COLOR=1
```

### Script Integration

```bash
#!/bin/bash
set -euo pipefail

# Source logging library first
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$REPO_ROOT/repo_utilities/logging.sh"

# Initialize if using log file
init_log_file  # Creates log file if LOG_FILE set

# Now use logging functions
log_info "Starting process"
log_execution_info "my_script.sh" "$REPO_ROOT"
```

## Log Output Examples

### Build Pipeline Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 PDF REGENERATION FROM SCRATCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️ [09:08:10] [INFO] Repository: /Users/4d/Documents/GitHub/template
ℹ️ [09:08:10] [INFO] Started: 2025-11-21 09:08:10

▶ Step 1/3: Cleaning Previous Outputs
   Executing: /Users/4d/Documents/GitHub/template/repo_utilities/clean_output.sh
✅ Output directory cleaned (2s)

▶ Step 2/3: Regenerating All PDFs
   Executing: /Users/4d/Documents/GitHub/template/repo_utilities/render_pdf.sh
ℹ️ [09:08:14] [INFO] This may take 1-2 minutes...
[15/100 - 15%] Compiling PDF
✅ PDF generation complete (104s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 REGENERATION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️ [09:09:59] [INFO] Total time: 109s
```

### Error Output

```
⚠️ [09:08:51] [WARN] First xelatex pass failed
   Check /Users/4d/Documents/GitHub/template/output/pdf/01_abstract_compile.log
   Common issues: undefined references, missing packages
❌ [09:08:51] [ERROR] Failed to build combined PDF
```

## Accessibility

### Features
- TTY detection (disable colors in pipes)
- NO_COLOR environment variable support
- Optional emoji output (`--no-emoji`)
- Graceful fallback to plain text
- Works in all environments (CI/CD, pipes, redirects)

### CI/CD Friendly

```bash
# In CI/CD pipeline
./build.sh --no-color --log-file build_log.txt

# Check results
if [ -f build_log.txt ]; then
    grep ERROR build_log.txt && exit 1
fi
```

## Troubleshooting Logging

### Colors Not Appearing

```bash
# TTY not detected, explicitly enable
./script.sh --color  # Not supported (use NO_COLOR=0)

# Or redirect to see colors
./script.sh 2>&1 | cat  # May lose colors
```

### Log File Not Created

```bash
# Check path is writable
touch "$LOG_FILE"  # Test write permission

# Use absolute path if relative doesn't work
export LOG_FILE="/tmp/build_$(date +%s).log"
```

### Missing Functions

```bash
# Ensure logging library is sourced
source repo_utilities/logging.sh

# Verify functions exported
type log_info  # Should show function definition
```

## See Also

- [repo_utilities/logging.sh](../repo_utilities/logging.sh) - Library implementation
- [build_pipeline.md](build_pipeline.md) - Build logging examples
- [generate_pdf_from_scratch.sh](../generate_pdf_from_scratch.sh) - Full logging usage
- [../repo_utilities/render_pdf.sh](../repo_utilities/render_pdf.sh) - Script logging

