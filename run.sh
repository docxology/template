#!/usr/bin/env bash

################################################################################
# Unified Research Project Pipeline Orchestrator
#
# A single entry point for all pipeline operations with interactive menu:
#
# Core Pipeline Scripts (aligned with script numbering):
#   0. Setup Environment (00_setup_environment.py)
#   1. Run Tests (01_run_tests.py - infrastructure + project)
#   2. Run Analysis (02_run_analysis.py)
#   3. Render PDF (03_render_pdf.py)
#   4. Validate Output (04_validate_output.py)
#   5. Copy Outputs (05_copy_outputs.py)
#   6. LLM Review (requires Ollama) (06_llm_review.py)
#   7. Literature Search (07_literature_search.py)
#
# Orchestration:
#   8. Run Full Pipeline (10 stages: 0-9, via run.sh)
#
# Literature Sub-Operations (via 07_literature_search.py):
#   9. Search only (network only)
#   10. Download only (network only)
#   11. Summarize (requires Ollama)
#   12. Cleanup (local files only)
#   13. Advanced LLM operations (requires Ollama)
#
#   14. Exit
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
# Note: Stage 0 (Clean Output Directories) is not in this array as it's a pre-pipeline step.
# This array tracks stages 1-9, which are displayed as [1/9] to [9/9] in progress logs.
declare -a STAGE_NAMES=(
    "Setup Environment"        # Stage 1
    "Infrastructure Tests"     # Stage 2
    "Project Tests"            # Stage 3
    "Project Analysis"         # Stage 4
    "PDF Rendering"            # Stage 5
    "Output Validation"        # Stage 6
    "Copy Outputs"            # Stage 7
    "LLM Scientific Review"   # Stage 8 (optional)
    "LLM Translations"        # Stage 9 (optional)
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
    echo -e "${BOLD}Core Pipeline Scripts (aligned with script numbering):${NC}"
    echo "  0. Setup Environment (00_setup_environment.py)"
    echo "  1. Run Tests (01_run_tests.py - infrastructure + project)"
    echo "  2. Run Analysis (02_run_analysis.py)"
    echo "  3. Render PDF (03_render_pdf.py)"
    echo "  4. Validate Output (04_validate_output.py)"
    echo "  5. Copy Outputs (05_copy_outputs.py)"
    echo -e "  6. LLM Review ${YELLOW}(requires Ollama)${NC} (06_llm_review.py)"
    echo "  7. Literature Search (07_literature_search.py)"
    echo
    echo -e "${BOLD}Orchestration:${NC}"
    echo "  8. Run Full Pipeline (10 stages: 0-9, via run.sh)"
    echo
    echo -e "${BOLD}Literature Sub-Operations (via 07_literature_search.py):${NC}"
    echo -e "  9. Search only ${CYAN}(network only)${NC}"
    echo -e "  10. Download only ${CYAN}(network only)${NC}"
    echo -e "  11. Summarize ${YELLOW}(requires Ollama)${NC}"
    echo -e "  12. Cleanup ${CYAN}(local files only)${NC}"
    echo -e "  13. Advanced LLM operations ${YELLOW}(requires Ollama)${NC}"
    echo
    echo "  14. Exit"
    echo
    echo -e "${BLUE}============================================================${NC}"
    echo -e "  Repository: ${CYAN}$REPO_ROOT${NC}"
    echo -e "  Python: ${CYAN}$(python3 --version 2>&1)${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo
    echo -e "${CYAN}Tip:${NC} Enter multiple digits to chain steps (e.g., 345 for analysis → render → validate). Comma forms like 3,4,5 work too."
}

# ============================================================================
# Clean Output Directories
# ============================================================================

clean_output_directories() {
    # Clean and recreate output directories for fresh pipeline run.
    # Removes all files from project/output/ and root output/ directories,
    # then recreates the standard directory structure.
    # This ensures no stale files from previous runs interfere with current execution.
    # Log files are preserved in logs/archive/ directory.
    echo
    echo -e "${YELLOW}[0/9] Clean Output Directories${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local project_output="$REPO_ROOT/project/output"
    local root_output="$REPO_ROOT/output"
    
    # Archive old log files before cleanup
    if [[ -d "$project_output/logs" ]]; then
        local archive_dir="$project_output/logs/archive"
        mkdir -p "$archive_dir"
        for log_file in "$project_output/logs"/*.log; do
            if [[ -f "$log_file" ]]; then
                mv "$log_file" "$archive_dir/" 2>/dev/null || true
            fi
        done
    fi
    
    if [[ -d "$root_output/logs" ]]; then
        local archive_dir="$root_output/logs/archive"
        mkdir -p "$archive_dir"
        for log_file in "$root_output/logs"/*.log; do
            if [[ -f "$log_file" ]]; then
                mv "$log_file" "$archive_dir/" 2>/dev/null || true
            fi
        done
    fi
    
    # Clean project/output/
    if [[ -d "$project_output" ]]; then
        log_info "Cleaning project/output/..."
        rm -rf "$project_output"/*
        mkdir -p "$project_output"/{pdf,figures,data,reports,simulations,slides,web,llm,logs}
        log_success "Cleaned project/output/ (recreated subdirectories)"
    else
        mkdir -p "$project_output"/{pdf,figures,data,reports,simulations,slides,web,llm,logs}
        log_info "Created project/output/ directory structure"
    fi
    
    # Clean root output/
    if [[ -d "$root_output" ]]; then
        log_info "Cleaning output/..."
        rm -rf "$root_output"/*
        mkdir -p "$root_output"/{pdf,figures,data,reports,simulations,slides,web,llm,logs}
        log_success "Cleaned output/ (recreated subdirectories)"
    else
        mkdir -p "$root_output"/{pdf,figures,data,reports,simulations,slides,web,llm,logs}
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
    
    python3 -m pytest tests/infrastructure/ \
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
    # Standalone environment setup (menu option 0)
    log_header "SETUP ENVIRONMENT (00_setup_environment.py)"
    
    cd "$REPO_ROOT"
    if python3 scripts/00_setup_environment.py; then
        log_success "Environment setup complete"
        return 0
    else
        log_error "Environment setup failed"
        return 1
    fi
}

run_all_tests() {
    # Run both infrastructure and project tests via 01_run_tests.py
    log_header "RUN TESTS (01_run_tests.py)"
    
    cd "$REPO_ROOT"
    if python3 scripts/01_run_tests.py; then
        log_success "All tests passed"
        return 0
    else
        log_error "Tests failed"
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

run_analysis_standalone() {
    # Standalone analysis execution (menu option 2)
    log_header "RUN ANALYSIS (02_run_analysis.py)"
    
    cd "$REPO_ROOT"
    
    if python3 scripts/02_run_analysis.py; then
        log_success "Analysis complete"
        return 0
    else
        log_error "Analysis failed"
        return 1
    fi
}

run_pdf_rendering() {
    log_header "PDF RENDERING (03_render_pdf.py)"
    
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

run_validation_standalone() {
    # Standalone validation execution (menu option 4)
    log_header "VALIDATE OUTPUT (04_validate_output.py)"
    
    cd "$REPO_ROOT"
    
    if python3 scripts/04_validate_output.py; then
        log_success "Validation complete"
        return 0
    else
        log_error "Validation failed"
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

run_copy_outputs_standalone() {
    # Standalone copy outputs execution (menu option 5)
    log_header "COPY OUTPUTS (05_copy_outputs.py)"
    
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

run_llm_review() {
    # Run both reviews and translations (menu option 6)
    log_header "LLM REVIEW (06_llm_review.py)"
    
    cd "$REPO_ROOT"
    
    log_info "Running LLM review (requires Ollama)..."
    log_info "This will run both reviews and translations"
    
    local exit_code
    python3 scripts/06_llm_review.py
    exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM review complete"
        return 0
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "LLM review skipped (Ollama not available)"
        log_info "To enable: start Ollama with 'ollama serve' and install a model"
        return 0  # Not a failure, just skipped
    else
        log_error "LLM review failed"
        return 1
    fi
}

run_literature_search_all() {
    # Run all literature operations interactively (menu option 7)
    log_header "LITERATURE SEARCH (07_literature_search.py)"
    
    cd "$REPO_ROOT"
    
    log_info "Running literature search (all operations)..."
    log_info "This will search, download, and optionally summarize papers"
    
    if python3 scripts/07_literature_search.py --search --summarize; then
        log_success "Literature search complete"
        return 0
    else
        log_error "Literature search failed"
        return 1
    fi
}

run_literature_search() {
    # Network-only operation: Searches arXiv and Semantic Scholar APIs
    # Does NOT require Ollama
    log_header "LITERATURE SEARCH (ADD TO BIBLIOGRAPHY)"

    cd "$REPO_ROOT"

    log_info "Searching literature and adding papers to bibliography (network only)..."

    if python3 scripts/07_literature_search.py --search-only; then
        log_success "Literature search complete"
        return 0
    else
        log_error "Literature search failed"
        return 1
    fi
}

run_literature_download() {
    # Network-only operation: Downloads PDFs via HTTP
    # Does NOT require Ollama
    log_header "DOWNLOAD PDFs (FOR BIBLIOGRAPHY ENTRIES)"

    cd "$REPO_ROOT"

    log_info "Downloading PDFs for bibliography entries without PDFs (network only)..."

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
    # Local files-only operation: Removes files from filesystem
    # Does NOT require Ollama or network
    log_header "CLEANUP LIBRARY (REMOVE PAPERS WITHOUT PDFs)"

    cd "$REPO_ROOT"

    log_info "Cleaning up library by removing papers without PDFs (local files only)..."

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
    
    # Initialize log file capture
    # Write to project/output/logs during execution, will be copied to output/logs in copy stage
    local log_dir="$REPO_ROOT/project/output/logs"
    mkdir -p "$log_dir"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local log_file="$log_dir/pipeline_${timestamp}.log"
    export PIPELINE_LOG_FILE="$log_file"
    
    # Function to strip ANSI color codes for log file
    strip_ansi_codes() {
        sed -u 's/\x1b\[[0-9;]*m//g'
    }
    
    # Set up signal handlers for graceful interruption
    local current_stage=0
    local pipeline_start=0
    
    handle_pipeline_interrupt() {
        local log_file_path="${PIPELINE_LOG_FILE:-$log_file}"
        echo ""
        echo -e "${YELLOW}⚠${NC} Pipeline interrupted (Ctrl+C detected)"
        echo -e "${YELLOW}⚠${NC} Saving checkpoint..."
        
        # Log to file
        {
            echo ""
            echo "============================================================"
            echo "⚠ Pipeline interrupted (Ctrl+C detected) at stage $current_stage"
            echo "  Time: $(date)"
            echo "============================================================"
        } >> "$log_file_path" 2>/dev/null || true
        
        # Save checkpoint if possible
        if [[ -n "$pipeline_start" ]] && [[ "$pipeline_start" -gt 0 ]]; then
            if python3 -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); cm.save_checkpoint(pipeline_start_time=$pipeline_start, last_stage_completed=$current_stage, stage_results=[], total_stages=9)" 2>/dev/null; then
                log_success "Checkpoint saved"
                echo "✓ Checkpoint saved" >> "$log_file_path" 2>/dev/null || true
            fi
        fi
        
        echo -e "${CYAN}To resume: ./run.sh --pipeline --resume${NC}"
        echo -e "${CYAN}Log file: $log_file_path${NC}"
        
        # Log resume instructions to file
        {
            echo "To resume: ./run.sh --pipeline --resume"
            echo "Log file: $log_file_path"
            echo "============================================================"
        } >> "$log_file_path" 2>/dev/null || true
        
        exit 130  # Exit code 130 for SIGINT
    }
    
    trap 'handle_pipeline_interrupt' INT TERM
    
    log_header_to_file "COMPLETE RESEARCH PROJECT PIPELINE"
    
    pipeline_start=$(date +%s)
    
    log_info_to_file "Repository: $REPO_ROOT"
    log_info_to_file "Python: $(python3 --version)"
    log_info_to_file "Log file: $log_file"
    echo
    
    # Log initial header to file (without colors)
    {
        echo "============================================================"
        echo "  COMPLETE RESEARCH PROJECT PIPELINE"
        echo "============================================================"
        echo ""
        echo "Repository: $REPO_ROOT"
        echo "Python: $(python3 --version)"
        echo "Log file: $log_file"
        echo "Pipeline started: $(date)"
        echo ""
    } >> "$log_file"
    
    # Check for checkpoint if resuming
    if [[ "$resume_flag" == "--resume" ]]; then
        log_info_to_file "Checking for checkpoint..."
        if python3 -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); valid, msg = cm.validate_checkpoint(); exit(0 if valid else 1)" 2>/dev/null; then
            log_success_to_file "Checkpoint found - resuming pipeline"
        else
            log_warning_to_file "No valid checkpoint found - starting fresh pipeline"
            resume_flag=""
        fi
    fi
    
    # Reset stage tracking
    STAGE_RESULTS=()
    STAGE_DURATIONS=()
    
    # Stage 0: Clean output directories (skip if resuming)
    if [[ "$resume_flag" != "--resume" ]]; then
        clean_output_directories 2>&1 | tee -a "$log_file" || true
    else
        log_info_to_file "Skipping clean stage (resuming from checkpoint)"
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
    current_stage=1
    local stage_start=$(date +%s)
    run_setup_environment 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
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
    current_stage=2
    stage_start=$(date +%s)
    log_stage 2 "Infrastructure Tests" 9 "$pipeline_start"
    {
        echo ""
        echo "[2/9] Infrastructure Tests (22% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_pytest_infrastructure 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error_to_file "Pipeline failed at Stage 2 (Infrastructure Tests)"
        log_info_to_file "  Troubleshooting:"
        log_info_to_file "    - Run tests manually: python3 -m pytest tests/infrastructure/ -v"
        log_info_to_file "    - Check coverage: python3 -m pytest tests/infrastructure/ --cov=infrastructure --cov-report=term"
        log_info_to_file "    - View HTML report: open htmlcov/index.html"
        return 1
    fi
    log_success_to_file "Infrastructure tests passed"
    stage_end=$(date +%s)
    STAGE_RESULTS[1]=0
    STAGE_DURATIONS[1]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 3: Project Tests
    current_stage=3
    stage_start=$(date +%s)
    log_stage 3 "Project Tests" 9 "$pipeline_start"
    {
        echo ""
        echo "[3/9] Project Tests (33% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_pytest_project 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error_to_file "Pipeline failed at Stage 3 (Project Tests)"
        log_info_to_file "  Troubleshooting:"
        log_info_to_file "    - Run tests manually: python3 -m pytest project/tests/ -v"
        log_info_to_file "    - Check specific test: python3 -m pytest project/tests/test_example.py -v"
        log_info_to_file "    - View coverage: python3 -m pytest project/tests/ --cov=project/src --cov-report=term"
        return 1
    fi
    log_success_to_file "Project tests passed"
    stage_end=$(date +%s)
    STAGE_RESULTS[2]=0
    STAGE_DURATIONS[2]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 4: Analysis
    current_stage=4
    stage_start=$(date +%s)
    run_analysis 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
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
    current_stage=5
    stage_start=$(date +%s)
    log_stage 5 "PDF Rendering" 9 "$pipeline_start"
    cd "$REPO_ROOT"
    python3 scripts/03_render_pdf.py 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
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
    current_stage=6
    stage_start=$(date +%s)
    run_validation 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
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
    current_stage=7
    stage_start=$(date +%s)
    run_copy_outputs 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
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
    current_stage=8
    stage_start=$(date +%s)
    log_stage 8 "LLM Scientific Review" 9 "$pipeline_start"
    cd "$REPO_ROOT"
    log_info "Running LLM scientific review (requires Ollama)..."
    log_info "Note: This stage is optional - pipeline will continue even if it fails"
    local exit_code
    python3 scripts/06_llm_review.py --reviews-only 2>&1 | tee -a "$log_file" || true
    exit_code=${PIPESTATUS[0]}
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
    current_stage=9
    stage_start=$(date +%s)
    log_stage 9 "LLM Translations" 9 "$pipeline_start"
    cd "$REPO_ROOT"
    log_info "Running LLM translations (requires Ollama)..."
    log_info "Note: This stage is optional - pipeline will continue even if it fails"
    python3 scripts/06_llm_review.py --translations-only 2>&1 | tee -a "$log_file" || true
    exit_code=${PIPESTATUS[0]}
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
    
    print_pipeline_summary "$total_duration" "$log_file"
    
    # Log completion to file
    {
        echo ""
        echo "============================================================"
        echo "Pipeline completed: $(date)"
        echo "Total duration: $(format_duration "$total_duration")"
        echo "Log file: $log_file"
        echo "  (Will be copied to output/logs/ during copy stage)"
        echo "============================================================"
    } >> "$log_file"
    
    # Clear trap
    trap - INT TERM
    
    return 0
}

print_pipeline_summary() {
    local total_duration="$1"
    local log_file="${2:-}"
    local num_stages="${#STAGE_NAMES[@]}"
    
    echo
    log_header "PIPELINE SUMMARY"
    
    log_success "All stages completed successfully!"
    if [[ -n "$log_file" ]]; then
        # Show both current location and final location after copy
        local log_file_final="${log_file/project\/output/output}"
        log_info "Full pipeline log: $log_file"
        log_info "  (Will be available at: $log_file_final after copy stage)"
    fi
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
    if [[ -n "$log_file" ]]; then
        echo "  • Pipeline log: $log_file"
    fi
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
    local exit_code=0
    
    start_time=$(date +%s)
    
    case "$choice" in
        0)
            run_setup_environment
            exit_code=$?
            ;;
        1)
            run_all_tests
            exit_code=$?
            ;;
        2)
            run_analysis_standalone
            exit_code=$?
            ;;
        3)
            run_pdf_rendering
            exit_code=$?
            ;;
        4)
            run_validation_standalone
            exit_code=$?
            ;;
        5)
            run_copy_outputs_standalone
            exit_code=$?
            ;;
        6)
            run_llm_review
            exit_code=$?
            ;;
        7)
            run_literature_search_all
            exit_code=$?
            ;;
        8)
            run_full_pipeline
            exit_code=$?
            ;;
        9)
            run_literature_search
            exit_code=$?
            ;;
        10)
            run_literature_download
            exit_code=$?
            ;;
        11)
            run_literature_summarize
            exit_code=$?
            ;;
        12)
            run_literature_cleanup
            exit_code=$?
            ;;
        13)
            run_literature_llm_operations
            exit_code=$?
            ;;
        14)
            echo
            log_info "Exiting. Goodbye!"
            exit 0
            ;;
        *)
            log_error "Invalid option: $choice"
            log_info "Please enter a number between 0 and 14"
            exit_code=1
            ;;
    esac
    
    end_time=$(date +%s)
    duration=$(get_elapsed_time "$start_time" "$end_time")
    
    echo
    log_info "Operation completed in $(format_duration "$duration")"
    return $exit_code
}

# Run a sequence of menu options in order, stopping on first failure.
run_option_sequence() {
    local -a options=("$@")
    local exit_code=0

    if [[ ${#options[@]} -gt 0 ]]; then
        log_info "Running sequence: ${options[*]}"
    fi

    for opt in "${options[@]}"; do
        handle_menu_choice "$opt"
        exit_code=$?
        if [[ $exit_code -ne 0 ]]; then
            log_error "Sequence aborted at option $opt (exit code $exit_code)"
            return $exit_code
        fi
    done

    return $exit_code
}

# ============================================================================
# Non-Interactive Mode
# ============================================================================

run_non_interactive() {
    local option="$1"
    
    log_header "NON-INTERACTIVE MODE"

    if parse_choice_sequence "$option" && [[ ${#SHORTHAND_CHOICES[@]} -gt 1 ]]; then
        log_info "Running shorthand sequence: ${SHORTHAND_CHOICES[*]}"
        run_option_sequence "${SHORTHAND_CHOICES[@]}"
        exit $?
    fi

    log_info "Running option: $option"
    handle_menu_choice "$option"
    exit $?
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
    echo "Literature Operations:"
    echo "  --search            Search literature (network only, add to bibliography)"
    echo "  --download          Download PDFs (network only, for bibliography entries)"
    echo "  --summarize         Generate summaries (requires Ollama, for papers with PDFs)"
    echo "  --cleanup           Cleanup library (local files only, remove papers without PDFs)"
    echo
    echo "Menu Options:"
    echo
    echo "Core Pipeline Scripts (aligned with script numbering):"
    echo "  0  Setup Environment (00_setup_environment.py)"
    echo "  1  Run Tests (01_run_tests.py - infrastructure + project)"
    echo "  2  Run Analysis (02_run_analysis.py)"
    echo "  3  Render PDF (03_render_pdf.py)"
    echo "  4  Validate Output (04_validate_output.py)"
    echo "  5  Copy Outputs (05_copy_outputs.py)"
    echo "  6  LLM Review (requires Ollama) (06_llm_review.py)"
    echo "  7  Literature Search (07_literature_search.py)"
    echo
    echo "Orchestration:"
    echo "  8  Run Full Pipeline (10 stages: 0-9, via run.sh)"
    echo
    echo "Literature Sub-Operations (via 07_literature_search.py):"
    echo "  9  Search only (network only)"
    echo "  10 Download only (network only)"
    echo "  11 Summarize (requires Ollama)"
    echo "  12 Cleanup (local files only)"
    echo "  13 Advanced LLM operations (requires Ollama)"
    echo "  14 Exit"
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
    echo "Note: --option N is also supported for compatibility (0-14)"
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
                run_infrastructure_tests
                exit $?
                ;;
            --project-tests|--tests-project)
                run_project_tests
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
                    run_non_interactive 8
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
                run_llm_scientific_review
                exit $?
                ;;
            --translations)
                run_llm_translations
                exit $?
                ;;
            --search)
                run_non_interactive 9
                exit $?
                ;;
            --download)
                run_non_interactive 10
                exit $?
                ;;
            --summarize)
                run_non_interactive 11
                exit $?
                ;;
            --cleanup)
                run_non_interactive 12
                exit $?
                ;;
            --llm-operation)
                run_non_interactive 13
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
        
        echo -n "Select option [0-14]: "
        read -r choice

        local exit_code=0
        local prompt_for_continue=true
        if parse_choice_sequence "$choice" && [[ ${#SHORTHAND_CHOICES[@]} -gt 1 ]]; then
            run_option_sequence "${SHORTHAND_CHOICES[@]}"
            exit_code=$?
            # Skip prompt if cleanup (12) included
            for opt in "${SHORTHAND_CHOICES[@]}"; do
                if [[ "$opt" == "12" ]]; then
                    prompt_for_continue=false
                    break
                fi
            done
        else
            handle_menu_choice "$choice"
            exit_code=$?
            if [[ "$choice" == "12" ]]; then
                prompt_for_continue=false
            fi
        fi

        if [[ $exit_code -ne 0 ]]; then
            log_error "Last operation exited with code $exit_code"
        fi

        if [[ "$choice" != "14" && "$prompt_for_continue" == true ]]; then
            press_enter_to_continue
        fi
    done
}

# Run main
main "$@"

