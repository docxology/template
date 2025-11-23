#!/usr/bin/env bash

################################################################################
# Complete Research Project Pipeline Orchestrator
#
# This script orchestrates the complete build pipeline:
#   Stage 0: Environment Setup
#   Stage 1a: Infrastructure Tests
#   Stage 1b: Project Tests  
#   Stage 2: Analysis & Figures
#   Stage 3: PDF Rendering
#   Stage 4: Output Validation
#
# All stages are run in sequence, stopping on first failure.
# Provides detailed progress reporting and final summary.
#
# Usage: ./run_all.sh
# Exit codes: 0 = success, 1 = failure
################################################################################

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"

# Export for subprocess use
export PROJECT_ROOT="$REPO_ROOT"
export PYTHONPATH="${REPO_ROOT}:${REPO_ROOT}/infrastructure:${REPO_ROOT}/project/src:${PYTHONPATH:-}"

# Stage tracking
declare -a STAGE_NAMES=(
    "Setup Environment"
    "Infrastructure Tests"
    "Project Tests"
    "Project Analysis"
    "PDF Rendering"
    "Output Validation"
    "Copy Outputs"
)

declare -a STAGE_SCRIPTS=(
    "scripts/00_setup_environment.py"
    "tests/infrastructure/"
    "project/tests/"
    "scripts/02_run_analysis.py"
    "scripts/03_render_pdf.py"
    "scripts/04_validate_output.py"
    "scripts/05_copy_outputs.py"
)

declare -a STAGE_RESULTS=()
declare -a STAGE_DURATIONS=()

# ============================================================================
# Utility Functions
# ============================================================================

log_header() {
    local message="$1"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  ${message}${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

log_stage() {
    local stage_num="$1"
    local stage_name="$2"
    local total_stages="${#STAGE_NAMES[@]}"
    
    echo
    echo -e "${YELLOW}[${stage_num}/${total_stages}] ${stage_name}${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
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

# ============================================================================
# Stage Execution Functions
# ============================================================================

run_setup_environment() {
    log_stage 1 "${STAGE_NAMES[0]}"
    
    cd "$REPO_ROOT"
    if python3 scripts/00_setup_environment.py; then
        log_success "Environment setup complete"
        return 0
    else
        log_error "Environment setup failed"
        return 1
    fi
}

run_infrastructure_tests() {
    log_stage 2 "${STAGE_NAMES[1]}"
    
    cd "$REPO_ROOT"
    
    log_info "Running infrastructure module tests..."
    
    # Run infrastructure tests with integration tests for full coverage
    # (excluding problematic module interoperability tests that expect non-existent repo_utilities)
    if python3 -m pytest tests/infrastructure/ tests/test_coverage_completion.py \
        --ignore=tests/integration/test_module_interoperability.py \
        --cov=infrastructure \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=49 \
        -v --tb=short; then
        
        log_success "Infrastructure tests passed"
        return 0
    else
        log_error "Infrastructure tests failed"
        return 1
    fi
}

run_project_tests() {
    log_stage 3 "${STAGE_NAMES[2]}"
    
    cd "$REPO_ROOT"
    
    log_info "Running project tests..."
    
    if python3 -m pytest project/tests/ \
        --ignore=project/tests/integration \
        --cov=project/src \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=70 \
        -v --tb=short; then
        
        log_success "Project tests passed"
        return 0
    else
        log_error "Project tests failed"
        return 1
    fi
}

run_analysis() {
    log_stage 4 "${STAGE_NAMES[3]}"
    
    cd "$REPO_ROOT"
    
    if python3 scripts/02_run_analysis.py; then
        log_success "Project analysis complete"
        return 0
    else
        log_error "Project analysis failed"
        return 1
    fi
}

run_pdf_rendering() {
    log_stage 5 "${STAGE_NAMES[4]}"
    
    cd "$REPO_ROOT"
    
    if python3 scripts/03_render_pdf.py; then
        log_success "PDF rendering complete"
        return 0
    else
        log_error "PDF rendering failed"
        return 1
    fi
}

run_validation() {
    log_stage 6 "${STAGE_NAMES[5]}"
    
    cd "$REPO_ROOT"
    
    if python3 scripts/04_validate_output.py; then
        log_success "Output validation complete"
        return 0
    else
        log_error "Output validation failed"
        return 1
    fi
}

run_copy_outputs() {
    log_stage 7 "${STAGE_NAMES[6]}"
    
    cd "$REPO_ROOT"
    
    if python3 scripts/05_copy_outputs.py; then
        log_success "Output copying complete"
        return 0
    else
        log_error "Output copying failed"
        return 1
    fi
}

# ============================================================================
# Main Pipeline
# ============================================================================

main() {
    log_header "COMPLETE RESEARCH PROJECT PIPELINE"
    
    local pipeline_start=$(date +%s)
    
    log_info "Repository: $REPO_ROOT"
    log_info "Python: $(python3 --version)"
    echo
    
    # Stage 1: Setup Environment
    local stage_start=$(date +%s)
    if ! run_setup_environment; then
        log_error "Pipeline failed at Stage 1 (Setup Environment)"
        return 1
    fi
    local stage_end=$(date +%s)
    STAGE_RESULTS[0]=0
    STAGE_DURATIONS[0]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 2: Infrastructure Tests
    local stage_start=$(date +%s)
    if ! run_infrastructure_tests; then
        log_error "Pipeline failed at Stage 2 (Infrastructure Tests)"
        return 1
    fi
    local stage_end=$(date +%s)
    STAGE_RESULTS[1]=0
    STAGE_DURATIONS[1]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 3: Project Tests
    local stage_start=$(date +%s)
    if ! run_project_tests; then
        log_error "Pipeline failed at Stage 3 (Project Tests)"
        return 1
    fi
    local stage_end=$(date +%s)
    STAGE_RESULTS[2]=0
    STAGE_DURATIONS[2]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 4: Analysis
    local stage_start=$(date +%s)
    if ! run_analysis; then
        log_error "Pipeline failed at Stage 4 (Project Analysis)"
        return 1
    fi
    local stage_end=$(date +%s)
    STAGE_RESULTS[3]=0
    STAGE_DURATIONS[3]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 5: PDF Rendering
    local stage_start=$(date +%s)
    if ! run_pdf_rendering; then
        log_error "Pipeline failed at Stage 5 (PDF Rendering)"
        return 1
    fi
    local stage_end=$(date +%s)
    STAGE_RESULTS[4]=0
    STAGE_DURATIONS[4]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 6: Validation
    local stage_start=$(date +%s)
    if ! run_validation; then
        log_error "Pipeline failed at Stage 6 (Output Validation)"
        return 1
    fi
    local stage_end=$(date +%s)
    STAGE_RESULTS[5]=0
    STAGE_DURATIONS[5]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 7: Copy Outputs
    local stage_start=$(date +%s)
    if ! run_copy_outputs; then
        log_error "Pipeline failed at Stage 7 (Copy Outputs)"
        return 1
    fi
    local stage_end=$(date +%s)
    STAGE_RESULTS[6]=0
    STAGE_DURATIONS[6]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Success - print summary
    local pipeline_end=$(date +%s)
    local total_duration=$(get_elapsed_time "$pipeline_start" "$pipeline_end")
    
    print_summary "${#STAGE_NAMES[@]}" "$total_duration"
    
    return 0
}

print_summary() {
    local num_stages="$1"
    local total_duration="$2"
    
    echo
    log_header "PIPELINE SUMMARY"
    
    log_success "All stages completed successfully!"
    echo
    
    echo "Stage Results:"
    for ((i=0; i<num_stages; i++)); do
        local stage_name="${STAGE_NAMES[$i]}"
        local duration=$(format_duration "${STAGE_DURATIONS[$i]}")
        echo -e "  ${GREEN}✓${NC} Stage $((i+1)): ${stage_name} (${duration})"
    done
    
    echo
    echo "Total Execution Time: $(format_duration "$total_duration")"
    echo
    echo "Generated Outputs:"
    echo "  • Coverage reports: htmlcov/"
    echo "  • PDF files: project/output/pdf/"
    echo "  • Figures: project/output/figures/"
    echo "  • Data files: project/output/data/"
    echo
    log_success "Pipeline complete - ready for deployment"
    echo
}

print_error_summary() {
    local failed_stage="$1"
    
    echo
    log_header "PIPELINE FAILED"
    
    log_error "Failed at: Stage $failed_stage"
    echo
    echo "Previous successful stages:"
    for ((i=0; i<failed_stage-1; i++)); do
        local stage_name="${STAGE_NAMES[$i]}"
        local duration=$(format_duration "${STAGE_DURATIONS[$i]}")
        echo -e "  ${GREEN}✓${NC} Stage $((i+1)): ${stage_name} (${duration})"
    done
    echo
    log_error "Review errors above and fix issues before retrying"
    echo
}

# ============================================================================
# Entry Point
# ============================================================================

if main; then
    exit 0
else
    exit 1
fi

