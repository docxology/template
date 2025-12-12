#!/usr/bin/env bash

################################################################################
# Research Project Template - Main Entry Point
#
# Entry point for manuscript pipeline operations.
#
# This script routes to run_manuscript.sh for all manuscript operations.
#
# For direct access, you can also run:
#   ./run_manuscript.sh [options]
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

# Path to the manuscript script
MANUSCRIPT_SCRIPT="$REPO_ROOT/run_manuscript.sh"

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


# ============================================================================
# Help
# ============================================================================

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Research Project Template - Main Entry Point"
    echo
    echo "This script routes to run_manuscript.sh for manuscript pipeline operations."
    echo
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo
    echo "Direct Script Access:"
    echo "  ./run_manuscript.sh [options]   # Direct access to manuscript operations"
    echo
    echo "Examples:"
    echo "  $0                      # Run manuscript operations menu"
    echo "  $0 --pipeline           # Run manuscript full pipeline"
    echo "  ./run_manuscript.sh --help  # Show manuscript script help"
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
            *)
                # Pass all arguments to manuscript script
                run_manuscript "$@"
                exit $?
                ;;
        esac
    done
    
    # No arguments - run manuscript script interactively
    run_manuscript
}

# Run main
main "$@"
