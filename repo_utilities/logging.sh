#!/bin/bash

# Unified Logging Library for Build Scripts
# Provides consistent logging across all repository automation scripts
# Features: log levels, timestamps, colors, emojis, log file support, progress tracking

# =============================================================================
# CONFIGURATION
# =============================================================================

# Log levels (numeric for comparison)
LOG_DEBUG=0
LOG_INFO=1
LOG_WARN=2
LOG_ERROR=3

# Current log level (can be set via LOG_LEVEL environment variable)
LOG_LEVEL="${LOG_LEVEL:-$LOG_INFO}"

# Log file (optional)
LOG_FILE="${LOG_FILE:-}"

# Color and emoji support
USE_COLORS="${USE_COLORS:-1}"
USE_EMOJIS="${USE_EMOJIS:-1}"

# Detect TTY if not already set
if [ -z "${TTY_DETECTED:-}" ]; then
    if [ -t 1 ]; then
        TTY_DETECTED=1
    else
        TTY_DETECTED=0
    fi
fi

# Disable colors if NO_COLOR is set or not a TTY
if [ -n "${NO_COLOR:-}" ] || [ $TTY_DETECTED -eq 0 ]; then
    USE_COLORS=0
fi

# =============================================================================
# COLOR DEFINITIONS (only used if USE_COLORS=1)
# =============================================================================

COLOR_RESET='\033[0m'
COLOR_BOLD='\033[1m'
COLOR_DIM='\033[2m'
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_BLUE='\033[0;34m'
COLOR_CYAN='\033[0;36m'

# =============================================================================
# EMOJI DEFINITIONS
# =============================================================================

EMOJI_SUCCESS="✅"
EMOJI_INFO="ℹ️"
EMOJI_WARNING="⚠️"
EMOJI_ERROR="❌"
EMOJI_ROCKET="🚀"
EMOJI_SPARKLES="✨"
EMOJI_FOLDER="📁"
EMOJI_BOOK="📖"
EMOJI_CLEAN="🧹"
EMOJI_GEAR="⚙️"
EMOJI_CHART="📊"

# =============================================================================
# CORE LOGGING FUNCTION
# =============================================================================

# Core logging function with timestamp and level
# Usage: log <level> <message>
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local level_name=""
    local color_code=""
    local emoji=""
    
    # Determine level name and color based on level
    case "$level" in
        $LOG_DEBUG) 
            level_name="DEBUG"
            color_code="$COLOR_DIM"
            emoji=""
            ;;
        $LOG_INFO)  
            level_name="INFO"
            color_code="$COLOR_CYAN"
            if [ $USE_EMOJIS -eq 1 ]; then emoji="$EMOJI_INFO"; fi
            ;;
        $LOG_WARN)  
            level_name="WARN"
            color_code="$COLOR_YELLOW"
            if [ $USE_EMOJIS -eq 1 ]; then emoji="$EMOJI_WARNING"; fi
            ;;
        $LOG_ERROR) 
            level_name="ERROR"
            color_code="$COLOR_RED"
            if [ $USE_EMOJIS -eq 1 ]; then emoji="$EMOJI_ERROR"; fi
            ;;
        *)
            level_name="UNKNOWN"
            color_code="$COLOR_DIM"
            emoji=""
            ;;
    esac
    
    # Only log if level is high enough
    if [ "$level" -lt "$LOG_LEVEL" ]; then
        return 0
    fi
    
    # Format message with or without colors
    local formatted_msg=""
    if [ $USE_COLORS -eq 1 ] && [ -n "$color_code" ]; then
        if [ -n "$emoji" ]; then
            formatted_msg="${color_code}${emoji} [$timestamp] [$level_name]${COLOR_RESET} $message"
        else
            formatted_msg="${color_code}[$timestamp] [$level_name]${COLOR_RESET} $message"
        fi
    else
        formatted_msg="[$timestamp] [$level_name] $message"
    fi
    
    # Output to console (stderr for WARN/ERROR, stdout otherwise)
    if [ "$level" -ge $LOG_WARN ]; then
        echo -e "$formatted_msg" >&2
    else
        echo -e "$formatted_msg"
    fi
    
    # Also log to file if specified (plain text)
    if [ -n "$LOG_FILE" ]; then
        echo "[$timestamp] [$level_name] $message" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

# =============================================================================
# CONVENIENCE LOGGING FUNCTIONS
# =============================================================================

log_debug() { log $LOG_DEBUG "$@"; }
log_info() { log $LOG_INFO "$@"; }
log_warn() { log $LOG_WARN "$@"; }
log_error() { log $LOG_ERROR "$@"; }

# =============================================================================
# SPECIALIZED LOGGING FUNCTIONS
# =============================================================================

# Log a section header with visual emphasis
log_header() {
    local message="$1"
    local emoji=""
    if [ $USE_EMOJIS -eq 1 ]; then
        emoji="$EMOJI_ROCKET "
    fi
    
    if [ $USE_COLORS -eq 1 ]; then
        echo ""
        echo -e "${COLOR_BOLD}${COLOR_BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
        echo -e "${COLOR_BOLD}${COLOR_CYAN}${emoji}${message}${COLOR_RESET}"
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
        echo "" >> "$LOG_FILE" 2>/dev/null || true
        echo "================================================================================" >> "$LOG_FILE" 2>/dev/null || true
        echo "$message" >> "$LOG_FILE" 2>/dev/null || true
        echo "================================================================================" >> "$LOG_FILE" 2>/dev/null || true
        echo "" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

# Log a processing step
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
        echo "" >> "$LOG_FILE" 2>/dev/null || true
        echo "Step ${step_num}: ${step_title}" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

# Log a success message
log_success() {
    local message="$1"
    local emoji=""
    if [ $USE_EMOJIS -eq 1 ]; then
        emoji="$EMOJI_SUCCESS "
    fi
    
    if [ $USE_COLORS -eq 1 ]; then
        echo -e "${COLOR_GREEN}${emoji}${message}${COLOR_RESET}"
    else
        echo "[SUCCESS] $message"
    fi
    
    if [ -n "$LOG_FILE" ]; then
        echo "[SUCCESS] $message" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

# Log a dimmed message (for details/context)
log_dim() {
    local message="$1"
    
    if [ $USE_COLORS -eq 1 ]; then
        echo -e "${COLOR_DIM}   ${message}${COLOR_RESET}"
    else
        echo "   $message"
    fi
    
    if [ -n "$LOG_FILE" ]; then
        echo "   $message" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

# Log progress indicator with percentage
log_progress() {
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
        echo "[$current/$total - ${percent}%] $task" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

# Log timing information
log_timing() {
    local start_time="$1"
    local end_time="$2"
    local label="$3"
    
    local duration=$((end_time - start_time))
    local msg="${label}: ${duration}s"
    
    if [ $USE_COLORS -eq 1 ]; then
        echo -e "${COLOR_DIM}   ${msg}${COLOR_RESET}"
    else
        echo "   $msg"
    fi
    
    if [ -n "$LOG_FILE" ]; then
        echo "   $msg" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Initialize log file
init_log_file() {
    if [ -n "$LOG_FILE" ]; then
        touch "$LOG_FILE" || {
            log_error "Cannot create log file: $LOG_FILE"
            return 1
        }
        log_info "Logging to: $LOG_FILE"
    fi
    return 0
}

# Get current log level name
get_log_level_name() {
    case "$LOG_LEVEL" in
        $LOG_DEBUG) echo "DEBUG" ;;
        $LOG_INFO) echo "INFO" ;;
        $LOG_WARN) echo "WARN" ;;
        $LOG_ERROR) echo "ERROR" ;;
        *) echo "UNKNOWN" ;;
    esac
}

# Set log level by name
set_log_level() {
    local level_name="$1"
    case "$level_name" in
        DEBUG|debug|0) LOG_LEVEL=$LOG_DEBUG ;;
        INFO|info|1) LOG_LEVEL=$LOG_INFO ;;
        WARN|warn|2) LOG_LEVEL=$LOG_WARN ;;
        ERROR|error|3) LOG_LEVEL=$LOG_ERROR ;;
        *) 
            log_error "Unknown log level: $level_name"
            return 1
            ;;
    esac
    return 0
}

# Log script execution info
log_execution_info() {
    local script_name="${1:-script}"
    local repo_root="${2:-.}"
    
    log_info "Script: $script_name"
    log_info "Repository: $repo_root"
    log_info "Started: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "Log level: $(get_log_level_name)"
}

# =============================================================================
# EXPORT FUNCTIONS FOR SUBSHELLS
# =============================================================================

# Export all functions so they're available in subshells
export -f log
export -f log_debug
export -f log_info
export -f log_warn
export -f log_error
export -f log_header
export -f log_step
export -f log_success
export -f log_dim
export -f log_progress
export -f log_timing
export -f init_log_file
export -f get_log_level_name
export -f set_log_level
export -f log_execution_info

# Export constants
export LOG_DEBUG LOG_INFO LOG_WARN LOG_ERROR
export LOG_LEVEL LOG_FILE
export USE_COLORS USE_EMOJIS TTY_DETECTED
export COLOR_RESET COLOR_BOLD COLOR_DIM COLOR_RED COLOR_GREEN COLOR_YELLOW COLOR_BLUE COLOR_CYAN
export EMOJI_SUCCESS EMOJI_INFO EMOJI_WARNING EMOJI_ERROR EMOJI_ROCKET EMOJI_SPARKLES EMOJI_FOLDER EMOJI_BOOK EMOJI_CLEAN EMOJI_GEAR EMOJI_CHART

