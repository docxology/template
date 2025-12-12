#!/usr/bin/env bash

################################################################################
# Research Project Template - Main Dispatcher
#
# Simple dispatcher menu to choose between manuscript and literature operations.
#
# This script provides a unified entry point that routes to:
#   - run_manuscript.sh: Manuscript pipeline operations (setup, tests, analysis, PDF, etc.)
#   - run_literature.sh: Literature search and management operations
#
# For direct access, you can also run:
#   ./run_manuscript.sh [options]
#   ./run_literature.sh [options]
#
# Exit codes: 0 = success, 1 = failure
################################################################################

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

# Paths to the specialized scripts
MANUSCRIPT_SCRIPT="$REPO_ROOT/run_manuscript.sh"
LITERATURE_SCRIPT="$REPO_ROOT/run_literature.sh"

# ============================================================================
# Utility Functions
# ============================================================================

log_header() {
    local message="$1"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  ${message}${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
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

# ============================================================================
# Menu Display
# ============================================================================

display_menu() {
    clear
    echo -e "${BOLD}${BLUE}"
    echo "============================================================"
    echo "  Research Project Template - Main Menu"
    echo "============================================================"
    echo -e "${NC}"
    echo
    echo "Select operation type:"
    echo
    echo "  1. Manuscript Operations"
    echo "     (Setup, Tests, Analysis, PDF Rendering, Validation, LLM Review)"
    echo
    echo "  2. Literature Operations"
    echo "     (Search, Download, Extract, Summarize, Advanced LLM Operations)"
    echo
    echo "  3. Exit"
    echo
    echo -e "${BLUE}============================================================${NC}"
    echo -e "  Repository: ${CYAN}$REPO_ROOT${NC}"
    echo -e "  Python: ${CYAN}$(python3 --version 2>&1)${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo
}

# ============================================================================
# Script Execution
# ============================================================================

run_manuscript() {
    if [[ ! -f "$MANUSCRIPT_SCRIPT" ]]; then
        log_error "Manuscript script not found: $MANUSCRIPT_SCRIPT"
        return 1
    fi
    
    # Pass all arguments to the manuscript script
    exec "$MANUSCRIPT_SCRIPT" "$@"
}

run_literature() {
    if [[ ! -f "$LITERATURE_SCRIPT" ]]; then
        log_error "Literature script not found: $LITERATURE_SCRIPT"
        return 1
    fi
    
    # Pass all arguments to the literature script
    exec "$LITERATURE_SCRIPT" "$@"
}

# ============================================================================
# Help
# ============================================================================

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Research Project Template - Main Dispatcher"
    echo
    echo "This script provides a menu to choose between manuscript and literature operations."
    echo
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --manuscript        Run manuscript operations (passes remaining args to run_manuscript.sh)"
    echo "  --literature        Run literature operations (passes remaining args to run_literature.sh)"
    echo
    echo "Direct Script Access:"
    echo "  ./run_manuscript.sh [options]   # Direct access to manuscript operations"
    echo "  ./run_literature.sh [options]   # Direct access to literature operations"
    echo
    echo "Examples:"
    echo "  $0                      # Interactive menu mode"
    echo "  $0 --manuscript         # Run manuscript operations menu"
    echo "  $0 --literature          # Run literature operations menu"
    echo "  $0 --manuscript --pipeline  # Run manuscript full pipeline"
    echo "  $0 --literature --search    # Run literature search"
    echo
}

# ============================================================================
# Main Entry Point
# ============================================================================

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_help
                exit 0
                ;;
            --manuscript)
                shift  # Remove --manuscript
                run_manuscript "$@"
                exit $?
                ;;
            --literature)
                shift  # Remove --literature
                run_literature "$@"
                exit $?
                ;;
            *)
                # Unknown option - show menu for interactive selection
                break
                ;;
        esac
    done
    
    # Interactive menu mode
    while true; do
        display_menu
        
        echo -n "Select option [1-3]: "
        read -r choice

        case "$choice" in
            1)
                run_manuscript
                ;;
            2)
                run_literature
                ;;
            3)
                log_info "Exiting..."
                exit 0
                ;;
            *)
                log_error "Invalid option: $choice"
                log_info "Please enter 1, 2, or 3"
                echo
                echo -e "${CYAN}Press Enter to continue...${NC}"
                read -r
                ;;
        esac
    done
}

# Run main
main "$@"
