#!/usr/bin/env bash

################################################################################
# Research Project Template - Main Entry Point
#
# Entry point for manuscript pipeline operations with interactive menu:
#
# Core Pipeline Scripts (aligned with script numbering):
#   0. Setup Environment (00_setup_environment.py)
#   1. Run Tests (01_run_tests.py - infrastructure + project)
#   2. Run Analysis (02_run_analysis.py)
#   3. Render PDF (03_render_pdf.py)
#   4. Validate Output (04_validate_output.py)
#   5. Copy Outputs (05_copy_outputs.py)
#   6. LLM Review (requires Ollama) (06_llm_review.py --reviews-only)
#   7. LLM Translations (requires Ollama) (06_llm_review.py --translations-only)
#
# Orchestration:
#   8. Run Full Pipeline (10 stages: 0-9)
#
# Non-interactive mode: Use dedicated flags (--pipeline, --infra-tests, etc.)
#
# Exit codes: 0 = success, 1 = failure, 2 = skipped (for optional stages)
################################################################################

set -euo pipefail

# ============================================================================
# Bash Version Check
# ============================================================================

check_bash_compatibility() {
    # Check bash version and shell compatibility.
    # Warns if running under incompatible shell or old bash version.
    # Note: Script uses bash 3.2+ compatible features (no associative arrays).
    local shell_name="${BASH_VERSION:-}"
    local shell_type=""
    
    # Detect shell type
    if [[ -n "${ZSH_VERSION:-}" ]]; then
        shell_type="zsh"
        log_warning "Running under zsh. This script is designed for bash."
        log_info "For best compatibility, run with: bash $0"
    elif [[ -n "$shell_name" ]]; then
        shell_type="bash"
        # Extract major and minor version
        local major="${BASH_VERSINFO[0]:-0}"
        local minor="${BASH_VERSINFO[1]:-0}"
        
        if [[ $major -lt 3 ]] || [[ ($major -eq 3 && $minor -lt 2) ]]; then
            log_warning "Bash version $major.$minor detected. Bash 3.2+ recommended."
        fi
    else
        log_warning "Unable to detect shell version. Script may not work correctly."
        log_info "For best compatibility, run with: bash $0"
    fi
}

# Source shared utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/scripts/bash_utils.sh"

# Check bash compatibility (non-fatal warning)
check_bash_compatibility || true

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
# Menu Display
# ============================================================================

display_menu() {
    clear
    echo -e "${BOLD}${BLUE}"
    echo "============================================================"
    echo "  Manuscript Pipeline - Main Menu"
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
    echo -e "  6. LLM Review ${YELLOW}(requires Ollama)${NC} (06_llm_review.py --reviews-only)"
    echo -e "  7. LLM Translations ${YELLOW}(requires Ollama)${NC} (06_llm_review.py --translations-only)"
    echo
    echo -e "${BOLD}Orchestration:${NC}"
    echo "  8. Run Full Pipeline (10 stages: 0-9)"
    echo "  9. Run Full Pipeline (skip infrastructure tests)"
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
    # Runs pytest on tests/infrastructure/ with 60% coverage threshold.
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
        --cov-fail-under=60 \
        -v --tb=short
}

run_pytest_project() {
    # Execute project tests with coverage requirements.
    # Runs pytest on project/tests/ with 90% coverage threshold.
    # Skips integration tests by default.
    # Returns: 0 on success, 1 on failure
    cd "$REPO_ROOT"
    
    log_info "Running project tests..."
    
    python3 -m pytest project/tests/ \
        --ignore=project/tests/integration \
        --cov=project/src \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=90 \
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
    log_stage 1 "Setup Environment" 9 "$pipeline_start"
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
    
    print_pipeline_summary "$total_duration" "$log_file" "false"
    
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

run_full_pipeline_no_infra() {
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
            if python3 -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); cm.save_checkpoint(pipeline_start_time=$pipeline_start, last_stage_completed=$current_stage, stage_results=[], total_stages=8)" 2>/dev/null; then
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
    
    log_header_to_file "COMPLETE RESEARCH PROJECT PIPELINE (SKIP INFRASTRUCTURE TESTS)"
    
    pipeline_start=$(date +%s)
    
    log_info_to_file "Repository: $REPO_ROOT"
    log_info_to_file "Python: $(python3 --version)"
    log_info_to_file "Log file: $log_file"
    log_info_to_file "Note: Infrastructure tests are skipped in this pipeline"
    echo
    
    # Log initial header to file (without colors)
    {
        echo "============================================================"
        echo "  COMPLETE RESEARCH PROJECT PIPELINE (SKIP INFRASTRUCTURE TESTS)"
        echo "============================================================"
        echo ""
        echo "Repository: $REPO_ROOT"
        echo "Python: $(python3 --version)"
        echo "Log file: $log_file"
        echo "Pipeline started: $(date)"
        echo "Note: Infrastructure tests are skipped in this pipeline"
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
    log_stage 1 "Setup Environment" 8 "$pipeline_start"
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
    
    # Stage 2: Infrastructure Tests - SKIPPED
    log_info_to_file "Skipping Infrastructure Tests (Stage 2)"
    log_info "Skipping Infrastructure Tests - use option 8 for full validation"
    
    # Stage 3: Project Tests (becomes Stage 2 in display)
    current_stage=3
    stage_start=$(date +%s)
    log_stage 2 "Project Tests" 8 "$pipeline_start"
    {
        echo ""
        echo "[2/8] Project Tests (25% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_pytest_project 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error_to_file "Pipeline failed at Stage 2 (Project Tests)"
        log_info_to_file "  Troubleshooting:"
        log_info_to_file "    - Run tests manually: python3 -m pytest project/tests/ -v"
        log_info_to_file "    - Check specific test: python3 -m pytest project/tests/test_example.py -v"
        log_info_to_file "    - View coverage: python3 -m pytest project/tests/ --cov=project/src --cov-report=term"
        return 1
    fi
    log_success_to_file "Project tests passed"
    stage_end=$(date +%s)
    STAGE_RESULTS[1]=0
    STAGE_DURATIONS[1]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 4: Analysis (becomes Stage 3 in display)
    current_stage=4
    stage_start=$(date +%s)
    log_stage 3 "Project Analysis" 8 "$pipeline_start"
    {
        echo ""
        echo "[3/8] Project Analysis (38% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_analysis 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 3 (Project Analysis)"
        log_info "  Troubleshooting:"
        log_info "    - Check analysis scripts: ls project/scripts/*.py"
        log_info "    - Run script manually: python3 project/scripts/analysis_pipeline.py"
        log_info "    - Verify outputs: ls project/output/figures/ project/output/data/"
        log_info "    - Check logs for specific script errors above"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[2]=0
    STAGE_DURATIONS[2]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 5: PDF Rendering (becomes Stage 4 in display)
    current_stage=5
    stage_start=$(date +%s)
    log_stage 4 "PDF Rendering" 8 "$pipeline_start"
    {
        echo ""
        echo "[4/8] PDF Rendering (50% complete)"
    } >> "$log_file" 2>/dev/null || true
    cd "$REPO_ROOT"
    python3 scripts/03_render_pdf.py 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 4 (PDF Rendering)"
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
    STAGE_RESULTS[3]=0
    STAGE_DURATIONS[3]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 6: Validation (becomes Stage 5 in display)
    current_stage=6
    stage_start=$(date +%s)
    log_stage 5 "Output Validation" 8 "$pipeline_start"
    {
        echo ""
        echo "[5/8] Output Validation (63% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_validation 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 5 (Output Validation)"
        log_info "  Troubleshooting:"
        log_info "    - Validate PDFs: python3 -m infrastructure.validation.cli pdf project/output/pdf/"
        log_info "    - Validate markdown: python3 -m infrastructure.validation.cli markdown project/manuscript/"
        log_info "    - Check validation report: cat project/output/validation_report.md"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[4]=0
    STAGE_DURATIONS[4]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 7: Copy Outputs (becomes Stage 6 in display)
    current_stage=7
    stage_start=$(date +%s)
    log_stage 6 "Copy Outputs" 8 "$pipeline_start"
    {
        echo ""
        echo "[6/8] Copy Outputs (75% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_copy_outputs 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 6 (Copy Outputs)"
        log_info "  Troubleshooting:"
        log_info "    - Check source directory: ls project/output/"
        log_info "    - Check destination: ls output/"
        log_info "    - Verify permissions: ls -la project/output/"
        log_info "    - Run manually: python3 scripts/05_copy_outputs.py"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[5]=0
    STAGE_DURATIONS[5]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 8: LLM Scientific Review (optional - graceful degradation) (becomes Stage 7 in display)
    current_stage=8
    stage_start=$(date +%s)
    log_stage 7 "LLM Scientific Review" 8 "$pipeline_start"
    {
        echo ""
        echo "[7/8] LLM Scientific Review (88% complete)"
    } >> "$log_file" 2>/dev/null || true
    cd "$REPO_ROOT"
    log_info "Running LLM scientific review (requires Ollama)..."
    log_info "Note: This stage is optional - pipeline will continue even if it fails"
    python3 scripts/06_llm_review.py --reviews-only 2>&1 | tee -a "$log_file" || true
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM scientific review complete"
        STAGE_RESULTS[6]=0
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "LLM scientific review skipped (Ollama not available)"
        log_info "  To enable: start Ollama with 'ollama serve' and install a model"
        log_info "  Recommended: ollama pull llama3-gradient"
        STAGE_RESULTS[6]=2  # Mark as skipped
    else
        log_warning "LLM scientific review failed (exit code: $exit_code)"
        log_info "  This is an optional stage - pipeline will continue"
        log_info "  Check Ollama status: ollama ps"
        log_info "  Check logs: project/output/llm/"
        STAGE_RESULTS[6]=1  # Mark as failed but don't stop pipeline
    fi
    stage_end=$(date +%s)
    STAGE_DURATIONS[6]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Stage 9: LLM Translations (optional - graceful degradation) (becomes Stage 8 in display)
    current_stage=9
    stage_start=$(date +%s)
    log_stage 8 "LLM Translations" 8 "$pipeline_start"
    {
        echo ""
        echo "[8/8] LLM Translations (100% complete)"
    } >> "$log_file" 2>/dev/null || true
    cd "$REPO_ROOT"
    log_info "Running LLM translations (requires Ollama)..."
    log_info "Note: This stage is optional - pipeline will continue even if it fails"
    python3 scripts/06_llm_review.py --translations-only 2>&1 | tee -a "$log_file" || true
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM translations complete"
        STAGE_RESULTS[7]=0
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "LLM translations skipped (Ollama not available or no languages configured)"
        log_info "  To enable: configure translations in project/manuscript/config.yaml"
        log_info "  Example: llm.translations.enabled: true, languages: [zh, hi, ru]"
        STAGE_RESULTS[7]=2  # Mark as skipped
    else
        log_warning "LLM translations failed (exit code: $exit_code)"
        log_info "  This is an optional stage - pipeline will continue"
        log_info "  Check Ollama status: ollama ps"
        log_info "  Check configuration: project/manuscript/config.yaml"
        STAGE_RESULTS[7]=1  # Mark as failed but don't stop pipeline
    fi
    stage_end=$(date +%s)
    STAGE_DURATIONS[7]=$(get_elapsed_time "$stage_start" "$stage_end")
    
    # Success - print summary
    local pipeline_end=$(date +%s)
    local total_duration=$(get_elapsed_time "$pipeline_start" "$pipeline_end")
    
    print_pipeline_summary "$total_duration" "$log_file" "true"
    
    # Log completion to file
    {
        echo ""
        echo "============================================================"
        echo "Pipeline completed: $(date)"
        echo "Total duration: $(format_duration "$total_duration")"
        echo "Log file: $log_file"
        echo "  (Will be copied to output/logs/ during copy stage)"
        echo "Note: Infrastructure tests were skipped in this pipeline"
        echo "============================================================"
    } >> "$log_file"
    
    # Clear trap
    trap - INT TERM
    
    return 0
}

# ============================================================================
# File Collection and Inventory Functions
# ============================================================================

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

collect_generated_files() {
    # Collect all generated files from output directories with metadata.
    # Args:
    #   $1: Base directory to scan (project/output or output)
    # Returns: Array of file entries (path|size|category)
    local base_dir="$1"
    local files=()
    
    if [[ ! -d "$base_dir" ]]; then
        return 1
    fi
    
    # Categories to scan
    local categories=("pdf" "figures" "data" "reports" "simulations" "llm" "logs" "web" "slides" "tex")
    
    for category in "${categories[@]}"; do
        local category_dir="$base_dir/$category"
        if [[ -d "$category_dir" ]]; then
            # Find all files recursively
            while IFS= read -r -d '' file; do
                if [[ -f "$file" ]]; then
                    # Try macOS stat first, then Linux stat, then fallback
                    local file_size
                    if file_size=$(stat -f%z "$file" 2>/dev/null); then
                        : # macOS stat worked
                    elif file_size=$(stat -c%s "$file" 2>/dev/null); then
                        : # Linux stat worked
                    else
                        file_size=0
                    fi
                    files+=("$file|$file_size|$category")
                fi
            done < <(find "$category_dir" -type f -print0 2>/dev/null)
        fi
    done
    
    # Also check for root-level files (like project_combined.pdf)
    if [[ -f "$base_dir/project_combined.pdf" ]]; then
        local file_size
        if file_size=$(stat -f%z "$base_dir/project_combined.pdf" 2>/dev/null); then
            : # macOS stat worked
        elif file_size=$(stat -c%s "$base_dir/project_combined.pdf" 2>/dev/null); then
            : # Linux stat worked
        else
            file_size=0
        fi
        files+=("$base_dir/project_combined.pdf|$file_size|pdf")
    fi
    
    # Output files as newline-separated entries
    printf '%s\n' "${files[@]}"
}

# ============================================================================
# Category Management Helpers (Bash 3.2+ Compatible)
# ============================================================================

get_category_index() {
    # Find the index of a category in the category_names array.
    # Args:
    #   $1: Category name
    #   $2: Reference to category_names array (by name)
    # Returns: Index (0-based) or -1 if not found
    local category="$1"
    local array_name="$2"
    local idx=0
    
    # Use indirect reference to access the array
    eval "local arr_size=\${#${array_name}[@]}"
    while [[ $idx -lt $arr_size ]]; do
        eval "local arr_item=\${${array_name}[$idx]}"
        if [[ "$arr_item" == "$category" ]]; then
            echo "$idx"
            return 0
        fi
        idx=$((idx + 1))
    done
    
    echo "-1"
    return 1
}

get_or_create_category_index() {
    # Get or create an index for a category.
    # Args:
    #   $1: Category name
    #   $2: Reference to category_names array (by name)
    #   $3: Reference to category_count variable (by name)
    # Returns: Index (0-based) of the category
    local category="$1"
    local array_name="$2"
    local count_var="$3"
    
    # Try to find existing index
    local idx=$(get_category_index "$category" "$array_name")
    
    if [[ $idx -ge 0 ]]; then
        echo "$idx"
        return 0
    fi
    
    # Create new category
    eval "local current_count=\${${count_var}:-0}"
    eval "${array_name}[$current_count]=\"$category\""
    eval "${count_var}=$((current_count + 1))"
    echo "$current_count"
    return 0
}

generate_file_inventory() {
    # Generate comprehensive file inventory for display and logging.
    # Bash 3.2+ compatible implementation using regular arrays instead of associative arrays.
    # Args:
    #   $1: Base directory to scan (project/output or output)
    #   $2: Log file path (optional)
    local base_dir="$1"
    local log_file="${2:-}"
    
    if [[ ! -d "$base_dir" ]]; then
        log_warning "Output directory not found: $base_dir"
        return 1
    fi
    
    # Collect files
    local file_list
    if ! file_list=$(collect_generated_files "$base_dir" 2>/dev/null); then
        log_warning "Failed to collect files from $base_dir"
        return 1
    fi
    
    if [[ -z "$file_list" ]]; then
        log_warning "No files found in $base_dir"
        return 1
    fi
    
    # Organize by category using regular arrays (bash 3.2+ compatible)
    # Use parallel arrays: category_names, category_file_lists, category_sizes, category_counts
    local category_names=()
    local category_file_lists=()
    local category_sizes=()
    local category_counts=()
    local category_count=0
    
    # Process file list and organize by category
    while IFS='|' read -r file_path file_size category; do
        if [[ -z "$file_path" ]] || [[ -z "$category" ]]; then
            continue
        fi
        
        # Find or create category index
        local cat_idx=-1
        local i=0
        while [[ $i -lt $category_count ]]; do
            if [[ "${category_names[$i]}" == "$category" ]]; then
                cat_idx=$i
                break
            fi
            i=$((i + 1))
        done
        
        # Create new category if not found
        if [[ $cat_idx -lt 0 ]]; then
            cat_idx=$category_count
            category_names[$cat_idx]="$category"
            category_file_lists[$cat_idx]=""
            category_sizes[$cat_idx]=0
            category_counts[$cat_idx]=0
            category_count=$((category_count + 1))
        fi
        
        # Add file to category
        category_file_lists[$cat_idx]="${category_file_lists[$cat_idx]}$file_path|$file_size"$'\n'
        category_counts[$cat_idx]=$((${category_counts[$cat_idx]} + 1))
        category_sizes[$cat_idx]=$((${category_sizes[$cat_idx]} + file_size))
    done <<< "$file_list"
    
    # Display inventory
    echo
    echo "Generated Files Inventory:"
    
    # Category display order
    local display_order=("pdf" "figures" "data" "reports" "simulations" "llm" "logs" "web" "slides" "tex")
    
    for category in "${display_order[@]}"; do
        # Find category index
        local cat_idx=-1
        local i=0
        while [[ $i -lt $category_count ]]; do
            if [[ "${category_names[$i]}" == "$category" ]]; then
                cat_idx=$i
                break
            fi
            i=$((i + 1))
        done
        
        if [[ $cat_idx -ge 0 ]] && [[ ${category_counts[$cat_idx]} -gt 0 ]]; then
            local count="${category_counts[$cat_idx]}"
            local total_size="${category_sizes[$cat_idx]}"
            local size_formatted=$(format_file_size "$total_size")
            local category_name=$(echo "${category:0:1}" | tr '[:lower:]' '[:upper:]')${category:1}
            
            echo "  $category_name ($count file(s), $size_formatted):"
            
            # Show files (limit to first 10 for readability, show count if more)
            local file_count=0
            local shown_count=0
            while IFS='|' read -r file_path file_size; do
                if [[ -n "$file_path" ]]; then
                    file_count=$((file_count + 1))
                    if [[ $file_count -le 10 ]]; then
                        local file_size_formatted=$(format_file_size "$file_size")
                        local relative_path="${file_path#$base_dir/}"
                        echo "    - $file_path ($file_size_formatted)"
                        shown_count=$((shown_count + 1))
                    fi
                fi
            done <<< "${category_file_lists[$cat_idx]}"
            
            if [[ $file_count -gt 10 ]]; then
                local remaining=$((file_count - 10))
                echo "    ... and $remaining more file(s)"
            fi
        fi
    done
    
    # Log to file if provided
    if [[ -n "$log_file" ]]; then
        {
            echo ""
            echo "Generated Files Inventory:"
            for category in "${display_order[@]}"; do
                # Find category index
                local cat_idx=-1
                local i=0
                while [[ $i -lt $category_count ]]; do
                    if [[ "${category_names[$i]}" == "$category" ]]; then
                        cat_idx=$i
                        break
                    fi
                    i=$((i + 1))
                done
                
                if [[ $cat_idx -ge 0 ]] && [[ ${category_counts[$cat_idx]} -gt 0 ]]; then
                    local count="${category_counts[$cat_idx]}"
                    local total_size="${category_sizes[$cat_idx]}"
                    local size_formatted=$(format_file_size "$total_size")
                    local category_name=$(echo "${category:0:1}" | tr '[:lower:]' '[:upper:]')${category:1}
                    echo "  $category_name ($count file(s), $size_formatted):"
                    
                    while IFS='|' read -r file_path file_size; do
                        if [[ -n "$file_path" ]]; then
                            local file_size_formatted=$(format_file_size "$file_size")
                            echo "    - $file_path ($file_size_formatted)"
                        fi
                    done <<< "${category_file_lists[$cat_idx]}"
                fi
            done
        } >> "$log_file" 2>/dev/null || true
    fi
    
    echo
}

print_pipeline_summary() {
    local total_duration="$1"
    local log_file="${2:-}"
    local skip_infra="${3:-false}"
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
    local executed_stage_count=0
    
    # Build mapping of stage names to durations, handling skipped stages
    declare -a stage_duration_map=()
    local duration_idx=0
    
    for ((i=0; i<num_stages; i++)); do
        local stage_name="${STAGE_NAMES[$i]}"
        local duration=0
        local is_skipped=false
        
        # Check if this stage was skipped (Infrastructure Tests when skip_infra=true)
        if [[ "$skip_infra" == "true" ]] && [[ "$stage_name" == "Infrastructure Tests" ]]; then
            is_skipped=true
            stage_duration_map[$i]="SKIPPED"
        elif [[ -n "${STAGE_DURATIONS[$duration_idx]:-}" ]]; then
            duration="${STAGE_DURATIONS[$duration_idx]}"
            stage_duration_map[$i]="$duration"
            duration_idx=$((duration_idx + 1))
            executed_stage_count=$((executed_stage_count + 1))
        else
            # Stage duration not found - mark as skipped
            is_skipped=true
            stage_duration_map[$i]="SKIPPED"
        fi
        
        if [[ "$is_skipped" == "true" ]]; then
            echo -e "  ${YELLOW}⊘${NC} Stage $((i+1)): ${stage_name} ${YELLOW}(skipped)${NC}"
        else
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
        fi
    done
    
    echo
    echo "Performance Metrics:"
    echo "  Total Execution Time: $(format_duration "$total_duration")"
    
    if [[ $executed_stage_count -gt 0 ]]; then
        local avg_time=$((total_stage_time / executed_stage_count))
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
    # Generate file inventory for both project/output and output directories
    local project_output_dir="$REPO_ROOT/project/output"
    local output_dir="$REPO_ROOT/output"
    
    # Check which directory has files (prefer output/ if it exists and has files, otherwise project/output/)
    if [[ -d "$output_dir" ]] && [[ -n "$(collect_generated_files "$output_dir" 2>/dev/null)" ]]; then
        generate_file_inventory "$output_dir" "$log_file"
        log_info "Note: Files are also available in project/output/ during development"
    elif [[ -d "$project_output_dir" ]]; then
        generate_file_inventory "$project_output_dir" "$log_file"
        log_info "Note: Files will be copied to output/ during copy stage"
    fi
    
    # Always show log file location
    if [[ -n "$log_file" ]]; then
        local log_file_final="${log_file/project\/output/output}"
        echo "Pipeline Log:"
        echo "  • Current: $log_file"
        if [[ "$log_file" != "$log_file_final" ]]; then
            echo "  • Final: $log_file_final (after copy stage)"
        fi
        echo
    fi
    
    # Show coverage reports if they exist
    if [[ -d "$REPO_ROOT/htmlcov" ]]; then
        echo "Coverage Reports:"
        echo "  • HTML: $REPO_ROOT/htmlcov/index.html"
        echo
    fi
    
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
            run_llm_scientific_review
            exit_code=$?
            ;;
        7)
            run_llm_translations
            exit_code=$?
            ;;
        8)
            run_full_pipeline
            exit_code=$?
            ;;
        9)
            run_full_pipeline_no_infra
            exit_code=$?
            ;;
        *)
            log_error "Invalid option: $choice"
            log_info "Please enter a number between 0 and 9"
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
    echo "Manuscript Pipeline Orchestrator"
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
    echo "Main Menu Options (0-9):"
    echo
    echo "Core Pipeline Scripts (aligned with script numbering):"
    echo "  0  Setup Environment (00_setup_environment.py)"
    echo "  1  Run Tests (01_run_tests.py - infrastructure + project)"
    echo "  2  Run Analysis (02_run_analysis.py)"
    echo "  3  Render PDF (03_render_pdf.py)"
    echo "  4  Validate Output (04_validate_output.py)"
    echo "  5  Copy Outputs (05_copy_outputs.py)"
    echo "  6  LLM Review (requires Ollama) (06_llm_review.py --reviews-only)"
    echo "  7  LLM Translations (requires Ollama) (06_llm_review.py --translations-only)"
    echo
    echo "Orchestration:"
    echo "  8  Run Full Pipeline (10 stages: 0-9)"
    echo "  9  Run Full Pipeline (skip infrastructure tests)"
    echo
    echo "Examples:"
    echo "  $0                      # Interactive menu mode"
    echo "  $0 --pipeline           # Run full pipeline"
    echo "  $0 --infra-tests         # Run infrastructure tests"
    echo "  $0 --project-tests       # Run project tests"
    echo "  $0 --render-pdf          # Render PDF manuscript"
    echo "  $0 --reviews             # Run LLM manuscript review"
    echo "  $0 --translations        # Run LLM translations"
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
        
        echo -n "Select option [0-9]: "
        read -r choice

        local exit_code=0
        if parse_choice_sequence "$choice" && [[ ${#SHORTHAND_CHOICES[@]} -gt 1 ]]; then
            run_option_sequence "${SHORTHAND_CHOICES[@]}"
            exit_code=$?
        else
            handle_menu_choice "$choice"
            exit_code=$?
        fi

        if [[ $exit_code -ne 0 ]]; then
            log_error "Last operation exited with code $exit_code"
        fi

        press_enter_to_continue
    done
}

# Run main
main "$@"
