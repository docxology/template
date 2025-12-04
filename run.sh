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
    # Clean and recreate output directories for fresh pipeline run.
    # Removes all files from project/output/ and root output/ directories,
    # then recreates the standard directory structure.
    # This ensures no stale files from previous runs interfere with current execution.
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
# Common Test Execution Functions
# ============================================================================

run_pytest_infrastructure() {
    # Execute infrastructure tests with coverage requirements.
    # Runs pytest on tests/infrastructure/ with 49% coverage threshold.
    # Skips requires_ollama tests by default.
    # Returns: 0 on success, 1 on failure
    cd "$REPO_ROOT"
    
    log_info "Running infrastructure module tests..."
    log_info "(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)"
    
    python3 -m pytest tests/infrastructure/ tests/test_coverage_completion.py \
        --ignore=tests/integration/test_module_interoperability.py \
        -m "not requires_ollama" \
        --cov=infrastructure \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=49 \
        -v --tb=short
}

run_pytest_project() {
    # Execute project tests with coverage requirements.
    # Runs pytest on project/tests/ with 70% coverage threshold.
    # Skips integration tests by default.
    # Returns: 0 on success, 1 on failure
    cd "$REPO_ROOT"
    
    log_info "Running project tests..."
    
    python3 -m pytest project/tests/ \
        --ignore=project/tests/integration \
        --cov=project/src \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=70 \
        -v --tb=short
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
    
    if run_pytest_infrastructure; then
        log_success "Infrastructure tests passed"
        return 0
    else
        log_error "Infrastructure tests failed"
        return 1
    fi
}

run_project_tests() {
    log_header "PROJECT TESTS"
    
    if run_pytest_project; then
        log_success "Project tests passed"
        return 0
    else
        log_error "Project tests failed"
        return 1
    fi
}

run_analysis() {
    # Execute project analysis scripts from project/scripts/.
    # Discovers and runs all Python scripts in project/scripts/ directory.
    # Returns: 0 on success, 1 on failure
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
    local resume_flag="${1:-}"
    log_header "COMPLETE RESEARCH PROJECT PIPELINE"
    
    local pipeline_start=$(date +%s)
    
    log_info "Repository: $REPO_ROOT"
    log_info "Python: $(python3 --version)"
    echo
    
    # Check for checkpoint if resuming
    if [[ "$resume_flag" == "--resume" ]]; then
        log_info "Checking for checkpoint..."
        if python3 -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); valid, msg = cm.validate_checkpoint(); exit(0 if valid else 1)" 2>/dev/null; then
            log_success "Checkpoint found - resuming pipeline"
        else
            log_warning "No valid checkpoint found - starting fresh pipeline"
            resume_flag=""
        fi
    fi
    
    # Reset stage tracking
    STAGE_RESULTS=()
    STAGE_DURATIONS=()
    
    # Stage 0: Clean output directories (skip if resuming)
    if [[ "$resume_flag" != "--resume" ]]; then
        clean_output_directories
    else
        log_info "Skipping clean stage (resuming from checkpoint)"
    fi
    
    # For resume, use Python script with --resume flag
    if [[ "$resume_flag" == "--resume" ]]; then
        cd "$REPO_ROOT"
        if python3 scripts/run_all.py --resume; then
            log_success "Pipeline resumed and completed"
            return 0
        else
            log_error "Pipeline resume failed"
            return 1
        fi
    fi
    
    # Stage 1: Setup Environment
    local stage_start=$(date +%s)
    if ! run_setup_environment; then
        log_error "Pipeline failed at Stage 1 (Setup Environment)"
        log_info "  Troubleshooting:"
        log_info "    - Check Python version: python3 --version (requires >=3.10)"
        log_info "    - Verify dependencies: pip list | grep -E '(numpy|matplotlib|pytest)'"
        log_info "    - Check script: python3 scripts/00_setup_environment.py"
        return 1
    fi
    local stage_end=$(date +%s)
    STAGE_RESULTS[0]=0
    STAGE_DURATIONS[0]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 2: Infrastructure Tests
    stage_start=$(date +%s)
    log_stage 2 "Infrastructure Tests" 9 "$pipeline_start"
    if ! run_pytest_infrastructure; then
        log_error "Pipeline failed at Stage 2 (Infrastructure Tests)"
        log_info "  Troubleshooting:"
        log_info "    - Run tests manually: python3 -m pytest tests/infrastructure/ -v"
        log_info "    - Check coverage: python3 -m pytest tests/infrastructure/ --cov=infrastructure --cov-report=term"
        log_info "    - View HTML report: open htmlcov/index.html"
        return 1
    fi
    log_success "Infrastructure tests passed"
    stage_end=$(date +%s)
    STAGE_RESULTS[1]=0
    STAGE_DURATIONS[1]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 3: Project Tests
    stage_start=$(date +%s)
    log_stage 3 "Project Tests" 9 "$pipeline_start"
    if ! run_pytest_project; then
        log_error "Pipeline failed at Stage 3 (Project Tests)"
        log_info "  Troubleshooting:"
        log_info "    - Run tests manually: python3 -m pytest project/tests/ -v"
        log_info "    - Check specific test: python3 -m pytest project/tests/test_example.py -v"
        log_info "    - View coverage: python3 -m pytest project/tests/ --cov=project/src --cov-report=term"
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
        log_info "  Troubleshooting:"
        log_info "    - Check analysis scripts: ls project/scripts/*.py"
        log_info "    - Run script manually: python3 project/scripts/analysis_pipeline.py"
        log_info "    - Verify outputs: ls project/output/figures/ project/output/data/"
        log_info "    - Check logs for specific script errors above"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[3]=0
    STAGE_DURATIONS[3]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 5: PDF Rendering
    stage_start=$(date +%s)
    log_stage 5 "PDF Rendering" 9 "$pipeline_start"
    cd "$REPO_ROOT"
    if ! python3 scripts/03_render_pdf.py; then
        log_error "Pipeline failed at Stage 5 (PDF Rendering)"
        log_info "  Troubleshooting:"
        log_info "    - Check LaTeX installation: which xelatex"
        log_info "    - Verify manuscript files: ls project/manuscript/*.md"
        log_info "    - Check figure paths: ls project/output/figures/"
        log_info "    - View compilation logs: ls project/output/pdf/*.log"
        log_info "    - Run manually: python3 scripts/03_render_pdf.py"
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
        log_info "  Troubleshooting:"
        log_info "    - Validate PDFs: python3 -m infrastructure.validation.cli pdf project/output/pdf/"
        log_info "    - Validate markdown: python3 -m infrastructure.validation.cli markdown project/manuscript/"
        log_info "    - Check validation report: cat project/output/validation_report.md"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[5]=0
    STAGE_DURATIONS[5]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 7: Copy Outputs
    stage_start=$(date +%s)
    if ! run_copy_outputs; then
        log_error "Pipeline failed at Stage 7 (Copy Outputs)"
        log_info "  Troubleshooting:"
        log_info "    - Check source directory: ls project/output/"
        log_info "    - Check destination: ls output/"
        log_info "    - Verify permissions: ls -la project/output/"
        log_info "    - Run manually: python3 scripts/05_copy_outputs.py"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[6]=0
    STAGE_DURATIONS[6]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 8: LLM Scientific Review (optional - graceful degradation)
    stage_start=$(date +%s)
    log_stage 8 "LLM Scientific Review" 9 "$pipeline_start"
    cd "$REPO_ROOT"
    log_info "Running LLM scientific review (requires Ollama)..."
    log_info "Note: This stage is optional - pipeline will continue even if it fails"
    local exit_code
    python3 scripts/06_llm_review.py --reviews-only
    exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM scientific review complete"
        STAGE_RESULTS[7]=0
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "LLM scientific review skipped (Ollama not available)"
        log_info "  To enable: start Ollama with 'ollama serve' and install a model"
        log_info "  Recommended: ollama pull llama3-gradient"
        STAGE_RESULTS[7]=2  # Mark as skipped
    else
        log_warning "LLM scientific review failed (exit code: $exit_code)"
        log_info "  This is an optional stage - pipeline will continue"
        log_info "  Check Ollama status: ollama ps"
        log_info "  Check logs: project/output/llm/"
        STAGE_RESULTS[7]=1  # Mark as failed but don't stop pipeline
    fi
    stage_end=$(date +%s)
    STAGE_DURATIONS[7]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 9: LLM Translations (optional - graceful degradation)
    stage_start=$(date +%s)
    log_stage 9 "LLM Translations" 9 "$pipeline_start"
    cd "$REPO_ROOT"
    log_info "Running LLM translations (requires Ollama)..."
    log_info "Note: This stage is optional - pipeline will continue even if it fails"
    python3 scripts/06_llm_review.py --translations-only
    exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM translations complete"
        STAGE_RESULTS[8]=0
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "LLM translations skipped (Ollama not available or no languages configured)"
        log_info "  To enable: configure translations in project/manuscript/config.yaml"
        log_info "  Example: llm.translations.enabled: true, languages: [zh, hi, ru]"
        STAGE_RESULTS[8]=2  # Mark as skipped
    else
        log_warning "LLM translations failed (exit code: $exit_code)"
        log_info "  This is an optional stage - pipeline will continue"
        log_info "  Check Ollama status: ollama ps"
        log_info "  Check configuration: project/manuscript/config.yaml"
        STAGE_RESULTS[8]=1  # Mark as failed but don't stop pipeline
    fi
    stage_end=$(date +%s)
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
    local total_stage_time=0
    local slowest_stage_idx=0
    local slowest_duration=0
    local fastest_stage_idx=0
    local fastest_duration=999999
    
    for ((i=0; i<num_stages; i++)); do
        local stage_name="${STAGE_NAMES[$i]}"
        local duration="${STAGE_DURATIONS[$i]}"
        local duration_formatted=$(format_duration "$duration")
        local percentage=0
        if [[ $total_duration -gt 0 ]]; then
            percentage=$((duration * 100 / total_duration))
        fi
        
        total_stage_time=$((total_stage_time + duration))
        
        # Track slowest stage
        if [[ $duration -gt $slowest_duration ]]; then
            slowest_duration=$duration
            slowest_stage_idx=$i
        fi
        
        # Track fastest stage (skip stage 0 which is usually very fast)
        if [[ $i -gt 0 ]] && [[ $duration -lt $fastest_duration ]]; then
            fastest_duration=$duration
            fastest_stage_idx=$i
        fi
        
        # Highlight slowest stage
        if [[ $i -eq $slowest_stage_idx ]] && [[ $slowest_duration -gt 10 ]]; then
            echo -e "  ${GREEN}✓${NC} Stage $((i+1)): ${stage_name} (${duration_formatted}) ${YELLOW}${percentage}%${NC} ${YELLOW}⚠ bottleneck${NC}"
        else
            echo -e "  ${GREEN}✓${NC} Stage $((i+1)): ${stage_name} (${duration_formatted}) ${percentage}%"
        fi
    done
    
    echo
    echo "Performance Metrics:"
    echo "  Total Execution Time: $(format_duration "$total_duration")"
    
    if [[ $num_stages -gt 0 ]]; then
        local avg_time=$((total_stage_time / num_stages))
        echo "  Average Stage Time: $(format_duration "$avg_time")"
    fi
    
    if [[ $slowest_duration -gt 0 ]]; then
        local slowest_name="${STAGE_NAMES[$slowest_stage_idx]}"
        local slowest_formatted=$(format_duration "$slowest_duration")
        local slowest_pct=$((slowest_duration * 100 / total_duration))
        echo "  Slowest Stage: Stage $((slowest_stage_idx + 1)) - ${slowest_name} (${slowest_formatted}, ${slowest_pct}%)"
    fi
    
    if [[ $fastest_duration -lt 999999 ]] && [[ $fastest_stage_idx -gt 0 ]]; then
        local fastest_name="${STAGE_NAMES[$fastest_stage_idx]}"
        local fastest_formatted=$(format_duration "$fastest_duration")
        echo "  Fastest Stage: Stage $((fastest_stage_idx + 1)) - ${fastest_name} (${fastest_formatted})"
    fi
    
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
    echo "  --resume            Resume pipeline from last checkpoint (use with --pipeline)"
    echo
    echo "LLM Operations (requires Ollama):"
    echo "  --reviews           Run LLM manuscript review (English)"
    echo "  --translations      Run LLM translations (multi-language)"
    echo
    echo "Literature Operations (requires Ollama):"
    echo "  --search            Search literature (add to bibliography)"
    echo "  --download          Download PDFs (for bibliography entries)"
    echo "  --summarize         Generate summaries (for papers with PDFs)"
    echo "  --cleanup           Cleanup library (remove papers without PDFs)"
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
    echo "  10 Cleanup library (remove papers without PDFs)"
    echo "  11 Advanced LLM operations (literature review, etc.)"
    echo "  12 Exit"
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
    echo "  $0 --cleanup             # Cleanup library (remove papers without PDFs)"
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
                # Check if next argument is --resume
                if [[ "${2:-}" == "--resume" ]]; then
                    shift  # Remove --pipeline
                    shift  # Remove --resume
                    run_full_pipeline "--resume"
                    exit $?
                else
                    run_non_interactive 4
                    exit $?
                fi
                ;;
            --resume)
                # Resume flag must be used with --pipeline
                log_error "--resume must be used with --pipeline"
                log_info "Usage: $0 --pipeline --resume"
                exit 1
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
            --cleanup)
                run_non_interactive 10
                exit $?
                ;;
            --llm-operation)
                run_non_interactive 11
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
        
        echo -n "Select option [1-12]: "
        read -r choice
        
        handle_menu_choice "$choice"
        
        # Return to menu after operation (except for exit)
        if [[ "$choice" != "12" ]]; then
            press_enter_to_continue
        fi
    done
}

# Run main
main "$@"

