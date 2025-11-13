#!/bin/bash

# PDF Regeneration Script with Enhanced Logging and Robustness
# This script clears the output folder and fully regenerates all PDFs
# Supports: --help, --dry-run, --skip-validation, --verbose, --debug, --no-color, --log-file

set -euo pipefail
export LANG="${LANG:-C.UTF-8}"

# =============================================================================
# CONFIGURATION
# =============================================================================

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$(basename "$0")"

# Default values
DRY_RUN=0
SKIP_VALIDATION=0
LOG_FILE=""
USE_EMOJIS=1

# Log levels (aligned with render_pdf.sh)
LOG_DEBUG=0
LOG_INFO=1
LOG_WARN=2
LOG_ERROR=3
LOG_LEVEL="${LOG_LEVEL:-$LOG_INFO}"

# =============================================================================
# COLOR AND VISUAL DETECTION
# =============================================================================

# Check if colors should be used
USE_COLORS=1
if [ -n "${NO_COLOR:-}" ] || [ ! -t 1 ]; then
    USE_COLORS=0
fi

# Color codes (only used if USE_COLORS=1)
COLOR_RESET='\033[0m'
COLOR_BOLD='\033[1m'
COLOR_DIM='\033[2m'
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_BLUE='\033[0;34m'
COLOR_CYAN='\033[0;36m'

# Emoji fallbacks (empty if emojis disabled)
EMOJI_SUCCESS="✅"
EMOJI_INFO="ℹ️"
EMOJI_WARNING="⚠️"
EMOJI_ERROR="❌"
EMOJI_ROCKET="🚀"
EMOJI_SPARKLES="✨"
EMOJI_FOLDER="📁"
EMOJI_BOOK="📖"
EMOJI_CLEAN="🧹"

# Apply color/emoji settings
apply_color() {
    if [ $USE_COLORS -eq 1 ]; then
        echo -e "$1"
    else
        # Strip ANSI codes
        echo "$1" | sed 's/\x1b\[[0-9;]*m//g'
    fi
}

apply_emoji() {
    if [ $USE_EMOJIS -eq 1 ]; then
        echo "$1"
    else
        echo ""
    fi
}

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

# Core logging function with timestamp and level
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local level_name=""
    local color_code=""
    local emoji=""
    
    # Determine level name and color
    case "$level" in
        $LOG_DEBUG) level_name="DEBUG"; color_code="$COLOR_DIM"; emoji="" ;;
        $LOG_INFO)  level_name="INFO";  color_code="$COLOR_CYAN"; emoji=$(apply_emoji "$EMOJI_INFO") ;;
        $LOG_WARN)  level_name="WARN";  color_code="$COLOR_YELLOW"; emoji=$(apply_emoji "$EMOJI_WARNING") ;;
        $LOG_ERROR) level_name="ERROR"; color_code="$COLOR_RED"; emoji=$(apply_emoji "$EMOJI_ERROR") ;;
    esac
    
    # Format message
    local formatted_msg=""
    if [ $USE_COLORS -eq 1 ] && [ -n "$color_code" ]; then
        formatted_msg="${color_code}${emoji}${emoji:+ }[$timestamp] [$level_name]${COLOR_RESET} $message"
    else
        formatted_msg="[${timestamp}] [${level_name}] $message"
    fi
    
    # Output to console and/or log file
    if [ "$level" -ge "$LOG_LEVEL" ]; then
        if [ -n "$LOG_FILE" ]; then
            # Log file gets plain text
            echo "[${timestamp}] [${level_name}] $message" >> "$LOG_FILE"
        fi
        # Console gets formatted output
        if [ "$level" -ge $LOG_WARN ]; then
            echo "$formatted_msg" >&2
        else
            echo "$formatted_msg"
        fi
    fi
}

log_debug() { log $LOG_DEBUG "$@"; }
log_info() { log $LOG_INFO "$@"; }
log_warn() { log $LOG_WARN "$@"; }
log_error() { log $LOG_ERROR "$@"; }

# Specialized logging functions
log_header() {
    local message="$1"
    local emoji=$(apply_emoji "$EMOJI_ROCKET")
    if [ $USE_COLORS -eq 1 ]; then
        echo ""
        echo -e "${COLOR_BOLD}${COLOR_BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
        echo -e "${COLOR_BOLD}${COLOR_CYAN}${emoji}${emoji:+ }${message}${COLOR_RESET}"
        echo -e "${COLOR_BOLD}${COLOR_BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
        echo ""
    else
        echo ""
        echo "================================================================================"
        echo "$message"
        echo "================================================================================"
        echo ""
    fi
    if [ -n "$LOG_FILE" ]; then
        echo "" >> "$LOG_FILE"
        echo "================================================================================" >> "$LOG_FILE"
        echo "$message" >> "$LOG_FILE"
        echo "================================================================================" >> "$LOG_FILE"
        echo "" >> "$LOG_FILE"
    fi
}

log_step() {
    local step_num="$1"
    local step_title="$2"
    if [ $USE_COLORS -eq 1 ]; then
        echo ""
        echo -e "${COLOR_BOLD}${COLOR_BLUE}▶ Step ${step_num}:${COLOR_RESET} ${COLOR_BOLD}${step_title}${COLOR_RESET}"
    else
        echo ""
        echo "Step ${step_num}: ${step_title}"
    fi
    if [ -n "$LOG_FILE" ]; then
        echo "" >> "$LOG_FILE"
        echo "Step ${step_num}: ${step_title}" >> "$LOG_FILE"
    fi
}

log_success() {
    local message="$1"
    local emoji=$(apply_emoji "$EMOJI_SUCCESS")
    if [ $USE_COLORS -eq 1 ]; then
        echo -e "${COLOR_GREEN}${emoji}${emoji:+ }${message}${COLOR_RESET}"
    else
        echo "[SUCCESS] $message"
    fi
    if [ -n "$LOG_FILE" ]; then
        echo "[SUCCESS] $message" >> "$LOG_FILE"
    fi
}

log_dim() {
    local message="$1"
    if [ $USE_COLORS -eq 1 ]; then
        echo -e "${COLOR_DIM}   ${message}${COLOR_RESET}"
    else
        echo "   $message"
    fi
    if [ -n "$LOG_FILE" ]; then
        echo "   $message" >> "$LOG_FILE"
    fi
}

# Progress indicator
show_progress() {
    local current="$1"
    local total="$2"
    local task="$3"
    local percent=$((current * 100 / total))
    if [ $USE_COLORS -eq 1 ]; then
    echo -e "${COLOR_CYAN}[$current/$total - ${percent}%]${COLOR_RESET} $task"
    else
        echo "[$current/$total - ${percent}%] $task"
    fi
    if [ -n "$LOG_FILE" ]; then
        echo "[$current/$total - ${percent}%] $task" >> "$LOG_FILE"
    fi
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Show usage information
show_usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Regenerate all PDFs from scratch by cleaning outputs and rebuilding everything.

OPTIONS:
    --help              Show this help message and exit
    --dry-run           Show what would be executed without actually running
    --skip-validation   Skip PDF validation step (faster iteration)
    --verbose           Enable verbose logging (LOG_LEVEL=1)
    --debug             Enable debug logging (LOG_LEVEL=0)
    --no-color          Disable colored output
    --no-emoji          Disable emoji output
    --log-file FILE     Write logs to specified file in addition to console

ENVIRONMENT VARIABLES:
    LOG_LEVEL           Set log level (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR)
    NO_COLOR            Disable colored output (same as --no-color)
    REPO_ROOT           Override repository root directory

EXAMPLES:
    $SCRIPT_NAME
    $SCRIPT_NAME --verbose --log-file build.log
    $SCRIPT_NAME --skip-validation --no-color
    $SCRIPT_NAME --dry-run

EXIT CODES:
    0   Success - all steps completed successfully
    1   Error - script or dependency failure
    2   Validation warnings - PDFs generated but validation found issues
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_usage
                exit 0
                ;;
            --dry-run)
                DRY_RUN=1
                shift
                ;;
            --skip-validation)
                SKIP_VALIDATION=1
                shift
                ;;
            --verbose)
                LOG_LEVEL=$LOG_INFO
                shift
                ;;
            --debug)
                LOG_LEVEL=$LOG_DEBUG
                shift
                ;;
            --no-color)
                USE_COLORS=0
                shift
                ;;
            --no-emoji)
                USE_EMOJIS=0
                shift
                ;;
            --log-file)
                if [ -z "${2:-}" ]; then
                    log_error " --log-file requires a filename"
                    exit 1
                fi
                LOG_FILE="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Run with --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Initialize log file if specified
    if [ -n "$LOG_FILE" ]; then
        touch "$LOG_FILE" || {
            log_error "Cannot create log file: $LOG_FILE"
            exit 1
        }
        log_info "Logging to: $LOG_FILE"
    fi
}

# Check dependencies
check_dependencies() {
    log_debug "Checking dependencies..."
    
    local missing_deps=()
    
    # Check for required commands
    if ! command -v python3 >/dev/null 2>&1; then
        missing_deps+=("python3")
    fi
    
    if ! command -v uv >/dev/null 2>&1; then
        missing_deps+=("uv")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Install missing dependencies:"
        for dep in "${missing_deps[@]}"; do
            case "$dep" in
                python3) log_info "  - python3: sudo apt-get install python3" ;;
                uv) log_info "  - uv: See https://github.com/astral-sh/uv" ;;
            esac
        done
        exit 1
    fi
    
    # Check for required scripts
    if [ ! -f "$REPO_ROOT/repo_utilities/clean_output.sh" ]; then
        log_error "clean_output.sh not found: $REPO_ROOT/repo_utilities/clean_output.sh"
        exit 1
    fi
    
    if [ ! -f "$REPO_ROOT/repo_utilities/render_pdf.sh" ]; then
        log_error "render_pdf.sh not found: $REPO_ROOT/repo_utilities/render_pdf.sh"
        exit 1
    fi
    
    if [ ! -f "$REPO_ROOT/repo_utilities/validate_pdf_output.py" ]; then
        log_error "validate_pdf_output.py not found: $REPO_ROOT/repo_utilities/validate_pdf_output.py"
        exit 1
    fi
    
    log_debug "All dependencies satisfied"
}

# Filter output from render_pdf.sh (suppress harmless warnings)
filter_output() {
    grep -v "Deprecated: --highlight-style" | \
    grep -v "Deprecated: --listings" | \
    grep -v "Deprecated: --self-contained" | \
    grep -v "sed: 1:" | \
    grep -v "invalid command code" | \
    grep -v "^I found no" | \
    grep -v "There were.*error messages" | \
    grep -v "Could not convert TeX math" || true
}

# Cleanup handler
cleanup_on_exit() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Script interrupted or failed (exit code: $exit_code)"
        if [ -n "$LOG_FILE" ]; then
            log_info "Check log file for details: $LOG_FILE"
        fi
    fi
    # Any additional cleanup can go here
}

# Set up trap handlers
trap cleanup_on_exit EXIT INT TERM

# =============================================================================
# MAIN EXECUTION
# =============================================================================

# Parse command line arguments
parse_args "$@"

# Start timing
SCRIPT_START=$(date +%s)

# Show header
log_header "PDF REGENERATION FROM SCRATCH"

log_info "Repository: $REPO_ROOT"
log_info "Started: $(date '+%Y-%m-%d %H:%M:%S')"

if [ $DRY_RUN -eq 1 ]; then
    log_warn "DRY RUN MODE - No changes will be made"
fi

# Check dependencies
check_dependencies

# =============================================================================
# STEP 1: CLEANUP
# =============================================================================

log_step "1/3" "Cleaning Previous Outputs"

CLEAN_START=$(date +%s)
log_dim "Executing: $REPO_ROOT/repo_utilities/clean_output.sh"

if [ $DRY_RUN -eq 1 ]; then
    log_info "[DRY RUN] Would execute: $REPO_ROOT/repo_utilities/clean_output.sh"
    CLEAN_EXIT=0
else
    # Capture output but show errors if any
    CLEAN_OUTPUT=$("$REPO_ROOT/repo_utilities/clean_output.sh" 2>&1)
CLEAN_EXIT=$?
    
    if [ $CLEAN_EXIT -ne 0 ]; then
        log_error "Cleanup failed with exit code: $CLEAN_EXIT"
        log_error "Output: $CLEAN_OUTPUT"
        exit 1
    fi
fi

CLEAN_END=$(date +%s)
CLEAN_DURATION=$((CLEAN_END - CLEAN_START))

if [ $CLEAN_EXIT -eq 0 ]; then
    log_success "Output directory cleaned (${CLEAN_DURATION}s)"
else
    log_error "Cleanup failed"
    exit 1
fi

# =============================================================================
# STEP 2: REGENERATION
# =============================================================================

log_step "2/3" "Regenerating All PDFs"

RENDER_START=$(date +%s)
log_dim "Executing: $REPO_ROOT/repo_utilities/render_pdf.sh"
log_info "This may take 1-2 minutes depending on project complexity..."

if [ $DRY_RUN -eq 1 ]; then
    log_info "[DRY RUN] Would execute: $REPO_ROOT/repo_utilities/render_pdf.sh"
    RENDER_EXIT=0
else
    # Run render_pdf.sh with proper exit code capture
    # Use PIPESTATUS to get the actual exit code of render_pdf.sh
    set +e  # Temporarily disable exit on error to capture exit code
    "$REPO_ROOT/repo_utilities/render_pdf.sh" 2>&1 | filter_output
    RENDER_EXIT=${PIPESTATUS[0]}
    set -e  # Re-enable exit on error
    
    # If render_pdf.sh failed, show error context
    if [ $RENDER_EXIT -ne 0 ]; then
        log_error "PDF generation failed (exit code: $RENDER_EXIT)"
        log_info "Check the output above for error details"
        log_info "Common issues: missing dependencies, LaTeX errors, file permissions"
        exit 1
    fi
fi

RENDER_END=$(date +%s)
RENDER_DURATION=$((RENDER_END - RENDER_START))

if [ $RENDER_EXIT -eq 0 ]; then
    log_success "PDF generation complete (${RENDER_DURATION}s)"
    
    # Count generated files
    if [ -d "$REPO_ROOT/output/pdf" ]; then
        PDF_COUNT=$(find "$REPO_ROOT/output/pdf" -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')
        log_info "Generated ${PDF_COUNT} PDF files"
    fi
    
    if [ -d "$REPO_ROOT/output/figures" ]; then
        FIGURE_COUNT=$(find "$REPO_ROOT/output/figures" -name "*.png" 2>/dev/null | wc -l | tr -d ' ')
        log_info "Generated ${FIGURE_COUNT} figures"
    fi
    
    # Show file sizes if available
    if [ -f "$REPO_ROOT/output/pdf/project_combined.pdf" ]; then
        PDF_SIZE=$(du -h "$REPO_ROOT/output/pdf/project_combined.pdf" | cut -f1)
        log_debug "Main PDF size: $PDF_SIZE"
    fi
else
    log_error "PDF generation failed (exit code: $RENDER_EXIT)"
    exit 1
fi

# =============================================================================
# STEP 3: VALIDATION
# =============================================================================

if [ $SKIP_VALIDATION -eq 1 ]; then
    log_step "3/3" "Validating PDF Quality (SKIPPED)"
    log_warn "Validation skipped as requested"
    VALIDATION_EXIT=0
    VALIDATION_DURATION=0
else
log_step "3/3" "Validating PDF Quality"

VALIDATION_START=$(date +%s)
log_dim "Checking for rendering issues..."

    if [ $DRY_RUN -eq 1 ]; then
        log_info "[DRY RUN] Would execute: uv run python repo_utilities/validate_pdf_output.py --words 200"
    VALIDATION_EXIT=0
else
        # Run validation - capture both stdout and stderr
        set +e
        VALIDATION_OUTPUT=$(cd "$REPO_ROOT" && uv run python repo_utilities/validate_pdf_output.py --words 200 2>&1)
    VALIDATION_EXIT=$?
        set -e
        
        # Show validation output
        echo "$VALIDATION_OUTPUT"
fi

VALIDATION_END=$(date +%s)
VALIDATION_DURATION=$((VALIDATION_END - VALIDATION_START))

echo ""  # Add spacing

# Handle validation results with clear messaging
if [ $VALIDATION_EXIT -eq 0 ]; then
    log_success "PDF validation passed (${VALIDATION_DURATION}s)"
    log_dim "No unresolved references or citations found"
elif [ $VALIDATION_EXIT -eq 1 ]; then
    log_warning "PDF validation found rendering issues (${VALIDATION_DURATION}s)"
    log_dim "Review report above for unresolved references or citations"
    log_dim "Common issues: missing bibliography entries, undefined labels"
else
    log_error "PDF validation encountered an error (exit code: $VALIDATION_EXIT)"
        if [ -n "$VALIDATION_OUTPUT" ]; then
            log_debug "Validation output: $VALIDATION_OUTPUT"
        fi
    fi
fi

# =============================================================================
# SUMMARY
# =============================================================================

SCRIPT_END=$(date +%s)
TOTAL_DURATION=$((SCRIPT_END - SCRIPT_START))

log_header "REGENERATION COMPLETE"

log_info "Total time: ${TOTAL_DURATION}s (${CLEAN_DURATION}s + ${RENDER_DURATION}s + ${VALIDATION_DURATION}s)"
log_info "Completed: $(date '+%Y-%m-%d %H:%M:%S')"

echo ""
if [ $USE_COLORS -eq 1 ]; then
echo -e "${COLOR_BOLD}📁 Generated Outputs:${COLOR_RESET}"
    echo -e "   ${COLOR_GREEN}→${COLOR_RESET} PDFs:    ${COLOR_BOLD}$REPO_ROOT/output/pdf/${COLOR_RESET}"
    echo -e "   ${COLOR_GREEN}→${COLOR_RESET} Figures: ${COLOR_BOLD}$REPO_ROOT/output/figures/${COLOR_RESET}"
    echo -e "   ${COLOR_GREEN}→${COLOR_RESET} Data:    ${COLOR_BOLD}$REPO_ROOT/output/data/${COLOR_RESET}"
    echo -e "   ${COLOR_GREEN}→${COLOR_RESET} LaTeX:   ${COLOR_BOLD}$REPO_ROOT/output/tex/${COLOR_RESET}"
echo ""
echo -e "${COLOR_BOLD}📖 View Results:${COLOR_RESET}"
    echo -e "   ${COLOR_CYAN}•${COLOR_RESET} Main PDF:     ${COLOR_DIM}$REPO_ROOT/output/pdf/project_combined.pdf${COLOR_RESET}"
    echo -e "   ${COLOR_CYAN}•${COLOR_RESET} HTML version: ${COLOR_DIM}$REPO_ROOT/output/project_combined.html${COLOR_RESET}"
    echo -e "   ${COLOR_CYAN}•${COLOR_RESET} Open quickly: ${COLOR_DIM}$REPO_ROOT/repo_utilities/open_manuscript.sh${COLOR_RESET}"
else
    echo "Generated Outputs:"
    echo "   PDFs:    $REPO_ROOT/output/pdf/"
    echo "   Figures: $REPO_ROOT/output/figures/"
    echo "   Data:    $REPO_ROOT/output/data/"
    echo "   LaTeX:   $REPO_ROOT/output/tex/"
    echo ""
    echo "View Results:"
    echo "   Main PDF:     $REPO_ROOT/output/pdf/project_combined.pdf"
    echo "   HTML version: $REPO_ROOT/output/project_combined.html"
    echo "   Open quickly: $REPO_ROOT/repo_utilities/open_manuscript.sh"
fi

if [ -n "$LOG_FILE" ]; then
    echo ""
    log_info "Full log saved to: $LOG_FILE"
fi

# Exit with appropriate code
# 0 = success, 1 = error, 2 = validation warnings
if [ $VALIDATION_EXIT -eq 0 ]; then
    exit 0
elif [ $VALIDATION_EXIT -eq 1 ]; then
    exit 2  # Validation warnings
else
    exit 1  # Error
fi
