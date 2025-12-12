#!/usr/bin/env bash
################################################################################
# Shared Bash Utilities
#
# Common utilities for run_manuscript.sh and run_literature.sh:
# - Color codes and formatting
# - Logging functions
# - Utility functions (duration formatting, choice parsing, etc.)
# - Environment setup
#
# This file is sourced by both run_manuscript.sh and run_literature.sh
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
export PYTHONPATH="${REPO_ROOT}:${REPO_ROOT}/infrastructure:${REPO_ROOT}/project/src:${PYTHONPATH:-}"

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


