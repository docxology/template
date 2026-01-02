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
#   8. Run Full Pipeline (9 stages: [1/9] to [9/9])
#
# Non-interactive mode: Use dedicated flags (--pipeline, --infra-tests, etc.)
#
# PROJECT DISCOVERY: This script discovers and operates only on active projects
# in the projects/ directory. Projects in projects_archive/ are preserved but
# not discovered or executed by infrastructure.
#
# Exit codes: 0 = success, 1 = failure, 2 = skipped (for optional stages)
#
# ARCHITECTURE: Thin Orchestration Pattern
# =========================================
# This script follows the thin orchestrator pattern where all business logic
# resides in infrastructure/ and projects/{name}/src/ modules. This script acts
# as a lightweight coordinator that:
#
# 1. Provides user interface (interactive menu)
# 2. Delegates to Python orchestrators (execute_pipeline.py, execute_multi_project.py)
# 3. Handles high-level coordination and error reporting
# 4. Does NOT implement any scientific algorithms or business logic
#
# Business logic is implemented in:
# - infrastructure/ : Generic, reusable modules (rendering, validation, etc.)
# - projects/{name}/src/ : Project-specific scientific code and analysis
#
# This separation enables:
# - Reusability across projects
# - Thorough testing of business logic
# - Clean separation of concerns
# - Maintainable and extensible architecture
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
    # Discover available projects using Python infrastructure module
    # Sets PROJECT_LIST array with project names
    PROJECT_LIST=()

    # Use Python module for project discovery
    local python_output
    if ! python_output=$(python3 -c "
import sys
sys.path.insert(0, '$REPO_ROOT')
from infrastructure.project.discovery import discover_projects
from pathlib import Path

try:
    projects = discover_projects(Path('$REPO_ROOT'))
    for project in projects:
        print(project.name)
except Exception as e:
    print('ERROR:' + str(e), file=sys.stderr)
    sys.exit(1)
"); then
        log_error "Failed to discover projects using Python module"
        return 1
    fi

    # Convert Python output to bash array
    while IFS= read -r line; do
        PROJECT_LIST+=("$line")
    done <<< "$python_output"

    if [[ ${#PROJECT_LIST[@]} -eq 0 ]]; then
        log_error "No valid projects found in $REPO_ROOT/projects/"
        log_info "Projects must have src/ and tests/ directories"
        return 1
    fi

    log_info "Discovered ${#PROJECT_LIST[@]} projects: ${PROJECT_LIST[*]}"
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
    echo "  8. Run Full Pipeline (9 stages: [1/9] to [9/9])"
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

    log_stage_with_project 1 "Environment Setup" 9 "$project_name"
    log_project_context "$project_name" "Environment Setup"

    # Discover and display available projects
    log_info "Discovering available projects..."
    if ! discover_projects; then
        log_error "Failed to discover projects"
        return 1
    fi

    # Display discovered projects summary
    log_info "Discovered ${#PROJECT_LIST[@]} project(s):"
    for proj in "${PROJECT_LIST[@]}"; do
        local marker=""
        if [[ "$proj" == "$project_name" ]]; then
            marker="→ "
        else
            marker="  "
        fi

        # Check project structure
        local has_src=""
        local has_tests=""
        local has_scripts=""
        local has_manuscript=""

        [[ -d "$REPO_ROOT/projects/$proj/src" ]] && has_src="src"
        [[ -d "$REPO_ROOT/projects/$proj/tests" ]] && has_tests="tests"
        [[ -d "$REPO_ROOT/projects/$proj/scripts" ]] && has_scripts="scripts"
        [[ -d "$REPO_ROOT/projects/$proj/manuscript" ]] && has_manuscript="manuscript"

        local structure_parts=()
        [[ -n "$has_src" ]] && structure_parts+=("src")
        [[ -n "$has_tests" ]] && structure_parts+=("tests")
        [[ -n "$has_scripts" ]] && structure_parts+=("scripts")
        [[ -n "$has_manuscript" ]] && structure_parts+=("manuscript")

        local structure_str="${structure_parts[*]}"
        echo -e "${marker}${BOLD}${proj}${NC}: ${structure_str}"
    done
    echo

    # Execute Python setup script
    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage setup
    return $?
}

run_all_tests() {
    local project_name="${1:-$CURRENT_PROJECT}"

    log_stage_with_project 2 "Infrastructure Tests" 9 "$project_name"
    log_stage_with_project 3 "Project Tests" 9 "$project_name"
    log_project_context "$project_name" "Testing"

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage tests
    return $?
}

run_infrastructure_tests() {
    log_header "INFRASTRUCTURE TESTS"

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$CURRENT_PROJECT" --stage infra_tests
    return $?
}

run_project_tests() {
    local project_name="${1:-$CURRENT_PROJECT}"

    log_header "PROJECT TESTS - Project: $project_name"

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage project_tests
    return $?
}

run_analysis() {
    local project_name="${1:-$CURRENT_PROJECT}"

    log_stage_with_project 4 "Project Analysis" 9 "$project_name"
    log_project_context "$project_name" "Analysis"

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage analysis
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        log_output_path "Results" "projects/$project_name/output/data/"
    fi
    return $exit_code
}

run_analysis_standalone() {
    # Standalone analysis execution (menu option 2)
    log_header "RUN ANALYSIS (02_run_analysis.py)"

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$CURRENT_PROJECT" --stage analysis
    return $?
}

run_pdf_rendering() {
    local project_name="${1:-$CURRENT_PROJECT}"

    log_stage_with_project 5 "PDF Rendering" 9 "$project_name"
    log_project_context "$project_name" "PDF Rendering"

    log_info "Rendering PDF manuscript..."
    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage render_pdf
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        log_output_path "PDFs" "projects/$project_name/output/pdf/"
    fi
    return $exit_code
}

run_validation() {
    local project_name="${1:-$CURRENT_PROJECT}"

    log_stage_with_project 6 "Output Validation" 9 "$project_name"
    log_project_context "$project_name" "Validation"

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage validate
    return $?
}

run_validation_standalone() {
    # Standalone validation execution (menu option 4)
    log_header "VALIDATE OUTPUT (04_validate_output.py)"

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$CURRENT_PROJECT" --stage validate
    return $?
}

run_copy_outputs() {
    local project_name="${1:-$CURRENT_PROJECT}"

    log_stage_with_project 9 "Copy Outputs" 9 "$project_name"
    log_project_context "$project_name" "Copy Outputs"

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage copy
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        log_output_path "Final deliverables" "output/$project_name/"
    fi
    return $exit_code
}

run_copy_outputs_standalone() {
    # Standalone copy outputs execution (menu option 5)
    log_header "COPY OUTPUTS (05_copy_outputs.py)"

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$CURRENT_PROJECT" --stage copy
    return $?
}

run_llm_scientific_review() {
    local project_name="${1:-$CURRENT_PROJECT}"

    log_stage_with_project 7 "LLM Scientific Review" 9 "$project_name"
    log_project_context "$project_name" "LLM Scientific Review"

    log_info "Running LLM scientific review (requires Ollama)..."
    log_info "Generating: executive summary, quality review, methodology review, improvements"

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage llm_reviews
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM scientific review complete"
        log_output_path "LLM outputs" "projects/$project_name/output/llm/"
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

    log_stage_with_project 8 "LLM Translations" 9 "$project_name"
    log_project_context "$project_name" "LLM Translations"

    log_info "Running LLM translations (requires Ollama)..."
    log_info "Generating translations for configured languages (see config.yaml)"

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage llm_translations
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        log_success "LLM translations complete"
        log_output_path "Translations" "projects/$project_name/output/llm/"
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

    log_info "Running LLM review (requires Ollama)..."
    log_info "This will run both reviews and translations"
    
    local exit_code
    $(get_python_cmd) "$REPO_ROOT/scripts/06_llm_review.py" --project "$CURRENT_PROJECT"
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
    local skip_infra="${3:-false}"

    # THIN ORCHESTRATOR: Delegate to Python orchestrator script for pipeline execution
    # This follows the thin orchestration pattern - all pipeline logic is in Python infrastructure
    local args="--project $project_name"
    if [[ "$skip_infra" == "true" ]]; then
        args="$args --skip-infra"
    fi
    if [[ "$resume_flag" == "--resume" ]]; then
        args="$args --resume"
    fi

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args

    # Return the exit code from Python
    return $?
}
run_core_pipeline_no_llm() {
    local resume_flag="${1:-}"
    local project_name="${2:-$CURRENT_PROJECT}"
    local skip_infra="${3:-false}"

    # Use Python orchestrator script for pipeline execution
    local args="--project $project_name --core-only"
    if [[ "$skip_infra" == "true" ]]; then
        args="$args --skip-infra"
    fi
    if [[ "$resume_flag" == "--resume" ]]; then
        args="$args --resume"
    fi

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args

    # Return the exit code from Python
    return $?
}
run_all_projects_full() {
    log_header "RUNNING ALL PROJECTS - FULL PIPELINE (WITH INFRASTRUCTURE TESTS, WITH LLM)"

    # Use Python orchestrator script for multi-project execution
    $(get_python_cmd) "$REPO_ROOT/scripts/execute_multi_project.py"

    # Return the exit code from Python
    return $?
}

run_all_projects_core() {
    log_header "RUNNING ALL PROJECTS - CORE PIPELINE (WITH INFRASTRUCTURE TESTS, NO LLM)"

    # Use Python orchestrator script for multi-project execution
    $(get_python_cmd) "$REPO_ROOT/scripts/execute_multi_project.py" --no-llm

    # Return the exit code from Python
    return $?
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
    echo "  8  Run Full Pipeline (9 stages: [1/9] to [9/9])"
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


# Run main

press_enter_to_continue() {
    echo
    echo -e "${CYAN}Press Enter to continue...${NC}"
    read -r
}

parse_choice_sequence() {
    # Parse choice sequences like "345" into individual options
    # Sets SHORTHAND_CHOICES array with parsed options
    # Returns: 0 if valid sequence, 1 if invalid
    local choice="$1"
    
    SHORTHAND_CHOICES=()
    
    # Check if it's a multi-digit sequence
    if [[ "$choice" =~ ^[0-9]+$ ]] && [[ ${#choice} -gt 1 ]]; then
        # Split into individual digits
        local i
        for ((i=0; i<${#choice}; i++)); do
            local digit="${choice:$i:1}"
            if [[ "$digit" =~ [0-9] ]]; then
                SHORTHAND_CHOICES+=("$digit")
            else
                return 1
            fi
        done
        return 0
    elif [[ "$choice" =~ ^[0-9]+[,][0-9]+$ ]]; then
        # Handle comma-separated like "3,4,5"
        local cleaned_choice="${choice//,/}"
        if [[ "$cleaned_choice" =~ ^[0-9]+$ ]]; then
            # Split on commas and add to array
            IFS=',' read -ra SHORTHAND_CHOICES <<< "$choice"
            return 0
        fi
    fi
    
    return 1
}

run_option_sequence() {
    # Run a sequence of menu options in order, stopping on first failure.
    # Args: options to run as separate arguments
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

handle_menu_choice() {
    # THIN ORCHESTRATOR: Menu handler delegates to Python infrastructure modules
    # This function coordinates user choices but all actual work is done by
    # infrastructure/ modules (PipelineExecutor, MultiProjectOrchestrator, etc.)
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

run_all_projects() {
    log_header "RUNNING ALL PROJECTS"

    # Delegate to Python multi-project orchestrator so infra tests run once.
    $(get_python_cmd) "$REPO_ROOT/scripts/execute_multi_project.py"
    return $?
}

run_all_projects_full_no_infra() {
    log_header "RUNNING ALL PROJECTS - FULL PIPELINE (NO INFRASTRUCTURE TESTS, WITH LLM)"

    # Use Python orchestrator script for multi-project execution
    $(get_python_cmd) "$REPO_ROOT/scripts/execute_multi_project.py" --no-infra-tests

    # Return the exit code from Python
    return $?
}

run_all_projects_core_no_infra() {
    log_header "RUNNING ALL PROJECTS - CORE PIPELINE (NO INFRASTRUCTURE TESTS, NO LLM)"

    # Use Python orchestrator script for multi-project execution
    $(get_python_cmd) "$REPO_ROOT/scripts/execute_multi_project.py" --no-infra-tests --no-llm

    # Return the exit code from Python
    return $?
}

run_full_pipeline_no_infra() {
    local resume_flag="${1:-}"
    local project_name="${2:-$CURRENT_PROJECT}"

    # Use Python orchestrator script for pipeline execution
    local args="--project $project_name --skip-infra"
    if [[ "$resume_flag" == "--resume" ]]; then
        args="$args --resume"
    fi

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args

    # Return the exit code from Python
    return $?
}

run_core_pipeline_no_llm_no_infra() {
    local resume_flag="${1:-}"
    local project_name="${2:-$CURRENT_PROJECT}"

    # Use Python orchestrator script for pipeline execution
    local args="--project $project_name --core-only --skip-infra"
    if [[ "$resume_flag" == "--resume" ]]; then
        args="$args --resume"
    fi

    $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args

    # Return the exit code from Python
    return $?
}

show_project_info() {
    local project_name="${1:-$CURRENT_PROJECT}"

    clear
    $(get_python_cmd) "$REPO_ROOT/scripts/show_project_info.py" --project "$project_name"
    return $?
}

main() {
    # Initialize project discovery using Python module
    if ! $(get_python_cmd) -c "
import sys
sys.path.insert(0, '$REPO_ROOT')
from infrastructure.project.discovery import discover_projects
from pathlib import Path

try:
    projects = discover_projects(Path('$REPO_ROOT'))
    for project in projects:
        print(project.name)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" > /tmp/project_list.txt 2>&1; then
        log_error "Failed to discover projects"
        cat /tmp/project_list.txt
        exit 1
    fi

    # Read projects into array (bash 3.2 compatible)
    PROJECT_LIST=()
    while IFS= read -r line; do
        if [[ "$line" != ERROR* ]]; then
            PROJECT_LIST+=("$line")
        fi
    done < /tmp/project_list.txt

    # Clean up temp file
    rm -f /tmp/project_list.txt

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
                continue
                ;;
            --all-projects)
                CURRENT_PROJECT="all"
                shift
                continue
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
