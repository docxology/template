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

# Log levels (aligned with unified logging module)
LOG_DEBUG=0
LOG_INFO=1
LOG_WARN=2
LOG_ERROR=3
LOG_LEVEL="${LOG_LEVEL:-$LOG_INFO}"

# Attempt to source unified logging library for consistency
LOGGING_SCRIPT="$REPO_ROOT/repo_utilities/logging.sh"
USING_UNIFIED_LOGGING=0
if [ -f "$LOGGING_SCRIPT" ]; then
    source "$LOGGING_SCRIPT" 2>/dev/null && USING_UNIFIED_LOGGING=1
fi

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
    local message=""
    # Handle both direct calls (with argument) and pipe usage (read from stdin)
    if [ $# -gt 0 ]; then
        message="$1"
    else
        # Read from stdin if no argument provided
        while IFS= read -r line || [ -n "$line" ]; do
            message="$line"
            if [ $USE_COLORS -eq 1 ]; then
                echo -e "${COLOR_DIM}   ${message}${COLOR_RESET}"
            else
                echo "   $message"
            fi
            if [ -n "$LOG_FILE" ]; then
                echo "   $message" >> "$LOG_FILE"
            fi
        done
        return 0
    fi
    
    # Handle direct call with argument
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

# Detect OS for installation instructions
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get >/dev/null 2>&1; then
            echo "debian"
        elif command -v yum >/dev/null 2>&1; then
            echo "rhel"
        elif command -v pacman >/dev/null 2>&1; then
            echo "arch"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Install system dependencies (if possible)
install_system_dependency() {
    local dep="$1"
    local os=$(detect_os)
    
    if [ $DRY_RUN -eq 1 ]; then
        log_info "[DRY RUN] Would attempt to install: $dep"
        return 0
    fi
    
    case "$os" in
        debian)
            log_info "Attempting to install $dep via apt-get..."
            if command -v sudo >/dev/null 2>&1; then
                sudo apt-get update -qq && sudo apt-get install -y "$dep" 2>&1 | log_dim || return 1
            else
                log_warn "sudo not available, cannot install $dep automatically"
                return 1
            fi
            ;;
        macos)
            log_info "Attempting to install $dep via brew..."
            if command -v brew >/dev/null 2>&1; then
                brew install "$dep" 2>&1 | log_dim || return 1
            else
                log_warn "brew not available, cannot install $dep automatically"
                return 1
            fi
            ;;
        *)
            log_warn "Automatic installation not supported on this OS"
            return 1
            ;;
    esac
}

# Check and install Python dependencies via uv
install_python_dependencies() {
    log_debug "Checking Python dependencies..."
    
    if [ $DRY_RUN -eq 1 ]; then
        log_info "[DRY RUN] Would install Python dependencies via uv"
        return 0
    fi
    
    # Check if uv is available
    if ! command -v uv >/dev/null 2>&1; then
        log_error "uv is required but not found"
        log_info "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
    
    # Check if pyproject.toml exists
    if [ ! -f "$REPO_ROOT/pyproject.toml" ]; then
        log_warn "pyproject.toml not found, skipping Python dependency installation"
        return 0
    fi
    
    log_info "Installing Python dependencies via uv..."
    log_dim "This may take a few minutes on first run..."
    
    # Run uv sync to install all dependencies
    if cd "$REPO_ROOT" && uv sync --quiet 2>&1 | log_dim; then
        log_success "Python dependencies installed"
        return 0
    else
        log_error "Failed to install Python dependencies"
        log_info "Try running manually: cd $REPO_ROOT && uv sync"
        return 1
    fi
}

# Check dependencies
check_dependencies() {
    log_debug "Checking dependencies..."
    
    local missing_system_deps=()
    local missing_tools=()
    local install_attempts=()
    
    # Check for required commands
    if ! command -v python3 >/dev/null 2>&1; then
        missing_system_deps+=("python3")
    else
        # Verify Python version
        local python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        local major_version=$(echo "$python_version" | cut -d. -f1)
        local minor_version=$(echo "$python_version" | cut -d. -f2)
        
        if [ "$major_version" -lt 3 ] || ([ "$major_version" -eq 3 ] && [ "$minor_version" -lt 10 ]); then
            log_error "Python 3.10+ required, found: $python_version"
            missing_system_deps+=("python3>=3.10")
        else
            log_debug "Python version OK: $python_version"
        fi
    fi
    
    if ! command -v uv >/dev/null 2>&1; then
        missing_tools+=("uv")
    else
        log_debug "uv found: $(uv --version 2>&1 | head -1)"
    fi
    
    # Check for PDF generation dependencies
    if ! command -v pandoc >/dev/null 2>&1; then
        missing_system_deps+=("pandoc")
    else
        log_debug "pandoc found: $(pandoc --version 2>&1 | head -1)"
    fi
    
    if ! command -v xelatex >/dev/null 2>&1; then
        missing_system_deps+=("texlive-xetex")
    else
        log_debug "xelatex found: $(xelatex --version 2>&1 | head -1)"
    fi
    
    # Attempt to install missing system dependencies (if not in dry-run)
    if [ ${#missing_system_deps[@]:-0} -gt 0 ]; then
        log_warn "Missing system dependencies: ${missing_system_deps[*]:-}"
        
        for dep in "${missing_system_deps[@]:-}"; do
            # Map dependency names to package names
            local package_name=""
            case "$dep" in
                python3|python3*)
                    package_name="python3"
                    ;;
                pandoc)
                    package_name="pandoc"
                    ;;
                texlive-xetex)
                    local os=$(detect_os)
                    case "$os" in
                        debian) package_name="texlive-xetex texlive-fonts-recommended" ;;
                        macos) package_name="basictex" ;;
                        *) package_name="texlive-xetex" ;;
                    esac
                    ;;
            esac
            
            if [ -n "$package_name" ]; then
                log_info "Attempting to install: $package_name"
                if install_system_dependency "$package_name"; then
                    install_attempts+=("$package_name: installed")
                    # Remove from missing list if installation succeeded
                    local new_missing_deps=()
                    for existing_dep in "${missing_system_deps[@]:-}"; do
                        if [ "$existing_dep" != "$dep" ]; then
                            new_missing_deps+=("$existing_dep")
                        fi
                    done
                    missing_system_deps=("${new_missing_deps[@]:-}")
                else
                    install_attempts+=("$package_name: failed")
                fi
            fi
        done
    fi
    
    # Show installation results
    if [ ${#install_attempts[@]:-0} -gt 0 ]; then
        echo ""
        for attempt in "${install_attempts[@]:-}"; do
            if [[ "$attempt" == *": installed" ]]; then
                log_success "$attempt"
            else
                log_warn "$attempt"
            fi
        done
        echo ""
    fi
    
    # Check again after installation attempts
    local still_missing=()
    for dep in "${missing_system_deps[@]:-}"; do
        case "$dep" in
            python3|python3*)
                if ! command -v python3 >/dev/null 2>&1; then
                    still_missing+=("python3")
                fi
                ;;
            pandoc)
                if ! command -v pandoc >/dev/null 2>&1; then
                    still_missing+=("pandoc")
                fi
                ;;
            texlive-xetex)
                if ! command -v xelatex >/dev/null 2>&1; then
                    still_missing+=("texlive-xetex")
                fi
                ;;
        esac
    done
    
    # Report missing dependencies with installation instructions
    if [ ${#still_missing[@]:-0} -gt 0 ] || [ ${#missing_tools[@]:-0} -gt 0 ]; then
        log_error "Missing required dependencies: ${still_missing[*]:-} ${missing_tools[*]:-}"
        echo ""
        log_info "Installation instructions:"
        
        local os=$(detect_os)
        for dep in "${still_missing[@]:-}" "${missing_tools[@]:-}"; do
            case "$dep" in
                python3)
                    case "$os" in
                        debian) log_info "  sudo apt-get update && sudo apt-get install -y python3 python3-pip" ;;
                        macos) log_info "  brew install python3" ;;
                        *) log_info "  Install Python 3.10+ from https://www.python.org/" ;;
                    esac
                    ;;
                uv)
                    log_info "  curl -LsSf https://astral.sh/uv/install.sh | sh"
                    log_info "  Or: pip install uv"
                    ;;
                pandoc)
                    case "$os" in
                        debian) log_info "  sudo apt-get install -y pandoc" ;;
                        macos) log_info "  brew install pandoc" ;;
                        *) log_info "  Install from https://pandoc.org/installing.html" ;;
                    esac
                    ;;
                texlive-xetex)
                    case "$os" in
                        debian) log_info "  sudo apt-get install -y texlive-xetex texlive-fonts-recommended" ;;
                        macos) log_info "  brew install --cask mactex  # Or: brew install basictex" ;;
                        *) log_info "  Install TeX Live with XeLaTeX support" ;;
                    esac
                    ;;
            esac
        done
        echo ""
        
        if [ $DRY_RUN -eq 0 ]; then
            log_error "Please install missing dependencies and try again"
            exit 1
        fi
    fi
    
    # Install Python dependencies
    if ! install_python_dependencies; then
        if [ $DRY_RUN -eq 0 ]; then
            log_error "Failed to install Python dependencies"
            exit 1
        fi
    fi
    
    # Check for required scripts
    local missing_scripts=()
    if [ ! -f "$REPO_ROOT/repo_utilities/clean_output.sh" ]; then
        missing_scripts+=("clean_output.sh")
    fi
    
    if [ ! -f "$REPO_ROOT/repo_utilities/render_pdf.sh" ]; then
        missing_scripts+=("render_pdf.sh")
    fi
    
    if [ ! -f "$REPO_ROOT/repo_utilities/validate_pdf_output.py" ]; then
        missing_scripts+=("validate_pdf_output.py")
    fi
    
    if [ ${#missing_scripts[@]} -gt 0 ]; then
        log_error "Missing required scripts: ${missing_scripts[*]}"
        log_error "Repository structure appears incomplete"
        exit 1
    fi
    
    # Verify Python packages can be imported
    log_debug "Verifying Python package imports..."
    if command -v uv >/dev/null 2>&1 && [ $DRY_RUN -eq 0 ]; then
        if cd "$REPO_ROOT" && uv run python3 -c "
import sys
try:
    import numpy
    import matplotlib
    import pypdf
    import reportlab
    import yaml
    print('All required Python packages available')
except ImportError as e:
    print(f'Missing package: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1 | log_dim; then
            log_debug "Python package verification passed"
        else
            log_warn "Some Python packages may be missing, but continuing..."
        fi
    fi
    
    log_success "All dependencies satisfied"
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
# BUILD STATISTICS
# =============================================================================

echo ""
log_info "Collecting build statistics..."

# Count generated files by type
PDF_COUNT=$(find "$REPO_ROOT/output/pdf" -name "*.pdf" 2>/dev/null | wc -l)
TEX_COUNT=$(find "$REPO_ROOT/output/tex" -name "*.tex" 2>/dev/null | wc -l)
FIGURE_COUNT=$(find "$REPO_ROOT/output/figures" -name "*.png" -o -name "*.pdf" 2>/dev/null | wc -l)
DATA_FILES=$(find "$REPO_ROOT/output/data" -type f 2>/dev/null | wc -l)
REPORT_COUNT=$(find "$REPO_ROOT/output/reports" -name "*.md" 2>/dev/null | wc -l)

echo ""
if [ $USE_COLORS -eq 1 ]; then
    echo -e "${COLOR_BOLD}📊 Build Summary:${COLOR_RESET}"
    echo -e "   ${COLOR_GREEN}PDF Documents:${COLOR_RESET} $PDF_COUNT (sections + combined)"
    echo -e "   ${COLOR_GREEN}LaTeX Files:${COLOR_RESET} $TEX_COUNT"
    echo -e "   ${COLOR_GREEN}Figures Generated:${COLOR_RESET} $FIGURE_COUNT"
    echo -e "   ${COLOR_GREEN}Data Files:${COLOR_RESET} $DATA_FILES"
    echo -e "   ${COLOR_GREEN}Reports Generated:${COLOR_RESET} $REPORT_COUNT"
else
    echo "Build Summary:"
    echo "   PDF Documents: $PDF_COUNT (sections + combined)"
    echo "   LaTeX Files: $TEX_COUNT"
    echo "   Figures Generated: $FIGURE_COUNT"
    echo "   Data Files: $DATA_FILES"
    echo "   Reports Generated: $REPORT_COUNT"
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
