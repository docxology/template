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
    # Sets PROJECT_LIST array with project qualified names (including program prefix for nested projects)
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
        # Use qualified_name to include program directory for nested projects
        # e.g., 'cognitive_integrity/cogsec_multiagent_1_theory' instead of 'cogsec_multiagent_1_theory'
        print(project.qualified_name)
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

    # Header with project name
    echo -e "${BOLD}${BLUE}┌────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BOLD}${BLUE}│${NC}  ${BOLD}📄 MANUSCRIPT PIPELINE${NC}                                        ${BLUE}│${NC}"
    echo -e "${BOLD}${BLUE}│${NC}  Project: ${CYAN}${CURRENT_PROJECT}${NC}$(printf '%*s' $((42 - ${#CURRENT_PROJECT})) '')${BLUE}│${NC}"
    echo -e "${BOLD}${BLUE}└────────────────────────────────────────────────────────────────┘${NC}"
    echo

    # Core Pipeline Scripts
    echo -e "${BOLD}⚙️  INDIVIDUAL STAGES${NC}"
    echo -e "    ${GREEN}0${NC}  Setup Environment          ${CYAN}00_setup_environment.py${NC}"
    echo -e "    ${GREEN}1${NC}  Run Tests                  ${CYAN}01_run_tests.py${NC}"
    echo -e "    ${GREEN}2${NC}  Run Analysis               ${CYAN}02_run_analysis.py${NC}"
    echo -e "    ${GREEN}3${NC}  Render PDF                 ${CYAN}03_render_pdf.py${NC}"
    echo -e "    ${GREEN}4${NC}  Validate Output            ${CYAN}04_validate_output.py${NC}"
    echo -e "    ${GREEN}5${NC}  LLM Review                 ${CYAN}06_llm_review.py${NC} ${YELLOW}⚡${NC}"
    echo -e "    ${GREEN}6${NC}  LLM Translations           ${CYAN}06_llm_review.py${NC} ${YELLOW}⚡${NC}"
    echo

    # Orchestration
    echo -e "${BOLD}🚀 ORCHESTRATION${NC}"
    echo -e "    ${GREEN}7${NC}  Core Pipeline              ${CYAN}Stages 1-7 (no LLM)${NC}"
    echo -e "    ${GREEN}8${NC}  Full Pipeline              ${CYAN}All 9 stages${NC}"
    echo -e "    ${GREEN}9${NC}  Full Pipeline (fast)       ${CYAN}Skip infra tests${NC}"
    echo

    # Multi-Project Operations
    echo -e "${BOLD}📚 MULTI-PROJECT${NC}"
    echo -e "    ${GREEN}a${NC}  All projects full          ${CYAN}+infra +LLM +report${NC}"
    echo -e "    ${GREEN}b${NC}  All projects full (fast)   ${CYAN}-infra +LLM +report${NC}"
    echo -e "    ${GREEN}c${NC}  All projects core          ${CYAN}+infra -LLM +report${NC}"
    echo -e "    ${GREEN}d${NC}  All projects core (fast)   ${CYAN}-infra -LLM +report${NC}"
    echo

    # Project Management
    echo -e "${BOLD}📁 PROJECT${NC}"
    echo -e "    ${GREEN}p${NC}  Change Project             ${GREEN}i${NC}  Show Project Info"
    echo -e "    ${GREEN}q${NC}  Quit"
    echo

    # Status bar
    echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"
    local py_version=$($(get_python_cmd) --version 2>&1 | cut -d' ' -f2)
    local ollama_status="${RED}●${NC}"
    command -v ollama &>/dev/null && ollama list &>/dev/null 2>&1 && ollama_status="${GREEN}●${NC}"
    echo -e "  ${CYAN}Python${NC} $py_version  │  ${CYAN}Ollama${NC} $ollama_status  │  ${CYAN}Logs${NC} projects/*/output/logs/"
    echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"
    echo
    echo -e "${CYAN}💡 Tip:${NC} Chain commands: ${GREEN}345${NC} = analyze → render → validate"
}

# ============================================================================
# Clean Output Directories
# ============================================================================

clean_output_directories() {
    # Clean and recreate output directories for fresh pipeline run.
    # Uses the Python infrastructure function that handles multi-project structure correctly.
    echo
    echo -e "${YELLOW}[0/9] Clean Output Directories${NC}"
    echo -e "${GRAY}────────────────────────────────────────────────────────────────${NC}"
    echo -e "  ${CYAN}Project:${NC} $CURRENT_PROJECT"
    echo -e "  ${CYAN}Target:${NC}  projects/$CURRENT_PROJECT/output/"
    echo -e "${GRAY}────────────────────────────────────────────────────────────────${NC}"

    # Use Python function that handles multi-project structure correctly
    $(get_python_cmd) -c "
from infrastructure.core.file_operations import clean_output_directories
from pathlib import Path
import sys

repo_root = Path('$REPO_ROOT')
sys.path.insert(0, str(repo_root))
clean_output_directories(repo_root, '$CURRENT_PROJECT')
"

    log_success "Output directories cleaned - fresh start"
}

# ============================================================================
# Common Test Execution Functions
# ============================================================================

run_pytest_infrastructure() {
    # Execute infrastructure tests with coverage requirements.
    # Runs pytest on tests/infra_tests/ with 60% coverage threshold.
    # Skips requires_ollama tests by default.
    # Returns: 0 on success, 1 on failure
    cd "$REPO_ROOT"
    
    log_info "Running infrastructure module tests..."
    log_info "(Skipping LLM integration tests - run separately with: pytest -m requires_ollama)"
    
    $(get_pytest_cmd) tests/infra_tests/ \
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
# Logging Helpers for Comprehensive File Output
# ============================================================================

setup_stage_logging() {
    # Setup logging for individual stage execution.
    # Creates log directory and sets PIPELINE_LOG_FILE for tee-based logging.
    # Args:
    #   $1: project_name
    #   $2: stage_name (optional, for log file naming)
    local project_name="${1:-$CURRENT_PROJECT}"
    local stage_name="${2:-stage}"

    local log_dir="$REPO_ROOT/projects/$project_name/output/logs"
    mkdir -p "$log_dir" 2>/dev/null || true

    # Use a consistent log file for all stages within a project
    export PIPELINE_LOG_FILE="$log_dir/pipeline.log"

    # Log session start marker
    if [[ -n "$PIPELINE_LOG_FILE" ]]; then
        echo "" >> "$PIPELINE_LOG_FILE"
        echo "======================================================================" >> "$PIPELINE_LOG_FILE"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting: $stage_name" >> "$PIPELINE_LOG_FILE"
        echo "======================================================================" >> "$PIPELINE_LOG_FILE"
    fi
}

setup_multiproject_logging() {
    # Setup logging for multi-project execution.
    # Creates consolidated log in output/multi_project_summary/
    local log_dir="$REPO_ROOT/output/multi_project_summary"
    mkdir -p "$log_dir" 2>/dev/null || true

    export PIPELINE_LOG_FILE="$log_dir/multi_project_pipeline.log"

    if [[ -n "$PIPELINE_LOG_FILE" ]]; then
        echo "" >> "$PIPELINE_LOG_FILE"
        echo "======================================================================" >> "$PIPELINE_LOG_FILE"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Multi-Project Pipeline Started" >> "$PIPELINE_LOG_FILE"
        echo "======================================================================" >> "$PIPELINE_LOG_FILE"
    fi
}

execute_with_logging() {
    # Execute a Python command with tee-based logging.
    # Outputs to both terminal and log file simultaneously.
    # Args:
    #   $@: Command and arguments to execute
    local cmd="$@"
    local exit_code

    if [[ -n "$PIPELINE_LOG_FILE" ]]; then
        $cmd 2>&1 | tee -a "$PIPELINE_LOG_FILE"
        exit_code=${PIPESTATUS[0]}
    else
        $cmd
        exit_code=$?
    fi

    return $exit_code
}

show_completion_summary() {
    # Display completion summary with log file location.
    # Args:
    #   $1: Exit code (0=success, 1=failure)
    #   $2: Operation name
    #   $3: Duration in seconds
    local exit_code="$1"
    local operation="${2:-Operation}"
    local duration="${3:-0}"

    echo
    echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"
    if [[ $exit_code -eq 0 ]]; then
        echo -e "  ${GREEN}✓${NC} ${BOLD}$operation completed successfully${NC}"
    else
        echo -e "  ${RED}✗${NC} ${BOLD}$operation failed${NC} (exit code: $exit_code)"
    fi
    echo -e "  ${CYAN}Duration:${NC} $(format_duration "$duration")"
    if [[ -n "${PIPELINE_LOG_FILE:-}" ]]; then
        echo -e "  ${CYAN}Log file:${NC} $PIPELINE_LOG_FILE"
    fi
    echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"
}

# ============================================================================
# Individual Stage Functions
# ============================================================================

run_setup_environment() {
    local project_name="${1:-$CURRENT_PROJECT}"

    # Setup logging for this stage
    setup_stage_logging "$project_name" "Environment Setup"

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

    # Execute Python setup script with logging
    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage setup
    return $?
}

run_all_tests() {
    local project_name="${1:-$CURRENT_PROJECT}"

    # Setup logging for this stage
    setup_stage_logging "$project_name" "Testing"

    # Show combined test stage - run_tests.py handles infra+project sequentially with verbose logging
    log_stage_with_project 2 "Run Tests (Infrastructure + Project)" 9 "$project_name"
    log_project_context "$project_name" "Testing"

    # Strict Zero-Mock validation before running the test suite
    log_info "Running strict Zero-Mock policy validation..."
    if ! execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/verify_no_mocks.py"; then
        log_error "Zero-Mock validation failed - tests aborted"
        return 1
    fi

    # Run with verbose logging via the test runner
    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage tests
    return $?
}

run_infrastructure_tests() {
    # Setup logging for infrastructure tests
    setup_stage_logging "$CURRENT_PROJECT" "Infrastructure Tests"
    log_header "INFRASTRUCTURE TESTS"

    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$CURRENT_PROJECT" --stage infra_tests
    return $?
}

run_project_tests() {
    local project_name="${1:-$CURRENT_PROJECT}"

    # Setup logging for project tests
    setup_stage_logging "$project_name" "Project Tests"
    log_header "PROJECT TESTS - Project: $project_name"

    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage project_tests
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
    setup_stage_logging "$CURRENT_PROJECT" "Analysis"
    log_header "RUN ANALYSIS (02_run_analysis.py)"

    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$CURRENT_PROJECT" --stage analysis
    return $?
}

run_pdf_rendering() {
    local project_name="${1:-$CURRENT_PROJECT}"

    # Setup logging for this stage
    setup_stage_logging "$project_name" "PDF Rendering"

    log_stage_with_project 5 "PDF Rendering" 9 "$project_name"
    log_project_context "$project_name" "PDF Rendering"

    log_info "Rendering PDF manuscript..."
    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage render_pdf
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
    setup_stage_logging "$CURRENT_PROJECT" "Validation"
    log_header "VALIDATE OUTPUT (04_validate_output.py)"

    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$CURRENT_PROJECT" --stage validate
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

    # Setup logging for LLM review (captures Ollama output)
    setup_stage_logging "$project_name" "LLM Scientific Review"

    log_stage_with_project 7 "LLM Scientific Review" 9 "$project_name"
    log_project_context "$project_name" "LLM Scientific Review"

    log_info "Running LLM scientific review (requires Ollama)..."
    log_info "Generating: executive summary, quality review, methodology review, improvements"

    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage llm_reviews
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

    # Setup logging for LLM translations (captures Ollama output)
    setup_stage_logging "$project_name" "LLM Translations"

    log_stage_with_project 8 "LLM Translations" 9 "$project_name"
    log_project_context "$project_name" "LLM Translations"

    log_info "Running LLM translations (requires Ollama)..."
    log_info "Generating translations for configured languages (see config.yaml)"

    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" --project "$project_name" --stage llm_translations
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

    # Set up per-project log file for bash script output
    local log_dir="$REPO_ROOT/projects/$project_name/output/logs"
    mkdir -p "$log_dir"
    export PIPELINE_LOG_FILE="$log_dir/pipeline.log"

    # THIN ORCHESTRATOR: Delegate to Python orchestrator script for pipeline execution
    # This follows the thin orchestration pattern - all pipeline logic is in Python infrastructure
    local args="--project $project_name"
    if [[ "$skip_infra" == "true" ]]; then
        args="$args --skip-infra"
    fi
    if [[ "$resume_flag" == "--resume" ]]; then
        args="$args --resume"
    fi

    # Redirect output to log file while preserving terminal output
    if [[ -n "$PIPELINE_LOG_FILE" ]]; then
        $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args 2>&1 | tee -a "$PIPELINE_LOG_FILE"
        return ${PIPESTATUS[0]}  # Return Python script exit code
    else
        $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args
        return $?
    fi
}
run_core_pipeline_no_llm() {
    local resume_flag="${1:-}"
    local project_name="${2:-$CURRENT_PROJECT}"
    local skip_infra="${3:-false}"

    # Set up per-project log file for bash script output
    local log_dir="$REPO_ROOT/projects/$project_name/output/logs"
    mkdir -p "$log_dir"
    export PIPELINE_LOG_FILE="$log_dir/pipeline.log"

    # Use Python orchestrator script for pipeline execution
    local args="--project $project_name --core-only"
    if [[ "$skip_infra" == "true" ]]; then
        args="$args --skip-infra"
    fi
    if [[ "$resume_flag" == "--resume" ]]; then
        args="$args --resume"
    fi

    # Redirect output to log file while preserving terminal output
    if [[ -n "$PIPELINE_LOG_FILE" ]]; then
        $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args 2>&1 | tee -a "$PIPELINE_LOG_FILE"
        return ${PIPESTATUS[0]}  # Return Python script exit code
    else
        $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args
        return $?
    fi
}
run_all_projects_full() {
    # Setup consolidated multi-project logging
    setup_multiproject_logging
    log_header "RUNNING ALL PROJECTS - FULL PIPELINE (WITH INFRASTRUCTURE TESTS, WITH LLM)"

    # Use Python orchestrator script for multi-project execution with logging
    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_multi_project.py"

    # Return the exit code from Python
    return $?
}

run_all_projects_core() {
    # Setup consolidated multi-project logging
    setup_multiproject_logging
    log_header "RUNNING ALL PROJECTS - CORE PIPELINE (WITH INFRASTRUCTURE TESTS, NO LLM)"

    # Use Python orchestrator script for multi-project execution with logging
    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_multi_project.py" --no-llm

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
    echo
    echo -e "${BOLD}📄 MANUSCRIPT PIPELINE${NC}"
    echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"
    echo
    echo -e "${BOLD}USAGE${NC}"
    echo "  $0 [OPTIONS]"
    echo "  $0                     Interactive menu mode"
    echo
    echo -e "${BOLD}CLI FLAGS${NC}"
    echo -e "  ${GREEN}--pipeline${NC}            Full pipeline (9 stages)"
    echo -e "  ${GREEN}--resume${NC}              Resume from checkpoint"
    echo -e "  ${GREEN}--infra-tests${NC}         Infrastructure tests only"
    echo -e "  ${GREEN}--project-tests${NC}       Project tests only"
    echo -e "  ${GREEN}--render-pdf${NC}          PDF rendering only"
    echo -e "  ${GREEN}--reviews${NC}             LLM scientific review"
    echo -e "  ${GREEN}--translations${NC}        LLM translations"
    echo -e "  ${GREEN}--help, -h${NC}            This help message"
    echo
    echo -e "${BOLD}MENU OPTIONS${NC}"
    echo -e "  ${CYAN}Individual Stages:${NC}"
    echo "    0  Setup Environment       4  Validate Output"
    echo "    1  Run Tests               5  LLM Review"
    echo "    2  Run Analysis            6  LLM Translations"
    echo "    3  Render PDF"
    echo
    echo -e "  ${CYAN}Orchestration:${NC}"
    echo "    7  Core Pipeline (no LLM)  9  Full Pipeline (fast)"
    echo "    8  Full Pipeline (all)"
    echo
    echo -e "  ${CYAN}Multi-Project:${NC}"
    echo "    a  All full (+infra +LLM)  c  All core (+infra -LLM)"
    echo "    b  All full (-infra +LLM)  d  All core (-infra -LLM)"
    echo
    echo -e "${BOLD}CHAINING${NC}"
    echo -e "  Enter digits together: ${GREEN}345${NC} = analyze → render → validate"
    echo -e "  Or comma-separated:    ${GREEN}3,4,5${NC}"
    echo
    echo -e "${BOLD}LOG LOCATIONS${NC}"
    echo -e "  Single-project:  ${CYAN}projects/{name}/output/logs/pipeline.log${NC}"
    echo -e "  Multi-project:   ${CYAN}output/multi_project_summary/multi_project_pipeline.log${NC}"
    echo
    echo -e "${BOLD}EXAMPLES${NC}"
    echo "  $0                      Interactive mode"
    echo "  $0 --pipeline           Full pipeline, current project"
    echo "  $0 --pipeline --resume  Resume from checkpoint"
    echo "  $0 8                    Full pipeline (shorthand)"
    echo "  $0 345                  Chain: analyze → render → validate"
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
            log_info "Valid options: 0-9, a-d, p, i, q"
            exit_code=1
            ;;
    esac

    end_time=$(date +%s)
    duration=$(get_elapsed_time "$start_time" "$end_time")

    # Determine operation name for summary
    local op_name
    case "$choice" in
        0) op_name="Environment Setup" ;;
        1) op_name="Testing" ;;
        2) op_name="Analysis" ;;
        3) op_name="PDF Rendering" ;;
        4) op_name="Validation" ;;
        5) op_name="LLM Review" ;;
        6) op_name="LLM Translations" ;;
        7) op_name="Core Pipeline" ;;
        8) op_name="Full Pipeline" ;;
        9) op_name="Full Pipeline (fast)" ;;
        *) op_name="Operation" ;;
    esac

    show_completion_summary "$exit_code" "$op_name" "$duration"
    return $exit_code
}

run_all_projects() {
    # Setup consolidated multi-project logging
    setup_multiproject_logging
    log_header "RUNNING ALL PROJECTS"

    # Delegate to Python multi-project orchestrator so infra tests run once.
    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_multi_project.py"
    return $?
}

run_all_projects_full_no_infra() {
    # Setup consolidated multi-project logging
    setup_multiproject_logging
    log_header "RUNNING ALL PROJECTS - FULL PIPELINE (NO INFRASTRUCTURE TESTS, WITH LLM)"

    # Use Python orchestrator script for multi-project execution with logging
    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_multi_project.py" --no-infra-tests

    # Return the exit code from Python
    return $?
}

run_all_projects_core_no_infra() {
    # Setup consolidated multi-project logging
    setup_multiproject_logging
    log_header "RUNNING ALL PROJECTS - CORE PIPELINE (NO INFRASTRUCTURE TESTS, NO LLM)"

    # Use Python orchestrator script for multi-project execution with logging
    execute_with_logging $(get_python_cmd) "$REPO_ROOT/scripts/execute_multi_project.py" --no-infra-tests --no-llm

    # Return the exit code from Python
    return $?
}

run_full_pipeline_no_infra() {
    local resume_flag="${1:-}"
    local project_name="${2:-$CURRENT_PROJECT}"

    # Set up per-project log file for bash script output
    local log_dir="$REPO_ROOT/projects/$project_name/output/logs"
    mkdir -p "$log_dir"
    export PIPELINE_LOG_FILE="$log_dir/pipeline.log"

    # Use Python orchestrator script for pipeline execution
    local args="--project $project_name --skip-infra"
    if [[ "$resume_flag" == "--resume" ]]; then
        args="$args --resume"
    fi

    # Redirect output to log file while preserving terminal output
    if [[ -n "$PIPELINE_LOG_FILE" ]]; then
        $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args 2>&1 | tee -a "$PIPELINE_LOG_FILE"
        return ${PIPESTATUS[0]}  # Return Python script exit code
    else
        $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args
        return $?
    fi
}

run_core_pipeline_no_llm_no_infra() {
    local resume_flag="${1:-}"
    local project_name="${2:-$CURRENT_PROJECT}"

    # Set up per-project log file for bash script output
    local log_dir="$REPO_ROOT/projects/$project_name/output/logs"
    mkdir -p "$log_dir"
    export PIPELINE_LOG_FILE="$log_dir/pipeline.log"

    # Use Python orchestrator script for pipeline execution
    local args="--project $project_name --core-only --skip-infra"
    if [[ "$resume_flag" == "--resume" ]]; then
        args="$args --resume"
    fi

    # Redirect output to log file while preserving terminal output
    if [[ -n "$PIPELINE_LOG_FILE" ]]; then
        $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args 2>&1 | tee -a "$PIPELINE_LOG_FILE"
        return ${PIPESTATUS[0]}  # Return Python script exit code
    else
        $(get_python_cmd) "$REPO_ROOT/scripts/execute_pipeline.py" $args
        return $?
    fi
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
