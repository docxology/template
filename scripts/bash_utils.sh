#!/usr/bin/env bash
################################################################################
# Shared Bash Utilities
#
# Common utilities for run.sh:
# - Color codes and formatting
# - Logging functions
# - Utility functions (duration formatting, choice parsing, etc.)
# - Environment setup
#
# This file is sourced by run.sh
################################################################################

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# Get script directory and repo root
# When sourced, BASH_SOURCE[1] is the script that sourced this file
# BASH_SOURCE[0] is this file (bash_utils.sh)
sourcing_script="${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}"
SCRIPT_DIR="$(cd "$(dirname "$sourcing_script")" && pwd)"

# Determine repo root: if script is in root, use it; if in scripts/, go up one level
if [[ "$(basename "$SCRIPT_DIR")" == "scripts" ]]; then
    REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    REPO_ROOT="$SCRIPT_DIR"
fi

# Export for subprocess use
export PROJECT_ROOT="$REPO_ROOT"
# PYTHONPATH will be set dynamically based on project name in scripts

# ============================================================================
# Logging Functions
# ============================================================================

log_header() {
    local message="$1"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  ${message}${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

log_stage() {
    # Display stage header with progress percentage and ETA.
    # Args:
    #   $1: Stage number (1-indexed)
    #   $2: Stage name
    #   $3: Total number of stages
    #   $4: Pipeline start time (optional, for ETA calculation)
    local stage_num="$1"
    local stage_name="$2"
    local total_stages="$3"
    local pipeline_start="${4:-}"
    
    echo
    local percentage=$((stage_num * 100 / total_stages))
    echo -e "${YELLOW}[${stage_num}/${total_stages}] ${stage_name} (${percentage}% complete)${NC}"
    
    # Calculate ETA if pipeline start time provided
    if [[ -n "$pipeline_start" ]]; then
        local current_time=$(date +%s)
        local elapsed=$((current_time - pipeline_start))
        if [[ $elapsed -gt 0 ]] && [[ $stage_num -gt 0 ]]; then
            local avg_time_per_stage=$((elapsed / stage_num))
            local remaining_stages=$((total_stages - stage_num))
            local eta=$((avg_time_per_stage * remaining_stages))
            echo -e "${CYAN}  Elapsed: $(format_duration "$elapsed") | ETA: $(format_duration "$eta")${NC}"
        fi
    fi
    
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_stage_start() {
    # Log stage start with consistent formatting.
    local stage_num="$1"
    local stage_name="$2"
    local total_stages="$3"
    echo -e "${BLUE}▶ Starting Stage ${stage_num}/${total_stages}: ${stage_name}${NC}"
}

log_stage_end() {
    # Log stage completion with consistent formatting.
    local stage_num="$1"
    local stage_name="$2"
    local duration="$3"
    echo -e "${GREEN}✓ Completed Stage ${stage_num}: ${stage_name} (${duration})${NC}"
}

log_success() {
    local message="$1"
    echo -e "${GREEN}✓${NC} ${message}"
}

log_error() {
    local message="$1"
    echo -e "${RED}✗${NC} ${message}"
}

log_info() {
    local message="$1"
    echo "  ${message}"
}

log_warning() {
    local message="$1"
    echo -e "${YELLOW}⚠${NC} ${message}"
}

# ============================================================================
# File Logging Functions
# ============================================================================

# Function to log to both terminal and log file
log_to_file() {
    local message="$1"
    local log_file="${PIPELINE_LOG_FILE:-}"
    
    # Always log to terminal
    echo "$message"
    
    # Also log to file if log file is set (strip ANSI codes)
    if [[ -n "$log_file" ]]; then
        echo "$message" | sed 's/\x1b\[[0-9;]*m//g' >> "$log_file" 2>/dev/null || true
    fi
}

# Wrapper functions to log bash output to file
log_header_to_file() {
    local message="$1"
    local log_file="${PIPELINE_LOG_FILE:-}"
    log_header "$message"
    if [[ -n "$log_file" ]]; then
        {
            echo "============================================================"
            echo "  $message"
            echo "============================================================"
        } >> "$log_file" 2>/dev/null || true
    fi
}

log_info_to_file() {
    local message="$1"
    local log_file="${PIPELINE_LOG_FILE:-}"
    log_info "$message"
    if [[ -n "$log_file" ]]; then
        echo "  $message" >> "$log_file" 2>/dev/null || true
    fi
}

log_success_to_file() {
    local message="$1"
    local log_file="${PIPELINE_LOG_FILE:-}"
    log_success "$message"
    if [[ -n "$log_file" ]]; then
        echo "✓ $message" >> "$log_file" 2>/dev/null || true
    fi
}

log_error_to_file() {
    local message="$1"
    local log_file="${PIPELINE_LOG_FILE:-}"
    log_error "$message"
    if [[ -n "$log_file" ]]; then
        echo "✗ $message" >> "$log_file" 2>/dev/null || true
    fi
}

log_warning_to_file() {
    local message="$1"
    local log_file="${PIPELINE_LOG_FILE:-}"
    log_warning "$message"
    if [[ -n "$log_file" ]]; then
        echo "⚠ $message" >> "$log_file" 2>/dev/null || true
    fi
}

# ============================================================================
# Structured Logging Functions
# ============================================================================

log_with_context() {
    # Log message with timestamp and optional context.
    # Args:
    #   $1: Log level (INFO, WARN, ERROR, SUCCESS)
    #   $2: Message
    #   $3: Optional context (function name, stage, etc.)
    local level="$1"
    local message="$2"
    local context="${3:-}"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")

    # Format: [TIMESTAMP] [LEVEL] [CONTEXT] message
    local formatted_msg="[$timestamp] [$level]"
    if [[ -n "$context" ]]; then
        formatted_msg="$formatted_msg [$context]"
    fi
    formatted_msg="$formatted_msg $message"

    echo "$formatted_msg"
}

log_error_with_context() {
    # Log error with context information (function name and line number).
    # Args:
    #   $1: Error message
    #   $2: Optional context override
    local message="$1"
    local context_override="${2:-}"

    if [[ -n "$context_override" ]]; then
        local context="$context_override"
    else
        local function="${FUNCNAME[1]:-unknown}"
        local line="${BASH_LINENO[0]:-?}"
        local context="$function:$line"
    fi

    log_error "$message (in $context)"
}

log_troubleshooting() {
    # Log troubleshooting information for common errors.
    # Args:
    #   $1: Error type/category
    #   $2: Primary error message
    #   $3+: Troubleshooting steps (variable arguments)
    local error_type="$1"
    local primary_message="$2"
    shift 2

    log_error "$primary_message"

    if [[ $# -gt 0 ]]; then
        log_info "Troubleshooting steps:"
        local step_num=1
        for step in "$@"; do
            log_info "  $step_num. $step"
            ((step_num++))
        done
    fi
}

log_pipeline_error() {
    # Log pipeline stage errors with structured troubleshooting.
    # Args:
    #   $1: Stage name
    #   $2: Error message
    #   $3: Exit code
    #   $4+: Troubleshooting steps
    local stage_name="$1"
    local error_message="$2"
    local exit_code="$3"
    shift 3

    log_error "Pipeline failed at Stage: $stage_name (exit code: $exit_code)"
    log_info "Error: $error_message"

    if [[ $# -gt 0 ]]; then
        log_info "Troubleshooting:"
        local step_num=1
        for step in "$@"; do
            log_info "  $step_num. $step"
            ((step_num++))
        done
    fi
}

log_resource_usage() {
    # Log resource usage information for monitoring.
    # Args:
    #   $1: Stage name
    #   $2: Duration in seconds
    #   $3: Optional additional metrics
    local stage_name="$1"
    local duration="$2"
    local additional="${3:-}"

    local formatted_duration=$(format_duration "$duration")
    local message="Stage '$stage_name' completed in $formatted_duration"

    if [[ -n "$additional" ]]; then
        message="$message ($additional)"
    fi

    log_with_context "INFO" "$message" "resource-monitor"
}

log_stage_progress() {
    # Enhanced log_stage with resource monitoring.
    # Args:
    #   $1: Stage number (1-indexed)
    #   $2: Stage name
    #   $3: Total number of stages
    #   $4: Pipeline start time (optional, for ETA calculation)
    #   $5: Current stage start time (optional, for resource tracking)
    local stage_num="$1"
    local stage_name="$2"
    local total_stages="$3"
    local pipeline_start="${4:-}"
    local stage_start="${5:-}"

    # Call original log_stage function
    log_stage "$stage_num" "$stage_name" "$total_stages" "$pipeline_start"

    # Add resource tracking if stage start time provided
    if [[ -n "$stage_start" ]]; then
        local current_time=$(date +%s)
        local stage_elapsed=$((current_time - stage_start))
        local formatted_elapsed=$(format_duration "$stage_elapsed")
        echo -e "${CYAN}  Stage elapsed: ${formatted_elapsed}${NC}"
    fi
}

# ============================================================================
# Enhanced Project Context Logging Functions
# ============================================================================

log_project_context() {
    # Display current project context with paths
    # Args:
    #   $1: Project name
    #   $2: Stage or operation name (optional)
    local project_name="$1"
    local operation="${2:-}"

    if [[ -n "$operation" ]]; then
        log_info "Project: $project_name | Operation: $operation"
    else
        log_info "Project: $project_name"
    fi
    log_info "  Manuscript: $REPO_ROOT/projects/$project_name/manuscript/"
    log_info "  Output: $REPO_ROOT/projects/$project_name/output/"
}

log_stage_with_project() {
    # Enhanced log_stage that includes project context
    # Args:
    #   $1: Stage number (1-indexed)
    #   $2: Stage name
    #   $3: Total number of stages
    #   $4: Project name
    #   $5: Pipeline start time (optional)
    local stage_num="$1"
    local stage_name="$2"
    local total_stages="$3"
    local project_name="$4"
    local pipeline_start="${5:-}"

    echo
    local percentage=$((stage_num * 100 / total_stages))
    echo -e "${YELLOW}[${stage_num}/${total_stages}] ${stage_name} (${percentage}% complete)${NC}"
    echo -e "${CYAN}  Project: ${project_name}${NC}"

    # ETA calculation (existing logic)
    if [[ -n "$pipeline_start" ]]; then
        local current_time=$(date +%s)
        local elapsed=$((current_time - pipeline_start))
        if [[ $elapsed -gt 0 ]] && [[ $stage_num -gt 0 ]]; then
            local avg_time_per_stage=$((elapsed / stage_num))
            local remaining_stages=$((total_stages - stage_num))
            local eta=$((avg_time_per_stage * remaining_stages))
            echo -e "${CYAN}  Elapsed: $(format_duration "$elapsed") | ETA: $(format_duration "$eta")${NC}"
        fi
    fi

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_output_path() {
    # Log where outputs are being written
    # Args:
    #   $1: Description (e.g., "PDF", "Figures")
    #   $2: Path to output directory or file
    local description="$1"
    local output_path="$2"
    log_info "$description → $output_path"
}

# ============================================================================
# Utility Functions
# ============================================================================

get_elapsed_time() {
    local start_time="$1"
    local end_time="$2"
    echo $((end_time - start_time))
}

format_duration() {
    local seconds="$1"
    if (( seconds < 60 )); then
        echo "${seconds}s"
    else
        local minutes=$((seconds / 60))
        local secs=$((seconds % 60))
        echo "${minutes}m ${secs}s"
    fi
}

press_enter_to_continue() {
    echo
    echo -e "${CYAN}Press Enter to return to menu...${NC}"
    read -r
}

format_file_size() {
    # Convert bytes to human-readable format
    local bytes="$1"
    if (( bytes < 1024 )); then
        echo "${bytes}B"
    elif (( bytes < 1048576 )); then
        echo "$((bytes / 1024))KB"
    elif (( bytes < 1073741824 )); then
        echo "$((bytes / 1048576))MB"
    else
        echo "$((bytes / 1073741824))GB"
    fi
}

# Parsed shorthand choices holder (for sequences like "0123" or "345")
SHORTHAND_CHOICES=()

# Parse a user-supplied option string into a sequence of menu choices.
# Supports:
# - Concatenated digits (e.g., "01234" or "345") → each digit is a choice
# - Comma/space separated numbers (e.g., "3,4,5" or "3 4 5")
# Returns 0 on success and populates SHORTHAND_CHOICES; 1 on parse failure.
parse_choice_sequence() {
    local input="${1//[[:space:]]/}"
    SHORTHAND_CHOICES=()

    if [[ -z "$input" ]]; then
        return 1
    fi

    # Pure digits with length > 1 → treat as shorthand digits
    if [[ "$input" =~ ^[0-9]+$ && ${#input} -gt 1 ]]; then
        for ((i = 0; i < ${#input}; i++)); do
            SHORTHAND_CHOICES+=("${input:i:1}")
        done
        return 0
    fi

    # Otherwise split on commas
    IFS=',' read -ra parts <<< "$input"
    for part in "${parts[@]}"; do
        [[ -z "$part" ]] && continue
        if [[ "$part" =~ ^[0-9]+$ ]]; then
            SHORTHAND_CHOICES+=("$part")
        else
            return 1
        fi
    done

    [[ ${#SHORTHAND_CHOICES[@]} -gt 0 ]]
}

# ============================================================================
# UV Package Manager Support
# ============================================================================

# Check if uv is available and working
check_uv() {
    # Returns 0 if uv is available, 1 otherwise
    if command -v uv >/dev/null 2>&1; then
        # Test that uv is actually functional
        if uv --version >/dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Get Python command with uv fallback
get_python_cmd() {
    # Returns the command array to use for Python execution
    # Prefers "uv run python" if uv is available, falls back to "python3"
    if check_uv; then
        echo "uv run python"
    else
        echo "python3"
    fi
}

# Get pytest command with uv fallback
get_pytest_cmd() {
    # Returns the command array to use for pytest execution
    # Prefers "uv run python -m pytest" if uv is available, falls back to "python3 -m pytest"
    if check_uv; then
        echo "uv run python -m pytest"
    else
        echo "python3 -m pytest"
    fi
}

# Log uv availability status
log_uv_status() {
    if check_uv; then
        log_info "uv package manager detected - using uv run for consistent environments"
    else
        log_warning "uv package manager not found - falling back to direct python3 execution"
        log_info "For better dependency management, install uv: https://github.com/astral-sh/uv"
    fi
}







