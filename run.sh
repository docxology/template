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
#   5. LLM Review (requires Ollama) (06_llm_review.py --reviews-only)
#   6. LLM Translations (requires Ollama) (06_llm_review.py --translations-only)
#
# Orchestration:
#   7. Run Core Pipeline (stages 0-7: no LLM)
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

# Log uv availability status
log_uv_status

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
    "LLM Scientific Review"   # Stage 7 (optional)
    "LLM Translations"        # Stage 8 (optional)
    "Copy Outputs"            # Stage 9
)

declare -a STAGE_RESULTS=()
declare -a STAGE_DURATIONS=()

# Project management
declare -a PROJECT_LIST=()
CURRENT_PROJECT="project"  # Default project
SELECTED_PROJECT=""

# ============================================================================
# Project Discovery and Selection
# ============================================================================

discover_projects() {
    # Discover available projects in projects/ directory
    # Sets PROJECT_LIST array with project names
    PROJECT_LIST=()
    local idx=0

    if [[ ! -d "$REPO_ROOT/projects" ]]; then
        log_error "Projects directory not found: $REPO_ROOT/projects"
        return 1
    fi

    # Find all directories in projects/ (skip hidden ones)
    while IFS= read -r -d '' project_dir; do
        local project_name=$(basename "$project_dir")

        # Validate project structure (has src/ and tests/)
        if [[ -d "$project_dir/src" && -d "$project_dir/tests" ]]; then
            PROJECT_LIST[$idx]="$project_name"
            ((idx++))
        else
            log_warning "Skipping invalid project: $project_name (missing src/ or tests/)"
        fi
    done < <(find "$REPO_ROOT/projects" -mindepth 1 -maxdepth 1 -type d -not -name ".*" -print0 | sort -z)

    if [[ ${#PROJECT_LIST[@]} -eq 0 ]]; then
        log_error "No valid projects found in $REPO_ROOT/projects/"
        log_info "Projects must have src/ and tests/ directories"
        return 1
    fi

    return 0
}

display_project_selection() {
    echo -e "${BOLD}${CYAN}Available Projects:${NC}"
    echo

    local idx=0
    for project_name in "${PROJECT_LIST[@]}"; do
        local marker=" "
        if [[ "$project_name" == "$CURRENT_PROJECT" ]]; then
            marker="→"
        fi
        echo -e "  ${marker} ${idx}. ${BOLD}${project_name}${NC}"

        # Show brief description if available
        local desc=""
        if [[ -f "$REPO_ROOT/projects/$project_name/README.md" ]]; then
            desc=$(head -3 "$REPO_ROOT/projects/$project_name/README.md" | grep -v "^#" | head -1 | xargs)
        elif [[ -f "$REPO_ROOT/projects/$project_name/pyproject.toml" ]]; then
            desc=$(grep "^description" "$REPO_ROOT/projects/$project_name/pyproject.toml" 2>/dev/null | cut -d'"' -f2)
        fi

        if [[ -n "$desc" && ${#desc} -lt 60 ]]; then
            echo -e "      ${GRAY}${desc}${NC}"
        fi
        echo

        ((idx++))
    done

    echo -e "${BLUE}────────────────────────────────────────────────────────${NC}"
    echo -e "  ${BOLD}a${NC}. Run all projects sequentially"
    echo -e "  ${BOLD}q${NC}. Quit"
    echo -e "${BLUE}────────────────────────────────────────────────────────${NC}"
    echo
}

select_project() {
    while true; do
        display_project_selection

        echo -n "Select project [0-$((${#PROJECT_LIST[@]}-1))], 'a' for all, 'q' to quit: "
        read -r choice

        case "$choice" in
            [0-9]*)
                if [[ $choice -ge 0 && $choice -lt ${#PROJECT_LIST[@]} ]]; then
                    SELECTED_PROJECT="${PROJECT_LIST[$choice]}"
                    log_success "Selected project: $SELECTED_PROJECT"
                    break
                else
                    log_error "Invalid selection: $choice"
                fi
                ;;
            a|A)
                SELECTED_PROJECT="all"
                log_success "Selected: Run all projects"
                break
                ;;
            q|Q)
                log_info "Goodbye!"
                exit 0
                ;;
            *)
                log_error "Invalid choice: $choice"
                ;;
        esac
        echo
        press_enter_to_continue
    done
}

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
    echo -e "${BOLD}Project:${NC} $CURRENT_PROJECT"
    echo -e "${BOLD}Available Operations:${NC}"
    echo
    echo -e "${BOLD}Core Pipeline Scripts (aligned with script numbering):${NC}"
    echo "  0. Setup Environment (00_setup_environment.py)"
    echo "  1. Run Tests (01_run_tests.py - infrastructure + project)"
    echo "  2. Run Analysis (02_run_analysis.py)"
    echo "  3. Render PDF (03_render_pdf.py)"
    echo "  4. Validate Output (04_validate_output.py)"
    echo -e "  5. LLM Review ${YELLOW}(requires Ollama)${NC} (06_llm_review.py --reviews-only)"
    echo -e "  6. LLM Translations ${YELLOW}(requires Ollama)${NC} (06_llm_review.py --translations-only)"
    echo
    echo -e "${BOLD}Orchestration:${NC}"
    echo "  7. Run Core Pipeline (stages 0-7: no LLM)"
    echo "  8. Run Full Pipeline (10 stages: 0-9)"
    echo "  9. Run Full Pipeline (skip infrastructure tests)"
    echo
echo -e "${BOLD}Multi-Project Operations:${NC}"
echo "  a. Run all projects - Full pipeline (with infra, with LLM) + Executive Report"
echo "  b. Run all projects - Full pipeline (no infra, with LLM) + Executive Report"
echo "  c. Run all projects - Core pipeline (with infra, no LLM) + Executive Report"
echo "  d. Run all projects - Core pipeline (no infra, no LLM) + Executive Report"
    echo
    echo -e "${BOLD}Project Management:${NC}"
    echo "  p. Change Project"
    echo "  i. Show Project Info"
    echo
    echo -e "${BLUE}============================================================${NC}"
    echo -e "  Repository: ${CYAN}$REPO_ROOT${NC}"
    echo -e "  Python: ${CYAN}$($(get_python_cmd) --version 2>&1)${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo
    echo -e "${CYAN}Tip:${NC} Enter multiple digits to chain steps (e.g., 345 for analysis → render → validate). Comma forms like 3,4,5 work too."
}

# ============================================================================
# Clean Output Directories
# ============================================================================

clean_output_directories() {
    # Clean and recreate output directories for fresh pipeline run.
    # Uses the Python infrastructure function that handles multi-project structure correctly.
    # Removes all files from projects/{project_name}/output/ and output/{project_name}/ directories,
    # then recreates the standard directory structure.
    # This ensures no stale files from previous runs interfere with current execution.
    # Root-level directories in output/ are cleaned to maintain proper organization.
    echo
    echo -e "${YELLOW}[0/9] Clean Output Directories${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Use Python function that handles multi-project structure correctly
    $(get_python_cmd) -c "
from infrastructure.core.file_operations import clean_output_directories
from pathlib import Path
import sys

# Change to repo root
repo_root = Path('$REPO_ROOT')
sys.path.insert(0, str(repo_root))

# Clean directories for current project
clean_output_directories(repo_root, '$CURRENT_PROJECT')
"

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
    
    $(get_pytest_cmd) tests/infrastructure/ \
        --ignore=tests/integration/test_module_interoperability.py \
        -m "not requires_ollama" \
        --cov=infrastructure \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=60 \
        -v --tb=short
}

run_pytest_project() {
    local project_name="${1:-$CURRENT_PROJECT}"

    # Execute project tests with coverage requirements.
    # Runs pytest on projects/{project_name}/tests/ with 90% coverage threshold.
    # Skips integration tests by default.
    # Returns: 0 on success, 1 on failure
    cd "$REPO_ROOT"

    log_info "Running project tests for '$project_name'..."

    $(get_pytest_cmd) "projects/$project_name/tests/" \
        --ignore="projects/$project_name/tests/integration" \
        --cov="projects/$project_name/src" \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=90 \
        -v --tb=short
}

# ============================================================================
# Individual Stage Functions
# ============================================================================

run_setup_environment() {
    local project_name="${1:-$CURRENT_PROJECT}"

    # Standalone environment setup (menu option 0)
    log_header "SETUP ENVIRONMENT (00_setup_environment.py) - Project: $project_name"

    cd "$REPO_ROOT"
    if $(get_python_cmd) scripts/00_setup_environment.py --project "$project_name"; then
        log_success "Environment setup complete"
        return 0
    else
        log_error "Environment setup failed"
        return 1
    fi
}

run_all_tests() {
    local project_name="${1:-$CURRENT_PROJECT}"

    # Run both infrastructure and project tests via 01_run_tests.py
    log_header "RUN TESTS (01_run_tests.py) - Project: $project_name"

    cd "$REPO_ROOT"
    if $(get_python_cmd) scripts/01_run_tests.py --project "$project_name"; then
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
    local project_name="${1:-$CURRENT_PROJECT}"

    log_header "PROJECT TESTS - Project: $project_name"

    if run_pytest_project "$project_name"; then
        log_success "Project tests passed"
        return 0
    else
        log_error "Project tests failed"
        return 1
    fi
}

run_analysis() {
    local project_name="${1:-$CURRENT_PROJECT}"

    # Execute project analysis scripts from projects/{project_name}/scripts/.
    # Discovers and runs all Python scripts in projects/{project_name}/scripts/ directory.
    # Returns: 0 on success, 1 on failure
    log_stage 4 "Project Analysis" 9

    cd "$REPO_ROOT"

    if $(get_python_cmd) scripts/02_run_analysis.py --project "$project_name"; then
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
    
    if $(get_python_cmd) scripts/02_run_analysis.py; then
        log_success "Analysis complete"
        return 0
    else
        log_error "Analysis failed"
        return 1
    fi
}

run_pdf_rendering() {
    local project_name="${1:-$CURRENT_PROJECT}"

    log_header "PDF RENDERING (03_render_pdf.py) - Project: $project_name"

    cd "$REPO_ROOT"

    log_info "Running analysis scripts..."
    if ! $(get_python_cmd) scripts/02_run_analysis.py --project "$project_name"; then
        log_error "Analysis failed"
        return 1
    fi

    log_info "Rendering PDF manuscript..."
    if $(get_python_cmd) scripts/03_render_pdf.py --project "$project_name"; then
        log_success "PDF rendering complete"
        return 0
    else
        log_error "PDF rendering failed"
        return 1
    fi
}

run_validation() {
    local project_name="${1:-$CURRENT_PROJECT}"

    log_stage 6 "Output Validation" 9

    cd "$REPO_ROOT"

    if $(get_python_cmd) scripts/04_validate_output.py --project "$project_name"; then
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
    
    if $(get_python_cmd) scripts/04_validate_output.py; then
        log_success "Validation complete"
        return 0
    else
        log_error "Validation failed"
        return 1
    fi
}

run_copy_outputs() {
    local project_name="${1:-$CURRENT_PROJECT}"

    log_stage 7 "Copy Outputs" 9

    cd "$REPO_ROOT"

    if $(get_python_cmd) scripts/05_copy_outputs.py --project "$project_name"; then
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
    
    if $(get_python_cmd) scripts/05_copy_outputs.py; then
        log_success "Output copying complete"
        return 0
    else
        log_error "Output copying failed"
        return 1
    fi
}

run_llm_scientific_review() {
    local project_name="${1:-$CURRENT_PROJECT}"

    log_header "LLM SCIENTIFIC REVIEW (ENGLISH) - Project: $project_name"

    cd "$REPO_ROOT"

    log_info "Running LLM scientific review (requires Ollama)..."
    log_info "Generating: executive summary, quality review, methodology review, improvements"

    local exit_code
    $(get_python_cmd) scripts/06_llm_review.py --reviews-only --project "$project_name"
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
    local project_name="${1:-$CURRENT_PROJECT}"

    log_header "LLM TRANSLATIONS - Project: $project_name"

    cd "$REPO_ROOT"

    log_info "Running LLM translations (requires Ollama)..."
    log_info "Generating translations for configured languages (see config.yaml)"

    local exit_code
    $(get_python_cmd) scripts/06_llm_review.py --translations-only --project "$project_name"
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
    $(get_python_cmd) scripts/06_llm_review.py
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

generate_pipeline_reports() {
    local project_name="${1:-$CURRENT_PROJECT}"
    local total_duration="${2:-0}"

    log_info "Generating pipeline reports..."

    # Run the dedicated Python script
    if $(get_python_cmd) "$REPO_ROOT/scripts/generate_pipeline_reports.py" --project "$project_name" --total-duration "$total_duration"; then
        log_success "Pipeline reports generated successfully"
        return 0
    else
        log_warning "Failed to generate pipeline reports"
        return 1
    fi
}

run_full_pipeline() {
    local resume_flag="${1:-}"
    local project_name="${2:-$CURRENT_PROJECT}"

    # Initialize log file capture
    # Write to projects/{project_name}/output/logs during execution, will be copied to output/{project_name}/logs in copy stage
    local log_dir="$REPO_ROOT/projects/$project_name/output/logs"
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
            if $(get_python_cmd) -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); cm.save_checkpoint(pipeline_start_time=$pipeline_start, last_stage_completed=$current_stage, stage_results=[], total_stages=9)" 2>/dev/null; then
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
    log_info_to_file "Python: $($(get_python_cmd) --version)"
    log_info_to_file "Log file: $log_file"
    echo
    
    # Log initial header to file (without colors)
    {
        echo "============================================================"
        echo "  COMPLETE RESEARCH PROJECT PIPELINE"
        echo "============================================================"
        echo ""
        echo "Repository: $REPO_ROOT"
        echo "Python: $($(get_python_cmd) --version)"
        echo "Log file: $log_file"
        echo "Pipeline started: $(date)"
        echo ""
    } >> "$log_file"
    
    # Check for checkpoint if resuming
    if [[ "$resume_flag" == "--resume" ]]; then
        log_info_to_file "Checking for checkpoint..."
        if $(get_python_cmd) -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); valid, msg = cm.validate_checkpoint(); exit(0 if valid else 1)" 2>/dev/null; then
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
        if $(get_python_cmd) scripts/run_all.py --resume; then
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
    log_stage_progress 1 "Setup Environment" 9 "$pipeline_start" "$stage_start"
    run_setup_environment "$project_name" 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_pipeline_error "Setup Environment" "Environment setup failed" "$exit_code" \
            "Check Python version: python3 --version (requires >=3.10)" \
            "Verify dependencies: pip list | grep -E '(numpy|matplotlib|pytest)'" \
            "Check script: python3 scripts/00_setup_environment.py"
        return 1
    fi
    local stage_end=$(date +%s)
    STAGE_RESULTS[0]=0
    STAGE_DURATIONS[0]=$(get_elapsed_time "$stage_start" "$stage_end")
    log_resource_usage "Setup Environment" "${STAGE_DURATIONS[0]}"

    # Stage 2: Infrastructure Tests
    current_stage=2
    stage_start=$(date +%s)
    log_stage_progress 2 "Infrastructure Tests" 9 "$pipeline_start" "$stage_start"
    {
        echo ""
        echo "[2/9] Infrastructure Tests (22% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_infrastructure_tests 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_pipeline_error "Infrastructure Tests" "Infrastructure tests failed" "$exit_code" \
            "Run tests manually: python3 -m pytest tests/infrastructure/ -v" \
            "Check coverage: python3 -m pytest tests/infrastructure/ --cov=infrastructure --cov-report=term" \
            "View HTML report: open htmlcov/index.html"
        return 1
    fi
    log_success_to_file "Infrastructure tests passed"
    stage_end=$(date +%s)
    STAGE_RESULTS[1]=0
    STAGE_DURATIONS[1]=$(get_elapsed_time "$stage_start" "$stage_end")
    log_resource_usage "Infrastructure Tests" "${STAGE_DURATIONS[1]}"

    # Stage 3: Project Tests
    current_stage=3
    stage_start=$(date +%s)
    log_stage_progress 3 "Project Tests" 9 "$pipeline_start" "$stage_start"
    {
        echo ""
        echo "[3/9] Project Tests (33% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_project_tests "$project_name" 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_pipeline_error "Project Tests" "Project tests failed" "$exit_code" \
            "Run tests manually: python3 -m pytest project/tests/ -v" \
            "Check specific test: python3 -m pytest project/tests/test_example.py -v" \
            "View coverage: python3 -m pytest project/tests/ --cov=project/src --cov-report=term"
        return 1
    fi
    log_success_to_file "Project tests passed"
    stage_end=$(date +%s)
    STAGE_RESULTS[2]=0
    STAGE_DURATIONS[2]=$(get_elapsed_time "$stage_start" "$stage_end")
    log_resource_usage "Project Tests" "${STAGE_DURATIONS[2]}"

    # Stage 4: Analysis
    current_stage=4
    stage_start=$(date +%s)
    run_analysis "$project_name" 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_pipeline_error "Project Analysis" "Analysis scripts failed" "$exit_code" \
            "Check analysis scripts: ls project/scripts/*.py" \
            "Run script manually: python3 project/scripts/analysis_pipeline.py" \
            "Verify outputs: ls projects/$CURRENT_PROJECT/output/figures/ projects/$CURRENT_PROJECT/output/data/" \
            "Check logs above for specific script errors"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[3]=0
    STAGE_DURATIONS[3]=$(get_elapsed_time "$stage_start" "$stage_end")
    log_resource_usage "Project Analysis" "${STAGE_DURATIONS[3]}"

    # Stage 5: PDF Rendering
    current_stage=5
    stage_start=$(date +%s)
    log_stage_progress 5 "PDF Rendering" 9 "$pipeline_start" "$stage_start"
    cd "$REPO_ROOT"
    $(get_python_cmd) scripts/03_render_pdf.py --project "$project_name" 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 5 (PDF Rendering)"
        log_info "  Troubleshooting:"
        log_info "    - Check LaTeX installation: which xelatex"
        log_info "    - Verify manuscript files: ls project/manuscript/*.md"
        log_info "    - Check figure paths: ls projects/$CURRENT_PROJECT/output/figures/"
        log_info "    - View compilation logs: ls projects/$CURRENT_PROJECT/output/pdf/*.log"
        log_info "    - Run manually: $(get_python_cmd) scripts/03_render_pdf.py"
        return 1
    fi
    log_success "PDF rendering complete"
    stage_end=$(date +%s)
    STAGE_RESULTS[4]=0
    STAGE_DURATIONS[4]=$(get_elapsed_time "$stage_start" "$stage_end")
    log_resource_usage "PDF Rendering" "${STAGE_DURATIONS[4]}"

    # Stage 6: Validation
    current_stage=6
    stage_start=$(date +%s)
    run_validation "$project_name" 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 6 (Output Validation)"
        log_info "  Troubleshooting:"
        log_info "    - Validate PDFs: python3 -m infrastructure.validation.cli pdf projects/$CURRENT_PROJECT/output/pdf/"
        log_info "    - Validate markdown: python3 -m infrastructure.validation.cli markdown project/manuscript/"
        log_info "    - Check validation report: cat projects/$CURRENT_PROJECT/output/validation_report.md"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[5]=0
    STAGE_DURATIONS[5]=$(get_elapsed_time "$stage_start" "$stage_end")
    log_resource_usage "Output Validation" "${STAGE_DURATIONS[5]}"

    # Stage 7: LLM Scientific Review (optional - graceful degradation)
    current_stage=7
    stage_start=$(date +%s)
    log_stage_progress 7 "LLM Scientific Review" 9 "$pipeline_start" "$stage_start"
    {
        echo ""
        echo "[7/9] LLM Scientific Review (78% complete)"
    } >> "$log_file" 2>/dev/null || true
    cd "$REPO_ROOT"
    log_info "Running LLM scientific review (requires Ollama)..."
    log_info "Note: This stage is optional - pipeline will continue even if it fails"
    local exit_code
    $(get_python_cmd) scripts/06_llm_review.py --reviews-only --project "$project_name" 2>&1 | tee -a "$log_file" || true
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
        log_info "  Check logs: projects/$CURRENT_PROJECT/output/llm/"
        STAGE_RESULTS[6]=1  # Mark as failed but don't stop pipeline
    fi
    stage_end=$(date +%s)
    STAGE_DURATIONS[6]=$(get_elapsed_time "$stage_start" "$stage_end")

    # Stage 8: LLM Translations (optional - graceful degradation)
    current_stage=8
    stage_start=$(date +%s)
    log_stage_progress 8 "LLM Translations" 9 "$pipeline_start" "$stage_start"
    {
        echo ""
        echo "[8/9] LLM Translations (89% complete)"
    } >> "$log_file" 2>/dev/null || true
    cd "$REPO_ROOT"

    # Get timeout configuration for logging
    LLM_TIMEOUT=${LLM_REVIEW_TIMEOUT:-300}
    log_info "Running LLM translations (requires Ollama)..."
    log_info "  Timeout: ${LLM_TIMEOUT}s per translation"
    log_info "  Expected duration: 1-5 minutes per language (depending on model)"
    log_info "Note: This stage is optional - pipeline will continue even if it fails"
    $(get_python_cmd) scripts/06_llm_review.py --translations-only --project "$project_name" 2>&1 | tee -a "$log_file" || true
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM translations complete"
        STAGE_RESULTS[7]=0
        stage_end=$(date +%s)
        STAGE_DURATIONS[7]=$(get_elapsed_time "$stage_start" "$stage_end")
        log_resource_usage "LLM Translations" "${STAGE_DURATIONS[7]}"
    elif [[ $exit_code -eq 2 ]]; then
        stage_end=$(date +%s)
        STAGE_DURATIONS[7]=$(get_elapsed_time "$stage_start" "$stage_end")
        log_warning "LLM translations skipped (Ollama not available or no languages configured)"
        log_info "  To enable: configure translations in project/manuscript/config.yaml"
        log_info "  Example: llm.translations.enabled: true, languages: [zh, hi, ru]"
        STAGE_RESULTS[7]=2  # Mark as skipped
    else
        # Calculate stage duration for better error reporting
        stage_end=$(date +%s)
        stage_duration=$(get_elapsed_time "$stage_start" "$stage_end")
        STAGE_DURATIONS[7]=$(get_elapsed_time "$stage_start" "$stage_end")

        log_warning "LLM translations failed (exit code: $exit_code, duration: ${stage_duration})"

        # Warn if stage took very long (>10 minutes)
        if [[ $stage_duration -gt 600 ]]; then
            log_warning "⚠️  Stage took unusually long (${stage_duration}s > 10 minutes)"
            log_info "  This may indicate model loading issues or slow hardware"
            log_info "  Consider using a smaller model or increasing timeout:"
            log_info "    export LLM_REVIEW_TIMEOUT=600  # 10 minutes"
        fi

        log_info "  This is an optional stage - pipeline will continue"
        log_info "  Troubleshooting:"
        log_info "    - Check Ollama status: ollama ps"
        log_info "    - Check configuration: project/manuscript/config.yaml"
        log_info "    - For timeout issues: export LLM_REVIEW_TIMEOUT=600"
        log_info "    - For slow models: consider gemma2:2b instead of larger models"
        STAGE_RESULTS[7]=1  # Mark as failed but don't stop pipeline
    fi

    # Stage 9: Copy Outputs
    current_stage=9
    stage_start=$(date +%s)
    log_stage_progress 9 "Copy Outputs" 9 "$pipeline_start" "$stage_start"
    {
        echo ""
        echo "[9/9] Copy Outputs (100% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_copy_outputs "$project_name" 2>&1 | tee -a "$log_file"
    local exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 9 (Copy Outputs)"
        log_info "  Troubleshooting:"
        log_info "    - Check source directory: ls projects/$CURRENT_PROJECT/output/"
        log_info "    - Check destination: ls output/"
        log_info "    - Verify permissions: ls -la projects/$CURRENT_PROJECT/output/"
        log_info "    - Run manually: python3 scripts/05_copy_outputs.py"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[8]=0
    STAGE_DURATIONS[8]=$(get_elapsed_time "$stage_start" "$stage_end")
    log_resource_usage "Copy Outputs" "${STAGE_DURATIONS[8]}"

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

    # Generate pipeline reports
    generate_pipeline_reports "$project_name" "$total_duration"

    # Clear trap
    trap - INT TERM

    return 0
}

run_full_pipeline_no_infra() {
    local resume_flag="${1:-}"
    
    # Initialize log file capture
    # Write to projects/$CURRENT_PROJECT/output/logs during execution, will be copied to output/logs in copy stage
    local log_dir="$REPO_ROOT/projects/$CURRENT_PROJECT/output/logs"
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
            if $(get_python_cmd) -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); cm.save_checkpoint(pipeline_start_time=$pipeline_start, last_stage_completed=$current_stage, stage_results=[], total_stages=8)" 2>/dev/null; then
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
    log_info_to_file "Python: $($(get_python_cmd) --version)"
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
        echo "Python: $($(get_python_cmd) --version)"
        echo "Log file: $log_file"
        echo "Pipeline started: $(date)"
        echo "Note: Infrastructure tests are skipped in this pipeline"
        echo ""
    } >> "$log_file"
    
    # Check for checkpoint if resuming
    if [[ "$resume_flag" == "--resume" ]]; then
        log_info_to_file "Checking for checkpoint..."
        if $(get_python_cmd) -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); valid, msg = cm.validate_checkpoint(); exit(0 if valid else 1)" 2>/dev/null; then
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
        if $(get_python_cmd) scripts/run_all.py --resume; then
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
    run_setup_environment "$project_name" 2>&1 | tee -a "$log_file"
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
    run_project_tests "$project_name" 2>&1 | tee -a "$log_file"
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
    run_analysis "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 3 (Project Analysis)"
        log_info "  Troubleshooting:"
        log_info "    - Check analysis scripts: ls project/scripts/*.py"
        log_info "    - Run script manually: python3 project/scripts/analysis_pipeline.py"
        log_info "    - Verify outputs: ls projects/$CURRENT_PROJECT/output/figures/ projects/$CURRENT_PROJECT/output/data/"
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
    $(get_python_cmd) scripts/03_render_pdf.py --project "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 4 (PDF Rendering)"
        log_info "  Troubleshooting:"
        log_info "    - Check LaTeX installation: which xelatex"
        log_info "    - Verify manuscript files: ls project/manuscript/*.md"
        log_info "    - Check figure paths: ls projects/$CURRENT_PROJECT/output/figures/"
        log_info "    - View compilation logs: ls projects/$CURRENT_PROJECT/output/pdf/*.log"
        log_info "    - Run manually: $(get_python_cmd) scripts/03_render_pdf.py"
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
    run_validation "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 5 (Output Validation)"
        log_info "  Troubleshooting:"
        log_info "    - Validate PDFs: python3 -m infrastructure.validation.cli pdf projects/$CURRENT_PROJECT/output/pdf/"
        log_info "    - Validate markdown: python3 -m infrastructure.validation.cli markdown project/manuscript/"
        log_info "    - Check validation report: cat projects/$CURRENT_PROJECT/output/validation_report.md"
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
    run_copy_outputs "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 6 (Copy Outputs)"
        log_info "  Troubleshooting:"
        log_info "    - Check source directory: ls projects/$CURRENT_PROJECT/output/"
        log_info "    - Check destination: ls output/"
        log_info "    - Verify permissions: ls -la projects/$CURRENT_PROJECT/output/"
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
    log_info "Auto-start: Ollama will be started automatically if not running"

    $(get_python_cmd) scripts/06_llm_review.py --reviews-only --project "$project_name" 2>&1 | tee -a "$log_file" || true
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM scientific review complete"
        STAGE_RESULTS[6]=0
        log_resource_usage "LLM Scientific Review" "${STAGE_DURATIONS[6]}"
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "LLM scientific review skipped (Ollama not available)"
        log_info "  Auto-start may have been attempted - check logs above"
        log_info "  To enable: start Ollama with 'ollama serve' and install a model"
        log_info "  Recommended: ollama pull llama3-gradient"
        STAGE_RESULTS[6]=2  # Mark as skipped
    else
        log_warning "LLM scientific review failed (exit code: $exit_code)"
        log_info "  This is an optional stage - pipeline will continue"
        log_info "  Check Ollama status: ollama ps"
        log_info "  Check logs: projects/$CURRENT_PROJECT/output/llm/"
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

    # Get timeout configuration for logging
    LLM_TIMEOUT=${LLM_REVIEW_TIMEOUT:-300}
    log_info "Running LLM translations (requires Ollama)..."
    log_info "  Timeout: ${LLM_TIMEOUT}s per translation"
    log_info "  Expected duration: 1-5 minutes per language (depending on model)"
    log_info "Note: This stage is optional - pipeline will continue even if it fails"
    log_info "Auto-start: Ollama will be started automatically if not running"

    $(get_python_cmd) scripts/06_llm_review.py --translations-only --project "$project_name" 2>&1 | tee -a "$log_file" || true
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM translations complete"
        STAGE_RESULTS[7]=0
    elif [[ $exit_code -eq 2 ]]; then
        log_warning "LLM translations skipped (Ollama not available or no languages configured)"
        log_info "  Auto-start may have been attempted - check logs above"
        log_info "  To enable: configure translations in project/manuscript/config.yaml"
        log_info "  Example: llm.translations.enabled: true, languages: [zh, hi, ru]"
        STAGE_RESULTS[7]=2  # Mark as skipped
    else
        # Calculate stage duration for better error reporting
        stage_end=$(date +%s)
        stage_duration=$(get_elapsed_time "$stage_start" "$stage_end")
        STAGE_DURATIONS[7]=$(get_elapsed_time "$stage_start" "$stage_end")

        log_warning "LLM translations failed (exit code: $exit_code, duration: ${stage_duration})"

        # Warn if stage took very long (>10 minutes)
        if [[ $stage_duration -gt 600 ]]; then
            log_warning "⚠️  Stage took unusually long (${stage_duration}s > 10 minutes)"
            log_info "  This may indicate model loading issues or slow hardware"
            log_info "  Consider using a smaller model or increasing timeout:"
            log_info "    export LLM_REVIEW_TIMEOUT=600  # 10 minutes"
        fi

        log_info "  This is an optional stage - pipeline will continue"
        log_info "  Troubleshooting:"
        log_info "    - Check Ollama status: ollama ps"
        log_info "    - Check configuration: project/manuscript/config.yaml"
        log_info "    - For timeout issues: export LLM_REVIEW_TIMEOUT=600"
        log_info "    - For slow models: consider gemma2:2b instead of larger models"
        STAGE_RESULTS[7]=1  # Mark as failed but don't stop pipeline
    fi
    
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

run_core_pipeline_no_llm() {
    local resume_flag="${1:-}"
    local project_name="${2:-$CURRENT_PROJECT}"

    # Initialize log file capture
    # Write to projects/{project_name}/output/logs during execution
    local log_dir="$REPO_ROOT/projects/$project_name/output/logs"
    mkdir -p "$log_dir"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local log_file="$log_dir/pipeline_core_${timestamp}.log"
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
            if $(get_python_cmd) -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); cm.save_checkpoint(pipeline_start_time=$pipeline_start, last_stage_completed=$current_stage, stage_results=[], total_stages=8)" 2>/dev/null; then
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

    log_header_to_file "CORE PIPELINE (STAGES 0-7: NO LLM)"

    pipeline_start=$(date +%s)

    log_info_to_file "Repository: $REPO_ROOT"
    log_info_to_file "Python: $($(get_python_cmd) --version)"
    log_info_to_file "Log file: $log_file"
    log_info_to_file "Core pipeline: stages 0-7 (no LLM)"
    echo

    # Log initial header to file (without colors)
    {
        echo "============================================================"
        echo "  CORE PIPELINE (STAGES 0-7: NO LLM)"
        echo "============================================================"
        echo ""
        echo "Repository: $REPO_ROOT"
        echo "Python: $($(get_python_cmd) --version)"
        echo "Log file: $log_file"
        echo "Pipeline started: $(date)"
        echo "Core pipeline: stages 0-7 (no LLM)"
        echo ""
    } >> "$log_file"

    # Check for checkpoint if resuming
    if [[ "$resume_flag" == "--resume" ]]; then
        log_info_to_file "Checking for checkpoint..."
        if $(get_python_cmd) -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); valid, msg = cm.validate_checkpoint(); exit(0 if valid else 1)" 2>/dev/null; then
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
        if $(get_python_cmd) scripts/run_all.py --resume --core-only; then
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
    log_stage 1 "Setup Environment" 7 "$pipeline_start"
    run_setup_environment "$project_name" 2>&1 | tee -a "$log_file"
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
    log_stage 2 "Infrastructure Tests" 7 "$pipeline_start"
    {
        echo ""
        echo "[2/7] Infrastructure Tests (29% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_infrastructure_tests 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
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
    log_stage 3 "Project Tests" 7 "$pipeline_start"
    {
        echo ""
        echo "[3/7] Project Tests (43% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_project_tests "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
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
    run_analysis "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 4 (Project Analysis)"
        log_info "  Troubleshooting:"
        log_info "    - Check analysis scripts: ls project/scripts/*.py"
        log_info "    - Run script manually: python3 project/scripts/analysis_pipeline.py"
        log_info "    - Verify outputs: ls projects/$CURRENT_PROJECT/output/figures/ projects/$CURRENT_PROJECT/output/data/"
        log_info "    - Check logs for specific script errors above"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[3]=0
    STAGE_DURATIONS[3]=$(get_elapsed_time "$stage_start" "$stage_end")

    # Stage 5: PDF Rendering
    current_stage=5
    stage_start=$(date +%s)
    log_stage 5 "PDF Rendering" 7 "$pipeline_start"
    cd "$REPO_ROOT"
    $(get_python_cmd) scripts/03_render_pdf.py --project "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_pipeline_error "PDF Rendering" "PDF generation failed" "$exit_code" \
            "Check LaTeX installation: which xelatex" \
            "Verify manuscript files: ls project/manuscript/*.md" \
            "Check figure paths: ls projects/$CURRENT_PROJECT/output/figures/" \
            "View compilation logs: ls projects/$CURRENT_PROJECT/output/pdf/*.log" \
            "Run manually: $(get_python_cmd) scripts/03_render_pdf.py"
        return 1
    fi
    log_success "PDF rendering complete"
    stage_end=$(date +%s)
    STAGE_RESULTS[4]=0
    STAGE_DURATIONS[4]=$(get_elapsed_time "$stage_start" "$stage_end")

    # Stage 6: Validation
    current_stage=6
    stage_start=$(date +%s)
    run_validation "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_pipeline_error "Output Validation" "Validation checks failed" "$exit_code" \
            "Validate PDFs: python3 -m infrastructure.validation.cli pdf projects/$CURRENT_PROJECT/output/pdf/" \
            "Validate markdown: python3 -m infrastructure.validation.cli markdown project/manuscript/" \
            "Check validation report: cat projects/$CURRENT_PROJECT/output/validation_report.md"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[5]=0
    STAGE_DURATIONS[5]=$(get_elapsed_time "$stage_start" "$stage_end")

    # Stage 7: Copy Outputs
    current_stage=7
    stage_start=$(date +%s)
    run_copy_outputs "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_pipeline_error "Copy Outputs" "Output copying failed" "$exit_code" \
            "Check source directory: ls projects/$CURRENT_PROJECT/output/" \
            "Check destination: ls output/" \
            "Verify permissions: ls -la projects/$CURRENT_PROJECT/output/" \
            "Run manually: python3 scripts/05_copy_outputs.py"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[6]=0
    STAGE_DURATIONS[6]=$(get_elapsed_time "$stage_start" "$stage_end")

    # Success - print summary
    local pipeline_end=$(date +%s)
    local total_duration=$(get_elapsed_time "$pipeline_start" "$pipeline_end")

    print_pipeline_summary "$total_duration" "$log_file" "false"

    # Log completion to file
    {
        echo ""
        echo "============================================================"
        echo "Core pipeline completed: $(date)"
        echo "Total duration: $(format_duration "$total_duration")"
        echo "Log file: $log_file"
        echo "============================================================"
    } >> "$log_file"

    # Clear trap
    trap - INT TERM

    return 0
}

run_core_pipeline_no_llm_no_infra() {
    local resume_flag="${1:-}"
    local project_name="${2:-$CURRENT_PROJECT}"

    # Initialize log file capture
    # Write to projects/{project_name}/output/logs during execution
    local log_dir="$REPO_ROOT/projects/$project_name/output/logs"
    mkdir -p "$log_dir"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local log_file="$log_dir/pipeline_core_no_infra_${timestamp}.log"
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
            if $(get_python_cmd) -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); cm.save_checkpoint(pipeline_start_time=$pipeline_start, last_stage_completed=$current_stage, stage_results=[], total_stages=7)" 2>/dev/null; then
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

    log_header_to_file "CORE PIPELINE (STAGES 0-7: NO LLM, NO INFRA TESTS)"

    pipeline_start=$(date +%s)

    log_info_to_file "Repository: $REPO_ROOT"
    log_info_to_file "Python: $($(get_python_cmd) --version)"
    log_info_to_file "Log file: $log_file"
    log_info_to_file "Core pipeline: stages 0-7 (no LLM, no infrastructure tests)"
    echo

    # Log initial header to file (without colors)
    {
        echo "============================================================"
        echo "  CORE PIPELINE (STAGES 0-7: NO LLM, NO INFRA TESTS)"
        echo "============================================================"
        echo ""
        echo "Repository: $REPO_ROOT"
        echo "Python: $($(get_python_cmd) --version)"
        echo "Log file: $log_file"
        echo "Pipeline started: $(date)"
        echo "Core pipeline: stages 0-7 (no LLM, no infrastructure tests)"
        echo ""
    } >> "$log_file"

    # Check for checkpoint if resuming
    if [[ "$resume_flag" == "--resume" ]]; then
        log_info_to_file "Checking for checkpoint..."
        if $(get_python_cmd) -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); valid, msg = cm.validate_checkpoint(); exit(0 if valid else 1)" 2>/dev/null; then
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
        if $(get_python_cmd) scripts/run_all.py --resume --core-only; then
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
    log_stage 1 "Setup Environment" 7 "$pipeline_start"
    run_setup_environment "$project_name" 2>&1 | tee -a "$log_file"
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
    log_info "Skipping Infrastructure Tests - use option 7 for full validation"

    # Stage 3: Project Tests (becomes Stage 2 in display)
    current_stage=3
    stage_start=$(date +%s)
    log_stage 2 "Project Tests" 7 "$pipeline_start"
    {
        echo ""
        echo "[2/7] Project Tests (29% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_project_tests "$project_name" 2>&1 | tee -a "$log_file"
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
    log_stage 3 "Project Analysis" 7 "$pipeline_start"
    {
        echo ""
        echo "[3/7] Project Analysis (43% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_analysis "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 3 (Project Analysis)"
        log_info "  Troubleshooting:"
        log_info "    - Check analysis scripts: ls project/scripts/*.py"
        log_info "    - Run script manually: python3 project/scripts/analysis_pipeline.py"
        log_info "    - Verify outputs: ls projects/$CURRENT_PROJECT/output/figures/ projects/$CURRENT_PROJECT/output/data/"
        log_info "    - Check logs for specific script errors above"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[2]=0
    STAGE_DURATIONS[2]=$(get_elapsed_time "$stage_start" "$stage_end")

    # Stage 5: PDF Rendering (becomes Stage 4 in display)
    current_stage=5
    stage_start=$(date +%s)
    log_stage 4 "PDF Rendering" 7 "$pipeline_start"
    {
        echo ""
        echo "[4/7] PDF Rendering (57% complete)"
    } >> "$log_file" 2>/dev/null || true
    cd "$REPO_ROOT"
    $(get_python_cmd) scripts/03_render_pdf.py --project "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 4 (PDF Rendering)"
        log_info "  Troubleshooting:"
        log_info "    - Check LaTeX installation: which xelatex"
        log_info "    - Verify manuscript files: ls project/manuscript/*.md"
        log_info "    - Check figure paths: ls projects/$CURRENT_PROJECT/output/figures/"
        log_info "    - View compilation logs: ls projects/$CURRENT_PROJECT/output/pdf/*.log"
        log_info "    - Run manually: $(get_python_cmd) scripts/03_render_pdf.py"
        return 1
    fi
    log_success "PDF rendering complete"
    stage_end=$(date +%s)
    STAGE_RESULTS[3]=0
    STAGE_DURATIONS[3]=$(get_elapsed_time "$stage_start" "$stage_end")

    # Stage 6: Validation (becomes Stage 5 in display)
    current_stage=6
    stage_start=$(date +%s)
    log_stage 5 "Output Validation" 7 "$pipeline_start"
    {
        echo ""
        echo "[5/7] Output Validation (71% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_validation "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 5 (Output Validation)"
        log_info "  Troubleshooting:"
        log_info "    - Validate PDFs: python3 -m infrastructure.validation.cli pdf projects/$CURRENT_PROJECT/output/pdf/"
        log_info "    - Validate markdown: python3 -m infrastructure.validation.cli markdown project/manuscript/"
        log_info "    - Check validation report: cat projects/$CURRENT_PROJECT/output/validation_report.md"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[4]=0
    STAGE_DURATIONS[4]=$(get_elapsed_time "$stage_start" "$stage_end")

    # Stage 7: Copy Outputs (becomes Stage 6 in display)
    current_stage=7
    stage_start=$(date +%s)
    log_stage 6 "Copy Outputs" 7 "$pipeline_start"
    {
        echo ""
        echo "[6/7] Copy Outputs (86% complete)"
    } >> "$log_file" 2>/dev/null || true
    run_copy_outputs "$project_name" 2>&1 | tee -a "$log_file"
    exit_code=${PIPESTATUS[0]}
    if [[ $exit_code -ne 0 ]]; then
        log_error "Pipeline failed at Stage 6 (Copy Outputs)"
        log_info "  Troubleshooting:"
        log_info "    - Check source directory: ls projects/$CURRENT_PROJECT/output/"
        log_info "    - Check destination: ls output/"
        log_info "    - Verify permissions: ls -la projects/$CURRENT_PROJECT/output/"
        log_info "    - Run manually: python3 scripts/05_copy_outputs.py"
        return 1
    fi
    stage_end=$(date +%s)
    STAGE_RESULTS[5]=0
    STAGE_DURATIONS[5]=$(get_elapsed_time "$stage_start" "$stage_end")

    # Success - print summary
    local pipeline_end=$(date +%s)
    local total_duration=$(get_elapsed_time "$pipeline_start" "$pipeline_end")

    print_pipeline_summary "$total_duration" "$log_file" "true"

    # Log completion to file
    {
        echo ""
        echo "============================================================"
        echo "Core pipeline completed: $(date)"
        echo "Total duration: $(format_duration "$total_duration")"
        echo "Log file: $log_file"
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
    #   $1: Base directory to scan (projects/$CURRENT_PROJECT/output or output)
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
    #   $1: Base directory to scan (projects/$CURRENT_PROJECT/output or output)
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
        elif [[ -n "${STAGE_DURATIONS[$i]:-}" ]]; then
            duration="${STAGE_DURATIONS[$i]}"
            stage_duration_map[$i]="$duration"
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
    # Generate file inventory for both projects/$CURRENT_PROJECT/output and output directories
    local project_output_dir="$REPO_ROOT/projects/$CURRENT_PROJECT/output"
    local output_dir="$REPO_ROOT/output"
    
    # Check which directory has files (prefer output/ if it exists and has files, otherwise projects/$CURRENT_PROJECT/output/)
    if [[ -d "$output_dir" ]] && [[ -n "$(collect_generated_files "$output_dir" 2>/dev/null)" ]]; then
        generate_file_inventory "$output_dir" "$log_file"
        log_info "Note: Files are also available in projects/$CURRENT_PROJECT/output/ during development"
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
            run_llm_scientific_review
            exit_code=$?
            ;;
        6)
            run_llm_translations
            exit_code=$?
            ;;
        7)
            run_core_pipeline_no_llm
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

show_project_info() {
    local project_dir="$REPO_ROOT/projects/$CURRENT_PROJECT"

    echo
    echo -e "${BOLD}${CYAN}Project Information: $CURRENT_PROJECT${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo

    # Basic info
    echo -e "${BOLD}Location:${NC} $project_dir"
    echo

    # Description from pyproject.toml or README
    local description=""
    if [[ -f "$project_dir/pyproject.toml" ]]; then
        description=$(grep "^description" "$project_dir/pyproject.toml" 2>/dev/null | cut -d'"' -f2)
    elif [[ -f "$project_dir/README.md" ]]; then
        description=$(head -5 "$project_dir/README.md" | grep -v "^#" | head -1 | xargs)
    fi

    if [[ -n "$description" ]]; then
        echo -e "${BOLD}Description:${NC} $description"
        echo
    fi

    # Directory structure
    echo -e "${BOLD}Structure:${NC}"
    local dirs=("src" "tests" "scripts" "manuscript" "output")
    for dir_name in "${dirs[@]}"; do
        if [[ -d "$project_dir/$dir_name" ]]; then
            local count=""
            if [[ "$dir_name" != "output" ]]; then
                count=$(find "$project_dir/$dir_name" -type f 2>/dev/null | wc -l | xargs)
                count=" ($count files)"
            fi
            echo -e "  ✅ $dir_name$count"
        else
            echo -e "  ❌ $dir_name"
        fi
    done
    echo

    # Recent output if exists
    local output_dir="$project_dir/output"
    if [[ -d "$output_dir" ]]; then
        echo -e "${BOLD}Recent Output:${NC}"
        local recent_files=$(find "$output_dir" -type f -mtime -7 2>/dev/null | head -5)
        if [[ -n "$recent_files" ]]; then
            echo "$recent_files" | while read -r file; do
                local size=$(du -h "$file" 2>/dev/null | cut -f1)
                local rel_path="${file#$project_dir/}"
                echo -e "  📄 $rel_path ($size)"
            done
        else
            echo -e "  ${GRAY}No recent output files${NC}"
        fi
        echo
    fi
}

run_all_projects() {
    log_header "RUNNING ALL PROJECTS"

    local failed_projects=()
    local total_projects=${#PROJECT_LIST[@]}

    for i in "${!PROJECT_LIST[@]}"; do
        local project_name="${PROJECT_LIST[$i]}"
        echo
        log_header "PROJECT $((i+1))/$total_projects: $project_name"
        echo

        # Temporarily set current project
        local old_project="$CURRENT_PROJECT"
        CURRENT_PROJECT="$project_name"

        # Run full pipeline for this project
        if run_full_pipeline; then
            log_success "✅ Project '$project_name' completed successfully"
        else
            log_error "❌ Project '$project_name' failed"
            failed_projects+=("$project_name")
        fi

        # Restore current project
        CURRENT_PROJECT="$old_project"
    done

    echo
    log_header "ALL PROJECTS SUMMARY"

    if [[ ${#failed_projects[@]} -eq 0 ]]; then
        log_success "🎉 All $total_projects projects completed successfully!"
    else
        log_error "❌ ${#failed_projects[@]} out of $total_projects projects failed:"
        for project in "${failed_projects[@]}"; do
            echo -e "  ❌ $project"
        done
        return 1
    fi

    return 0
}

# ============================================================================
# Executive Reporting Integration
# ============================================================================

run_executive_reporting() {
    local total_projects=$1

    # Only run if multiple projects
    if [[ $total_projects -lt 2 ]]; then
        log_info "Skipping executive reporting (requires 2+ projects)"
        return 0
    fi

    log_header "EXECUTIVE REPORTING - CROSS-PROJECT ANALYSIS"

    cd "$REPO_ROOT"

    local exit_code
    $(get_python_cmd) scripts/07_generate_executive_report.py 2>&1
    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        log_success "Executive reporting complete"
        log_info "Reports saved to: output/executive_summary/"
        log_info "  • consolidated_report.{json,html,md}"
        log_info "  • dashboard.{png,pdf,html}"
        return 0
    else
        log_warning "Executive reporting had issues (non-critical)"
        return 0  # Don't fail pipeline
    fi
}

run_all_projects_full() {
    log_header "RUNNING ALL PROJECTS - FULL PIPELINE (WITH INFRASTRUCTURE TESTS, WITH LLM)"

    local failed_projects=()
    local total_projects=${#PROJECT_LIST[@]}

    for i in "${!PROJECT_LIST[@]}"; do
        local project_name="${PROJECT_LIST[$i]}"
        echo
        log_header "PROJECT $((i+1))/$total_projects: $project_name (Full Pipeline)"
        echo

        # Temporarily set current project
        local old_project="$CURRENT_PROJECT"
        CURRENT_PROJECT="$project_name"

        # Run full pipeline (10 stages: 0-9) for this project
        if run_full_pipeline; then
            log_success "✅ Project '$project_name' completed successfully"
        else
            log_error "❌ Project '$project_name' failed"
            failed_projects+=("$project_name")
        fi

        # Restore current project
        CURRENT_PROJECT="$old_project"
    done

    echo
    log_header "ALL PROJECTS SUMMARY - FULL PIPELINE"

    if [[ ${#failed_projects[@]} -eq 0 ]]; then
        log_success "🎉 All $total_projects projects completed successfully (full pipeline)!"

        # Generate executive report (multi-project only)
        run_executive_reporting $total_projects

    else
        log_error "❌ ${#failed_projects[@]} out of $total_projects projects failed:"
        for project in "${failed_projects[@]}"; do
            echo -e "  ❌ $project"
        done
        return 1
    fi

    return 0
}

run_all_projects_full_no_infra() {
    log_header "RUNNING ALL PROJECTS - FULL PIPELINE (NO INFRASTRUCTURE TESTS, WITH LLM)"

    local failed_projects=()
    local total_projects=${#PROJECT_LIST[@]}

    for i in "${!PROJECT_LIST[@]}"; do
        local project_name="${PROJECT_LIST[$i]}"
        echo
        log_header "PROJECT $((i+1))/$total_projects: $project_name (Full Pipeline, No Infra)"
        echo

        # Temporarily set current project
        local old_project="$CURRENT_PROJECT"
        CURRENT_PROJECT="$project_name"

        # Run full pipeline without infrastructure tests for this project
        if run_full_pipeline_no_infra; then
            log_success "✅ Project '$project_name' completed successfully"
        else
            log_error "❌ Project '$project_name' failed"
            failed_projects+=("$project_name")
        fi

        # Restore current project
        CURRENT_PROJECT="$old_project"
    done

    echo
    log_header "ALL PROJECTS SUMMARY - FULL PIPELINE (NO INFRA)"

    if [[ ${#failed_projects[@]} -eq 0 ]]; then
        log_success "🎉 All $total_projects projects completed successfully (full pipeline, no infra)!"

        # Generate executive report (multi-project only)
        run_executive_reporting $total_projects

    else
        log_error "❌ ${#failed_projects[@]} out of $total_projects projects failed:"
        for project in "${failed_projects[@]}"; do
            echo -e "  ❌ $project"
        done
        return 1
    fi

    return 0
}

run_all_projects_core() {
    log_header "RUNNING ALL PROJECTS - CORE PIPELINE (WITH INFRASTRUCTURE TESTS, NO LLM)"

    local failed_projects=()
    local total_projects=${#PROJECT_LIST[@]}

    for i in "${!PROJECT_LIST[@]}"; do
        local project_name="${PROJECT_LIST[$i]}"
        echo
        log_header "PROJECT $((i+1))/$total_projects: $project_name (Core Pipeline)"
        echo

        # Temporarily set current project
        local old_project="$CURRENT_PROJECT"
        CURRENT_PROJECT="$project_name"

        # Run core pipeline (stages 0-7, no LLM) for this project
        if run_core_pipeline_no_llm; then
            log_success "✅ Project '$project_name' completed successfully"
        else
            log_error "❌ Project '$project_name' failed"
            failed_projects+=("$project_name")
        fi

        # Restore current project
        CURRENT_PROJECT="$old_project"
    done

    echo
    log_header "ALL PROJECTS SUMMARY - CORE PIPELINE"

    if [[ ${#failed_projects[@]} -eq 0 ]]; then
        log_success "🎉 All $total_projects projects completed successfully (core pipeline)!"

        # Generate executive report (multi-project only)
        run_executive_reporting $total_projects

    else
        log_error "❌ ${#failed_projects[@]} out of $total_projects projects failed:"
        for project in "${failed_projects[@]}"; do
            echo -e "  ❌ $project"
        done
        return 1
    fi

    return 0
}

run_all_projects_core_no_infra() {
    log_header "RUNNING ALL PROJECTS - CORE PIPELINE (NO INFRASTRUCTURE TESTS, NO LLM)"

    local failed_projects=()
    local total_projects=${#PROJECT_LIST[@]}

    for i in "${!PROJECT_LIST[@]}"; do
        local project_name="${PROJECT_LIST[$i]}"
        echo
        log_header "PROJECT $((i+1))/$total_projects: $project_name (Core Pipeline, No Infra)"
        echo

        # Temporarily set current project
        local old_project="$CURRENT_PROJECT"
        CURRENT_PROJECT="$project_name"

        # Run core pipeline without infrastructure tests for this project
        if run_core_pipeline_no_llm_no_infra; then
            log_success "✅ Project '$project_name' completed successfully"
        else
            log_error "❌ Project '$project_name' failed"
            failed_projects+=("$project_name")
        fi

        # Restore current project
        CURRENT_PROJECT="$old_project"
    done

    echo
    log_header "ALL PROJECTS SUMMARY - CORE PIPELINE (NO INFRA)"

    if [[ ${#failed_projects[@]} -eq 0 ]]; then
        log_success "🎉 All $total_projects projects completed successfully (core pipeline, no infra)!"

        # Generate executive report (multi-project only)
        run_executive_reporting $total_projects

    else
        log_error "❌ ${#failed_projects[@]} out of $total_projects projects failed:"
        for project in "${failed_projects[@]}"; do
            echo -e "  ❌ $project"
        done
        return 1
    fi

    return 0
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
    echo "  5  LLM Review (requires Ollama) (06_llm_review.py --reviews-only)"
    echo "  6  LLM Translations (requires Ollama) (06_llm_review.py --translations-only)"
    echo
    echo "Orchestration:"
    echo "  7  Run Core Pipeline (stages 0-7: no LLM)"
    echo "  8  Run Full Pipeline (10 stages: 0-9)"
    echo "  9  Run Full Pipeline (skip infrastructure tests)"
    echo
echo "Multi-Project Operations:"
echo "  a  Run all projects - Full pipeline (with infra, with LLM) + Executive Report"
echo "  b  Run all projects - Full pipeline (no infra, with LLM) + Executive Report"
echo "  c  Run all projects - Core pipeline (with infra, no LLM) + Executive Report"
echo "  d  Run all projects - Core pipeline (no infra, no LLM) + Executive Report"
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
    # Initialize project discovery FIRST
    if ! discover_projects; then
        log_error "Failed to discover projects"
        exit 1
    fi

    # Set default project if it exists
    if [[ " ${PROJECT_LIST[*]} " == *" project "* ]]; then
        CURRENT_PROJECT="project"
    elif [[ ${#PROJECT_LIST[@]} -gt 0 ]]; then
        CURRENT_PROJECT="${PROJECT_LIST[0]}"
    else
        log_error "No valid projects found"
        exit 1
    fi

    # Parse command line arguments (now PROJECT_LIST is available)
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_help
                exit 0
                ;;
            --project)
                if [[ -z "${2:-}" ]]; then
                    log_error "Missing project name after --project"
                    show_help
                    exit 1
                fi
                # Validate project exists (but don't exit on validation failure if --help follows)
                if [[ " ${PROJECT_LIST[*]} " != *" $2 "* ]]; then
                    # Check if --help is coming next
                    if [[ "${3:-}" == "--help" ]] || [[ "${3:-}" == "-h" ]]; then
                        show_help
                        exit 0
                    fi
                    log_error "Project '$2' not found. Available: ${PROJECT_LIST[*]}"
                    exit 1
                fi
                CURRENT_PROJECT="$2"
                shift 2
                ;;
            --all-projects)
                CURRENT_PROJECT="all"
                shift
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

        echo -n "Select option [0-9, p, i]: "
        read -r choice

        local exit_code=0

        case "$choice" in
            a|A)
                run_all_projects_full
                exit_code=$?
                ;;
            b|B)
                run_all_projects_full_no_infra
                exit_code=$?
                ;;
            c|C)
                run_all_projects_core
                exit_code=$?
                ;;
            d|D)
                run_all_projects_core_no_infra
                exit_code=$?
                ;;
            p|P)
                select_project
                if [[ "$SELECTED_PROJECT" == "all" ]]; then
                    run_all_projects
                    exit_code=$?
                else
                    CURRENT_PROJECT="$SELECTED_PROJECT"
                fi
                ;;
            i|I)
                show_project_info
                ;;
            *)
                if parse_choice_sequence "$choice" && [[ ${#SHORTHAND_CHOICES[@]} -gt 1 ]]; then
                    run_option_sequence "${SHORTHAND_CHOICES[@]}"
                    exit_code=$?
                else
                    handle_menu_choice "$choice"
                    exit_code=$?
                fi
                ;;
        esac

        if [[ $exit_code -ne 0 ]]; then
            log_error "Last operation exited with code $exit_code"
        fi

        press_enter_to_continue
    done
}

# Run main
main "$@"
