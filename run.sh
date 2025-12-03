#!/usr/bin/env bash

################################################################################
# Unified Research Project Pipeline Orchestrator
#
# A single entry point for all pipeline operations with interactive menu:
#
# Core Build Operations:
#   1. Run infrastructure tests
#   2. Run project tests
#   3. Render PDF manuscript
#   4. Run full pipeline (tests + analysis + PDF + validate)
#
# LLM Operations (requires Ollama):
#   5. LLM manuscript review (English)
#   6. LLM translations (multi-language)
#
# Literature Operations (requires Ollama):
#   7. Search literature and download PDFs
#   8. Generate summaries for existing PDFs
#
#   9. Exit
#
# Non-interactive mode: Use dedicated flags (--pipeline, --infra-tests, etc.)
#
# Exit codes: 0 = success, 1 = failure, 2 = skipped (for optional stages)
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

# Export for subprocess use
export PROJECT_ROOT="$REPO_ROOT"
export PYTHONPATH="${REPO_ROOT}:${REPO_ROOT}/infrastructure:${REPO_ROOT}/project/src:${PYTHONPATH:-}"

# Stage tracking for full pipeline
declare -a STAGE_NAMES=(
    "Setup Environment"
    "Infrastructure Tests"
    "Project Tests"
    "Project Analysis"
    "PDF Rendering"
    "Output Validation"
    "Copy Outputs"
    "LLM Scientific Review"
    "LLM Translations"
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
    local total_stages="$3"
    
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

log_warning() {
    local message="$1"
    echo -e "${YELLOW}⚠${NC} ${message}"
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

press_enter_to_continue() {
    echo
    echo -e "${CYAN}Press Enter to return to menu...${NC}"
    read -r
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
    echo -e "${BOLD}Core Build Operations:${NC}"
    echo "  1. Run infrastructure tests"
    echo "  2. Run project tests"
    echo "  3. Render PDF manuscript"
    echo "  4. Run full pipeline (tests + analysis + PDF + validate)"
    echo
    echo -e "${BOLD}LLM Operations ${YELLOW}(requires Ollama):${NC}"
    echo "  5. LLM manuscript review (English)"
    echo "  6. LLM translations (multi-language)"
    echo
    echo -e "${BOLD}Literature Operations ${YELLOW}(requires Ollama):${NC}"
    echo "  7. Search literature (add to bibliography)"
    echo "  8. Download PDFs (for bibliography entries)"
    echo "  9. Generate summaries (for papers with PDFs)"
    echo "  10. Cleanup library (remove papers without PDFs)"
    echo "  11. Advanced LLM operations (literature review, etc.)"
    echo
    echo "  12. Exit"
    echo
    echo -e "${BLUE}============================================================${NC}"
    echo -e "  Repository: ${CYAN}$REPO_ROOT${NC}"
    echo -e "  Python: ${CYAN}$(python3 --version 2>&1)${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo
}

# ============================================================================
# Clean Output Directories
# ============================================================================

clean_output_directories() {
    echo
    echo -e "${YELLOW}[0/9] Clean Output Directories${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local project_output="$REPO_ROOT/project/output"
    local root_output="$REPO_ROOT/output"
    
    # Clean project/output/
    if [[ -d "$project_output" ]]; then
        log_info "Cleaning project/output/..."
        rm -rf "$project_output"/*
        mkdir -p "$project_output"/{pdf,figures,data,reports,simulations,slides,web,llm}
        log_success "Cleaned project/output/ (recreated subdirectories)"
    else
        mkdir -p "$project_output"/{pdf,figures,data,reports,simulations,slides,web,llm}
        log_info "Created project/output/ directory structure"
    fi
    
    # Clean root output/
    if [[ -d "$root_output" ]]; then
        log_info "Cleaning output/..."
        rm -rf "$root_output"/*
        mkdir -p "$root_output"/{pdf,figures,data,reports,simulations,slides,web,llm}
        log_success "Cleaned output/ (recreated subdirectories)"
    else
        mkdir -p "$root_output"/{pdf,figures,data,reports,simulations,slides,web,llm}
        log_info "Created output/ directory structure"
    fi
    
    log_success "Output directories cleaned - fresh start"
}

# ============================================================================
# Individual Stage Functions
# ============================================================================

run_setup_environment() {
    log_stage 1 "Setup Environment" 9
    
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
    log_header "INFRASTRUCTURE TESTS"
    
    cd "$REPO_ROOT"
    
    log_info "Running infrastructure module tests..."
    log_info "(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)"
    
    if python3 -m pytest tests/infrastructure/ tests/test_coverage_completion.py \
        --ignore=tests/integration/test_module_interoperability.py \
        -m "not requires_ollama" \
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
    log_header "PROJECT TESTS"
    
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
    log_stage 4 "Project Analysis" 9
    
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
    log_header "PDF RENDERING"
    
    cd "$REPO_ROOT"
    
    log_info "Running analysis scripts..."
    if ! python3 scripts/02_run_analysis.py; then
        log_error "Analysis failed"
        return 1
    fi
    
    log_info "Rendering PDF manuscript..."
    if python3 scripts/03_render_pdf.py; then
        log_success "PDF rendering complete"
        return 0
    else
        log_error "PDF rendering failed"
        return 1
    fi
}

run_validation() {
    log_stage 6 "Output Validation" 9
    
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
    log_stage 7 "Copy Outputs" 9
    
    cd "$REPO_ROOT"
    
    if python3 scripts/05_copy_outputs.py; then
        log_success "Output copying complete"
        return 0
    else
        log_error "Output copying failed"
        return 1
    fi
}

run_llm_scientific_review() {
    log_header "LLM SCIENTIFIC REVIEW (ENGLISH)"
    
    cd "$REPO_ROOT"
    
    log_info "Running LLM scientific review (requires Ollama)..."
    log_info "Generating: executive summary, quality review, methodology review, improvements"
    
    local exit_code
    python3 scripts/06_llm_review.py --reviews-only
    exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM scientific review complete"
        return 0
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "LLM review skipped (Ollama not available)"
        log_info "To enable: start Ollama with 'ollama serve' and install a model"
        return 0  # Not a failure, just skipped
    else
        log_error "LLM scientific review failed"
        return 1
    fi
}

run_llm_translations() {
    log_header "LLM TRANSLATIONS"
    
    cd "$REPO_ROOT"
    
    log_info "Running LLM translations (requires Ollama)..."
    log_info "Generating translations for configured languages (see config.yaml)"
    
    local exit_code
    python3 scripts/06_llm_review.py --translations-only
    exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM translations complete"
        return 0
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "LLM translations skipped (Ollama not available or no languages configured)"
        log_info "Configure translations in project/manuscript/config.yaml"
        return 0  # Not a failure, just skipped
    else
        log_error "LLM translations failed"
        return 1
    fi
}

run_literature_search() {
    log_header "LITERATURE SEARCH (ADD TO BIBLIOGRAPHY)"

    cd "$REPO_ROOT"

    log_info "Searching literature and adding papers to bibliography (requires Ollama)..."

    if python3 scripts/07_literature_search.py --search-only; then
        log_success "Literature search complete"
        return 0
    else
        log_error "Literature search failed"
        return 1
    fi
}

run_literature_download() {
    log_header "DOWNLOAD PDFs (FOR BIBLIOGRAPHY ENTRIES)"

    cd "$REPO_ROOT"

    log_info "Downloading PDFs for bibliography entries without PDFs (requires Ollama)..."

    if python3 scripts/07_literature_search.py --download-only; then
        log_success "PDF download complete"
        return 0
    else
        log_error "PDF download failed"
        return 1
    fi
}

run_literature_summarize() {
    log_header "GENERATE SUMMARIES (FOR PAPERS WITH PDFs)"

    cd "$REPO_ROOT"

    log_info "Generating summaries for papers with PDFs (requires Ollama)..."

    if python3 scripts/07_literature_search.py --summarize; then
        log_success "Summary generation complete"
        return 0
    else
        log_error "Summary generation failed"
        return 1
    fi
}

run_literature_cleanup() {
    log_header "CLEANUP LIBRARY (REMOVE PAPERS WITHOUT PDFs)"

    cd "$REPO_ROOT"

    log_info "Cleaning up library by removing papers without PDFs..."

    if python3 scripts/07_literature_search.py --cleanup; then
        log_success "Library cleanup complete"
        return 0
    else
        log_error "Library cleanup failed"
        return 1
    fi
}

run_literature_llm_operations() {
    log_header "ADVANCED LLM OPERATIONS (LITERATURE REVIEW, ETC.)"

    cd "$REPO_ROOT"

    echo
    echo "Available LLM operations:"
    echo "  1. Literature review synthesis"
    echo "  2. Science communication narrative"
    echo "  3. Comparative analysis"
    echo "  4. Research gap identification"
    echo "  5. Citation network analysis"
    echo

    read -p "Choose operation (1-5): " op_choice

    case $op_choice in
        1)
            operation="review"
            ;;
        2)
            operation="communication"
            ;;
        3)
            operation="compare"
            ;;
        4)
            operation="gaps"
            ;;
        5)
            operation="network"
            ;;
        *)
            log_error "Invalid choice: $op_choice"
            return 1
            ;;
    esac

    log_info "Running LLM operation: $operation (requires Ollama)..."

    if python3 scripts/07_literature_search.py --llm-operation "$operation"; then
        log_success "LLM operation complete"
        return 0
    else
        log_error "LLM operation failed"
        return 1
    fi
}

# ============================================================================
# Full Pipeline Execution
# ============================================================================

run_full_pipeline() {
    log_header "COMPLETE RESEARCH PROJECT PIPELINE"
    
    local pipeline_start=$(date +%s)
    
    log_info "Repository: $REPO_ROOT"
    log_info "Python: $(python3 --version)"
    echo
    
    # Reset stage tracking
    STAGE_RESULTS=()
    STAGE_DURATIONS=()
    
    # Stage 0: Clean output directories
    clean_output_directories
    
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
    stage_start=$(date +%s)
    log_stage 2 "Infrastructure Tests" 9
    cd "$REPO_ROOT"
    log_info "Running infrastructure module tests..."
    if ! python3 -m pytest tests/infrastructure/ tests/test_coverage_completion.py \
        --ignore=tests/integration/test_module_interoperability.py \
        -m "not requires_ollama" \
        --cov=infrastructure \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=49 \
        -v --tb=short; then
        log_error "Pipeline failed at Stage 2 (Infrastructure Tests)"
        return 1
    fi
    log_success "Infrastructure tests passed"
    stage_end=$(date +%s)
    STAGE_RESULTS[1]=0
    STAGE_DURATIONS[1]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 3: Project Tests
    stage_start=$(date +%s)
    log_stage 3 "Project Tests" 9
    cd "$REPO_ROOT"
    log_info "Running project tests..."
    if ! python3 -m pytest project/tests/ \
        --ignore=project/tests/integration \
        --cov=project/src \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=70 \
        -v --tb=short; then
        log_error "Pipeline failed at Stage 3 (Project Tests)"
        return 1
    fi
    log_success "Project tests passed"
    stage_end=$(date +%s)
    STAGE_RESULTS[2]=0
    STAGE_DURATIONS[2]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 4: Analysis
    stage_start=$(date +%s)
    if ! run_analysis; then
        log_error "Pipeline failed at Stage 4 (Project Analysis)"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[3]=0
    STAGE_DURATIONS[3]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 5: PDF Rendering
    stage_start=$(date +%s)
    log_stage 5 "PDF Rendering" 9
    cd "$REPO_ROOT"
    if ! python3 scripts/03_render_pdf.py; then
        log_error "Pipeline failed at Stage 5 (PDF Rendering)"
        return 1
    fi
    log_success "PDF rendering complete"
    stage_end=$(date +%s)
    STAGE_RESULTS[4]=0
    STAGE_DURATIONS[4]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 6: Validation
    stage_start=$(date +%s)
    if ! run_validation; then
        log_error "Pipeline failed at Stage 6 (Output Validation)"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[5]=0
    STAGE_DURATIONS[5]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 7: Copy Outputs
    stage_start=$(date +%s)
    if ! run_copy_outputs; then
        log_error "Pipeline failed at Stage 7 (Copy Outputs)"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[6]=0
    STAGE_DURATIONS[6]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 8: LLM Scientific Review (optional)
    stage_start=$(date +%s)
    log_stage 8 "LLM Scientific Review" 9
    cd "$REPO_ROOT"
    log_info "Running LLM scientific review (requires Ollama)..."
    local exit_code
    python3 scripts/06_llm_review.py --reviews-only
    exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM scientific review complete"
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "LLM scientific review skipped (Ollama not available)"
    else
        log_error "Pipeline failed at Stage 8 (LLM Scientific Review)"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[7]=0
    STAGE_DURATIONS[7]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 9: LLM Translations (optional)
    stage_start=$(date +%s)
    log_stage 9 "LLM Translations" 9
    cd "$REPO_ROOT"
    log_info "Running LLM translations (requires Ollama)..."
    python3 scripts/06_llm_review.py --translations-only
    exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM translations complete"
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "LLM translations skipped (Ollama not available or no languages configured)"
    else
        log_error "Pipeline failed at Stage 9 (LLM Translations)"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[8]=0
    STAGE_DURATIONS[8]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Success - print summary
    local pipeline_end=$(date +%s)
    local total_duration=$(get_elapsed_time "$pipeline_start" "$pipeline_end")
    
    print_pipeline_summary "$total_duration"
    
    return 0
}

print_pipeline_summary() {
    local total_duration="$1"
    local num_stages="${#STAGE_NAMES[@]}"
    
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
    echo "  • LLM reviews: project/output/llm/ (if Ollama available)"
    echo
    log_success "Pipeline complete - ready for deployment"
    echo
}

# ============================================================================
# Menu Handler
# ============================================================================

handle_menu_choice() {
    local choice="$1"
    local start_time end_time duration
    
    start_time=$(date +%s)
    
    case "$choice" in
        1)
            run_infrastructure_tests
            ;;
        2)
            run_project_tests
            ;;
        3)
            run_pdf_rendering
            ;;
        4)
            run_full_pipeline
            ;;
        5)
            run_llm_scientific_review
            ;;
        6)
            run_llm_translations
            ;;
        7)
            run_literature_search
            ;;
        8)
            run_literature_download
            ;;
        9)
            run_literature_summarize
            ;;
        10)
            run_literature_cleanup
            ;;
        11)
            run_literature_llm_operations
            ;;
        12)
            echo
            log_info "Exiting. Goodbye!"
            exit 0
            ;;
        *)
            log_error "Invalid option: $choice"
            log_info "Please enter a number between 1 and 12"
            ;;
    esac
    
    end_time=$(date +%s)
    duration=$(get_elapsed_time "$start_time" "$end_time")
    
    echo
    log_info "Operation completed in $(format_duration "$duration")"
}

# ============================================================================
# Non-Interactive Mode
# ============================================================================

run_non_interactive() {
    local option="$1"
    
    log_header "NON-INTERACTIVE MODE"
    log_info "Running option: $option"
    
    handle_menu_choice "$option"
    local exit_code=$?
    
    exit $exit_code
}

# ============================================================================
# Help
# ============================================================================

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Unified Research Project Pipeline Orchestrator"
    echo
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo
    echo "Core Build Operations:"
    echo "  --infra-tests       Run infrastructure tests"
    echo "  --project-tests     Run project tests"
    echo "  --render-pdf        Render PDF manuscript"
    echo "  --pipeline          Run full pipeline (tests + analysis + PDF + validate)"
    echo
    echo "LLM Operations (requires Ollama):"
    echo "  --reviews           Run LLM manuscript review (English)"
    echo "  --translations      Run LLM translations (multi-language)"
    echo
    echo "Literature Operations (requires Ollama):"
    echo "  --search            Search literature (add to bibliography)"
    echo "  --download          Download PDFs (for bibliography entries)"
    echo "  --summarize         Generate summaries (for papers with PDFs)"
    echo
    echo "Menu Options:"
    echo
    echo "Core Build Operations:"
    echo "  1  Run infrastructure tests"
    echo "  2  Run project tests"
    echo "  3  Render PDF manuscript"
    echo "  4  Run full pipeline (tests + analysis + PDF + validate)"
    echo
    echo "LLM Operations (requires Ollama):"
    echo "  5  LLM manuscript review (English)"
    echo "  6  LLM translations (multi-language)"
    echo
    echo "Literature Operations (requires Ollama):"
    echo "  7  Search literature (add to bibliography)"
    echo "  8  Download PDFs (for bibliography entries)"
    echo "  9  Generate summaries (for papers with PDFs)"
    echo
    echo "  10  Exit"
    echo
    echo "Examples:"
    echo "  $0                      # Interactive menu mode"
    echo "  $0 --pipeline           # Run full pipeline"
    echo "  $0 --infra-tests         # Run infrastructure tests"
    echo "  $0 --project-tests       # Run project tests"
    echo "  $0 --render-pdf          # Render PDF manuscript"
    echo "  $0 --reviews             # Run LLM manuscript review"
    echo "  $0 --translations        # Run LLM translations"
    echo "  $0 --search              # Search literature (add to bibliography)"
    echo "  $0 --download            # Download PDFs (for bibliography entries)"
    echo "  $0 --summarize           # Generate summaries (for papers with PDFs)"
    echo
    echo "Note: --option N is also supported for compatibility (1-12)"
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
            --option)
                if [[ -z "${2:-}" ]]; then
                    log_error "Missing option number"
                    show_help
                    exit 1
                fi
                run_non_interactive "$2"
                exit $?
                ;;
            --infra-tests|--tests-infra)
                run_non_interactive 1
                exit $?
                ;;
            --project-tests|--tests-project)
                run_non_interactive 2
                exit $?
                ;;
            --render-pdf|--pdf)
                run_non_interactive 3
                exit $?
                ;;
            --pipeline)
                run_non_interactive 4
                exit $?
                ;;
            --reviews)
                run_non_interactive 5
                exit $?
                ;;
            --translations)
                run_non_interactive 6
                exit $?
                ;;
            --search)
                run_non_interactive 7
                exit $?
                ;;
            --download)
                run_non_interactive 8
                exit $?
                ;;
            --summarize)
                run_non_interactive 9
                exit $?
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done
    
    # Interactive menu mode
    while true; do
        display_menu
        
        echo -n "Select option [1-10]: "
        read -r choice
        
        handle_menu_choice "$choice"
        
        # Return to menu after operation (except for exit)
        if [[ "$choice" != "9" ]]; then
            press_enter_to_continue
        fi
    done
}

# Run main
main "$@"

