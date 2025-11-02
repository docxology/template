#!/bin/bash

# Simple PDF regeneration script
# This script clears the output folder and fully regenerates all PDFs

set -euo pipefail

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Color codes for improved readability
readonly COLOR_RESET='\033[0m'
readonly COLOR_BOLD='\033[1m'
readonly COLOR_DIM='\033[2m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_CYAN='\033[0;36m'

# Log with timestamp and visual formatting
log_header() {
    echo -e "\n${COLOR_BOLD}${COLOR_BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_CYAN}$1${COLOR_RESET}"
    echo -e "${COLOR_BOLD}${COLOR_BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}\n"
}

log_step() {
    local step_num="$1"
    local step_title="$2"
    echo -e "\n${COLOR_BOLD}${COLOR_BLUE}▶ Step ${step_num}:${COLOR_RESET} ${COLOR_BOLD}${step_title}${COLOR_RESET}"
}

log_success() {
    echo -e "${COLOR_GREEN}✅ $1${COLOR_RESET}"
}

log_info() {
    echo -e "${COLOR_CYAN}ℹ️  $1${COLOR_RESET}"
}

log_warning() {
    echo -e "${COLOR_YELLOW}⚠️  $1${COLOR_RESET}"
}

log_error() {
    echo -e "${COLOR_RED}❌ $1${COLOR_RESET}"
}

log_dim() {
    echo -e "${COLOR_DIM}   $1${COLOR_RESET}"
}

# Progress indicator
show_progress() {
    local current="$1"
    local total="$2"
    local task="$3"
    local percent=$((current * 100 / total))
    echo -e "${COLOR_CYAN}[$current/$total - ${percent}%]${COLOR_RESET} $task"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

SCRIPT_START=$(date +%s)

log_header "🚀 PDF REGENERATION FROM SCRATCH"

log_info "Repository: $(pwd)"
log_info "Started: $(date '+%Y-%m-%d %H:%M:%S')"

# =============================================================================
# STEP 1: CLEANUP
# =============================================================================

log_step "1/3" "Cleaning Previous Outputs"

if [ ! -f "./repo_utilities/clean_output.sh" ]; then
    log_error "clean_output.sh not found"
    exit 1
fi

CLEAN_START=$(date +%s)
log_dim "Executing: ./repo_utilities/clean_output.sh"

# Capture and suppress redundant output
CLEAN_OUTPUT=$(./repo_utilities/clean_output.sh 2>&1)
CLEAN_EXIT=$?
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

if [ ! -f "./repo_utilities/render_pdf.sh" ]; then
    log_error "render_pdf.sh not found"
    exit 1
fi

RENDER_START=$(date +%s)
log_dim "Executing: ./repo_utilities/render_pdf.sh"
log_info "This may take 1-2 minutes depending on project complexity..."

# Run render_pdf.sh but filter output for clarity
# Suppress harmless warnings and verbose messages
if ./repo_utilities/render_pdf.sh 2>&1 | \
   grep -v "Deprecated: --highlight-style" | \
   grep -v "Deprecated: --listings" | \
   grep -v "Deprecated: --self-contained" | \
   grep -v "sed: 1:" | \
   grep -v "invalid command code" | \
   grep -v "I found no" | \
   grep -v "There were.*error messages" | \
   grep -v "Could not convert TeX math"; then
    RENDER_EXIT=0
else
    RENDER_EXIT=$?
fi

RENDER_END=$(date +%s)
RENDER_DURATION=$((RENDER_END - RENDER_START))

if [ $RENDER_EXIT -eq 0 ]; then
    log_success "PDF generation complete (${RENDER_DURATION}s)"
    
    # Count generated files
    if [ -d "output/pdf" ]; then
        PDF_COUNT=$(find output/pdf -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')
        log_info "Generated ${PDF_COUNT} PDF files"
    fi
    
    if [ -d "output/figures" ]; then
        FIGURE_COUNT=$(find output/figures -name "*.png" 2>/dev/null | wc -l | tr -d ' ')
        log_info "Generated ${FIGURE_COUNT} figures"
    fi
else
    log_error "PDF generation failed (exit code: $RENDER_EXIT)"
    exit 1
fi

# =============================================================================
# STEP 3: VALIDATION
# =============================================================================

log_step "3/3" "Validating PDF Quality"

VALIDATION_START=$(date +%s)
log_dim "Checking for rendering issues..."

# Run validation with cleaner output
if uv run python repo_utilities/validate_pdf_output.py --words 200 2>&1; then
    VALIDATION_EXIT=0
else
    VALIDATION_EXIT=$?
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
fi

# =============================================================================
# SUMMARY
# =============================================================================

SCRIPT_END=$(date +%s)
TOTAL_DURATION=$((SCRIPT_END - SCRIPT_START))

log_header "✨ REGENERATION COMPLETE"

log_info "Total time: ${TOTAL_DURATION}s (${CLEAN_DURATION}s + ${RENDER_DURATION}s + ${VALIDATION_DURATION}s)"
log_info "Completed: $(date '+%Y-%m-%d %H:%M:%S')"

echo ""
echo -e "${COLOR_BOLD}📁 Generated Outputs:${COLOR_RESET}"
echo -e "   ${COLOR_GREEN}→${COLOR_RESET} PDFs:    ${COLOR_BOLD}output/pdf/${COLOR_RESET}"
echo -e "   ${COLOR_GREEN}→${COLOR_RESET} Figures: ${COLOR_BOLD}output/figures/${COLOR_RESET}"
echo -e "   ${COLOR_GREEN}→${COLOR_RESET} Data:    ${COLOR_BOLD}output/data/${COLOR_RESET}"
echo -e "   ${COLOR_GREEN}→${COLOR_RESET} LaTeX:   ${COLOR_BOLD}output/tex/${COLOR_RESET}"

echo ""
echo -e "${COLOR_BOLD}📖 View Results:${COLOR_RESET}"
echo -e "   ${COLOR_CYAN}•${COLOR_RESET} Main PDF:     ${COLOR_DIM}output/pdf/project_combined.pdf${COLOR_RESET}"
echo -e "   ${COLOR_CYAN}•${COLOR_RESET} HTML version: ${COLOR_DIM}output/project_combined.html${COLOR_RESET}"
echo -e "   ${COLOR_CYAN}•${COLOR_RESET} Open quickly: ${COLOR_DIM}./repo_utilities/open_manuscript.sh${COLOR_RESET}"

# Exit with appropriate code
if [ $VALIDATION_EXIT -eq 0 ]; then
    exit 0
else
    exit $VALIDATION_EXIT
fi
