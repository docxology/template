# scripts/ - Generic Entry Point Orchestrators

## Purpose

Root-level `scripts/` directory contains **generic entry point orchestrators** that coordinate the template's build pipeline. These are reusable across any project.

Scripts in this directory:
- Discover and invoke project-specific scripts
- Coordinate build stages (setup, test, analysis, pdf, validate)
- Handle template-level orchestration
- Work with ANY project structure

**Project-specific analysis scripts belong in `projects/{name}/scripts/`**, not here.

## Architectural Role

Root scripts are **thin orchestrators** that:
- Do NOT implement analysis or algorithms
- Discover and invoke `project/scripts/*.py`
- Handle I/O and orchestration
- Coordinate between stages
- Are generic across projects

## Entry Points

The template provides multiple entry points organized by function:

### Root-Level Scripts

**Main Entry Point** (`run.sh`):
- Interactive menu with manuscript pipeline operations (0-9)
- Full pipeline execution (10 stages: 0-9)
- Non-interactive: `./run.sh [options]` for direct pipeline operations
- Non-interactive flags: `--pipeline`, `--infra-tests`, `--project-tests`, `--render-pdf`, `--reviews`, `--translations`
- Sources shared utilities from `scripts/bash_utils.sh`

**Shared Utilities** (`scripts/bash_utils.sh`):
- Color codes and formatting
- Logging functions (log_header, log_success, log_error, etc.)
- Utility functions (format_duration, get_elapsed_time, parse_choice_sequence)
- File logging functions
- Sourced by `run.sh`

### Python Scripts

### 1. Setup Environment (`00_setup_environment.py`)

**Purpose:** Verify environment is ready for research template execution

**Core Functionality:**
- Checks Python version (3.8+ required)
- Verifies dependencies with uv package manager integration
- Confirms build tools availability (pandoc, xelatex)
- Validates and creates directory structure
- Sets environment variables for pipeline execution

**uv Integration Strategy:**
The setup prioritizes uv for dependency management due to its speed and reliability:
1. **Primary:** `uv sync` - Fast workspace dependency resolution
2. **Fallback:** Individual package checking/installation
3. **Guidance:** Clear messages for manual installation when uv unavailable

**Dependency Resolution Flow:**
```bash
Check uv availability
├── uv available? → uv sync (fast, preferred)
│   ├── Success → Continue
│   └── Failed → Individual package check/install
└── uv unavailable → Individual package check/install
    ├── All present → Continue
    └── Missing → Install packages → Verify
```

**Directory Structure Setup:**
Creates multi-project directory structure:
- `output/{project}/` - Project-specific outputs
- `projects/{project}/output/` - Working outputs
- Build artifacts, logs, reports, figures, data, tex, pdf, slides, web, llm directories

**Environment Variables:**
- `MPLBACKEND=Agg` - Headless matplotlib for server environments
- `PYTHONIOENCODING=utf-8` - Consistent text encoding
- `PROJECT_ROOT` - Repository root path for relative operations

**Error Handling:**
- Graceful fallback from uv to pip-based installation
- Clear error messages with actionable recovery steps
- Comprehensive logging with debug-level subprocess details

**Generic:** Works for any project in the multi-project template structure

**Troubleshooting:**
- **uv sync fails:** Check network, pyproject.toml validity, uv version
- **Missing packages:** Verify pip installation, check Python version compatibility
- **Build tools missing:** Install pandoc/xelatex, verify PATH configuration
- **Directory creation fails:** Check filesystem permissions, disk space

### 2. Run Tests (`01_run_tests.py`)

**Purpose:** Execute project test suite

- Runs infrastructure and project tests with pytest
- Verifies test coverage meets thresholds (60% infrastructure, 90% project)
- Generates coverage reports
- Generic orchestrator - does not implement tests

**Generic:** Works for any project using pytest

### 3. Run Analysis (`02_run_analysis.py`)

**Purpose:** Execute project analysis scripts

- Discovers scripts in `projects/{name}/scripts/`
- Executes each script in order
- Validates output generation
- Collects outputs to `projects/{name}/output/`

**Generic:** Works for any project with analysis scripts

### 4. Render PDF (`03_render_pdf.py`)

**Purpose:** Generate manuscript PDFs

- Processes `projects/{name}/manuscript/` markdown files
- Converts to LaTeX via pandoc
- Compiles to PDF via xelatex
- Generic orchestrator

**Generic:** Works for any markdown manuscript

### 5. Validate Output (`04_validate_output.py`)

**Purpose:** Validate build quality

- Checks generated PDFs for issues
- Validates markdown references
- Checks figure integrity
- Generic validation

**Generic:** Works for any project output

### 6. Copy Outputs (`05_copy_outputs.py`)

**Purpose:** Copy final deliverables to top-level output directory

- Cleans root-level directories from `output/` (keeps only project folders)
- Cleans project-specific `output/{name}/` directory
- Copies combined PDF manuscript
- Copies all presentation slides (PDF format)
- Copies all web outputs (HTML format)
- Validates all files copied successfully

**Notes:**
- Typically invoked as the final stage of the pipeline (via `execute_pipeline.py` / `run.sh --pipeline`).
- Can also be run directly when you only want to refresh `output/{project}/` from `projects/{project}/output/`.

**Generic:** Works for any project with rendered outputs

### 6. Audit Filepaths (`audit_filepaths.py`)

**Purpose:** Comprehensive audit of filepaths, references, and documentation accuracy using modular infrastructure validation.

**Core Functionality:**
- Thin orchestrator that coordinates `infrastructure.validation.audit_orchestrator`
- Discovers all markdown files in repository
- Validates internal/external links and file references
- Checks code block paths and directory structures
- Validates Python imports and placeholder consistency
- Generates structured reports (markdown/JSON formats)
- Categorizes issues by type and severity
- Filters false positives (Mermaid diagrams, LaTeX refs, templates)

**Function Signatures:**
```python
def main():
    """Main entry point for the audit script."""
    # Parse command line arguments
    # Run comprehensive audit via audit_orchestrator
    # Generate and save report
    # Exit with appropriate code based on issues found
```

**Usage Examples:**
```bash
# Basic audit with markdown report
python scripts/audit_filepaths.py

# JSON format output
python scripts/audit_filepaths.py --format json --output audit.json

# Verbose mode with custom output path
python scripts/audit_filepaths.py --verbose --output docs/audit/my_audit.md

# Audit specific project only
python scripts/audit_filepaths.py --project myproject
```

**Generic:** Works across entire repository or specific projects

### 7. Generate Executive Report (`07_generate_executive_report.py`)

**Purpose:** Generate cross-project executive summaries and dashboards

- Discovers all projects in repository
- Collects comprehensive metrics across all projects
- Generates comparative analysis and recommendations
- Creates visual dashboards (PNG, PDF, HTML)
- Saves reports to `output/executive_summary/`

**Function Signatures:**
```python
def discover_projects(repo_root: Path) -> list[ProjectInfo]:
    \"\"\"Discover all valid projects in the repository.\"\"\"
    pass

def collect_project_metrics(repo_root: Path, project_names: list[str]) -> dict:
    \"\"\"Collect metrics from all specified projects.\"\"\"
    pass

def generate_executive_dashboard(
    metrics: dict,
    output_dir: Path,
    formats: list[str] = None
) -> list[Path]:
    \"\"\"Generate executive dashboard in multiple formats.\"\"\"
    pass

def create_comparative_analysis(metrics: dict) -> dict:
    \"\"\"Create comparative analysis across projects.\"\"\"
    pass

def main():
    \"\"\"Main entry point for executive report generation.\"\"\"
    pass
```

**Generic:** Works with any number of projects (2+ required)

### 8. Pipeline Orchestrators

#### Single Project (`execute_pipeline.py`)

**Purpose:** Execute pipeline stages for a single project via `infrastructure.core.pipeline.PipelineExecutor`.

- Supports full pipeline and core-only pipeline
- Supports checkpoint resume
- Supports single-stage execution via `--stage`

**Function Signatures:**
```python
def execute_single_stage(stage: str, project_name: str, repo_root: Path) -> int:
    \"\"\"Execute a single pipeline stage.\"\"\"
    pass

def execute_pipeline(
    project_name: str,
    repo_root: Path,
    core_only: bool = False,
    resume: bool = False,
    start_stage: str = None
) -> int:
    \"\"\"Execute complete pipeline for a project.\"\"\"
    pass

def main():
    \"\"\"Main entry point with argument parsing.\"\"\"
    pass
```

#### Multi-Project (`execute_multi_project.py`)

**Purpose:** Execute pipelines across all discovered projects via `infrastructure.core.multi_project.MultiProjectOrchestrator`.

- Runs infrastructure tests once (optional)
- Runs each project pipeline with infra tests skipped per-project
- Optionally generates executive reporting

**Function Signatures:**
```python
def execute_multi_project(
    repo_root: Path,
    all_projects: bool = False,
    project_names: list[str] = None,
    core_only: bool = True,
    resume: bool = False
) -> int:
    \"\"\"Execute pipelines across multiple projects.\"\"\"
    pass

def main():
    \"\"\"Main entry point with argument parsing.\"\"\"
    pass
```


## Project-Specific Scripts

Analysis scripts specific to a project belong in `projects/{name}/scripts/`:

**Important:** Scripts in this directory operate **only on active projects** in the `projects/` directory. Projects in `projects_archive/` are **not discovered or executed** by any root-level scripts.

### Active vs Archived Projects

- **Active Projects (`projects/`):** Discovered and executed by all pipeline scripts
- **Archived Projects (`projects_archive/`):** Preserved but not executed

This separation ensures infrastructure focuses on current, active research while maintaining historical projects for reference.

```
projects/{name}/scripts/
├── analysis_pipeline.py     # Project-specific analysis
├── example_figure.py        # Project-specific figures
└── README.md                # Project script documentation
```

These scripts:
- Import from `projects/{name}/src/` for scientific computation
- Import from `infrastructure/` for document management
- Use the **thin orchestrator pattern**
- Are discovered and executed by root `02_run_analysis.py`

**Example:**
```python
# projects/{name}/scripts/analysis_pipeline.py
from data_generator import generate_synthetic_data
from statistics import calculate_descriptive_stats
from infrastructure.figure_manager import FigureManager

# Generate and analyze
data = generate_synthetic_data(n_samples=1000)
stats = calculate_descriptive_stats(data)

# Register output
fm = FigureManager()
fm.register_figure("results.png", label="fig:results")
```

## Pattern: Generic Orchestrator

### ✅ CORRECT Pattern (Root Entry Points)

Root entry points use **thin orchestrator pattern**:
- Import infrastructure modules, not business logic
- Coordinate between pipeline stages
- Delegate all computation to imported modules
- Work with ANY project following this structure

```python
# scripts/03_render_pdf.py - Generic orchestrator
from infrastructure.rendering import RenderManager

def run_render_pipeline() -> int:
    """Orchestrate PDF rendering stage."""
    # Use infrastructure modules
    renderer = RenderManager()
    
    # Discover manuscript files and render
    pdf = renderer.render_pdf(Path("manuscript.tex"))
    
    # Validate output
    report = validate_pdf_rendering(pdf)
    
    return 0 if not report['summary']['has_issues'] else 1
```

**Key Points:**
- Uses `infrastructure.<module>` imports
- Delegates computation to modules
- Coordinates pipeline stages
- Works with ANY project

### ✅ CORRECT Pattern (Project Scripts)

```python
# projects/{name}/scripts/analysis_pipeline.py - Project-specific orchestrator
from data_generator import generate_synthetic_data
from statistics import calculate_descriptive_stats

# Import from projects/{name}/src/ for computation
data = generate_synthetic_data()
stats = calculate_descriptive_stats(data)

# Import from infrastructure/ for document management
from infrastructure.figure_manager import FigureManager
fm = FigureManager()
fm.register_figure("results.png")
```

**Key Points:**
- Imports from `projects/{name}/src/` (computation)
- Imports from `infrastructure/` (utilities)
- Orchestrates workflow
- Handles I/O and visualization

### ❌ INCORRECT Pattern (Violates Architecture)

```python
# scripts/analysis_pipeline.py - WRONG location
from scientific.data_generator import generate_synthetic_data

# ❌ Root scripts should NOT contain analysis
# ❌ Duplicates projects/{name}/scripts/ logic
# ❌ Not generic across projects
```

## Integration with Build Pipeline

Complete pipeline execution (single project):

```bash
python3 scripts/execute_pipeline.py --project project --core-only
```

Stages:
1. **00_setup_environment.py** - Environment ready?
2. **01_run_tests.py** - Tests pass?
3. **02_run_analysis.py** - Executes `projects/{name}/scripts/*.py`
4. **03_render_pdf.py** - PDFs generated?
5. **04_validate_output.py** - Output valid?
6. **05_copy_outputs.py** - Final deliverables copied?
10. **07_generate_executive_report.py** - Executive summaries (multi-project only)

Each stage is **generic** and works with any project structure in `projects/{name}/`.

## Testing

Root entry points are tested through:
- Integration with project code
- Successful pipeline execution
- Correct delegation to project scripts

No unit tests needed for orchestrators - they're thin wrappers.

## Best Practices

### Do's ✅
- Keep root scripts generic
- Discover project scripts dynamically
- Delegate to `projects/{name}/scripts/`
- Handle I/O and orchestration
- Use clear logging

### Don'ts ❌
- Implement analysis in root scripts
- Hardcode paths to specific analyses
- Assume specific project structure
- Skip error handling
- Import from `projects/{name}/src/` in root scripts

## File Organization

```
scripts/
├── 00_setup_environment.py     # Entry: Setup
├── 01_run_tests.py             # Entry: Test
├── 02_run_analysis.py          # Entry: Analysis (discovers projects/{name}/scripts/)
├── 03_render_pdf.py            # Entry: PDF rendering
├── 04_validate_output.py       # Entry: Validation
├── 05_copy_outputs.py          # Entry: Copy outputs
├── 06_llm_review.py            # Entry: LLM review (optional)
├── execute_pipeline.py          # Entry: Single-project pipeline
├── execute_multi_project.py     # Entry: Multi-project pipeline
├── bash_utils.sh               # Shared utilities
├── AGENTS.md                   # This file
└── README.md                   # Quick reference

projects/{name}/scripts/
├── analysis_pipeline.py        # Project-specific analysis
├── example_figure.py           # Project-specific figures
├── AGENTS.md                   # Project script docs
└── README.md                   # Project quick reference
```

## Deployment

### Using with Template

```bash
cd /path/to/template
python3 scripts/execute_pipeline.py --project project --core-only
```

### Using with Different Project

1. Create new `projects/{name}/` structure
2. Add your code to `projects/{name}/src/`
3. Add your scripts to `projects/{name}/scripts/`
4. Run root entry points - they auto-discover your code

Root entry points work with **ANY** project that follows this structure.

## See Also

- [`README.md`](README.md) - Quick reference
- [`projects/project/scripts/AGENTS.md`](../projects/project/scripts/AGENTS.md) - Project scripts
- [`../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Pattern explanation
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation

## Testing and Logging Standards

### Testing Approach

Root scripts (`run.sh`, `scripts/bash_utils.sh`) are tested using Python subprocess calls in `tests/integration/`:

**Test Infrastructure:**
- **`test_run_sh.py`** - Tests `run.sh` command-line interface, argument parsing, project discovery
- **`test_bash_utils.sh`** - Tests individual bash utility functions using bash test framework
- **`test_logging.py`** - Tests logging functions and structured output

**Coverage Requirements:**
- **100% coverage** for `bash_utils.sh` utility functions
- **90%+ coverage** for core `run.sh` orchestration functions
- **80%+ coverage** for helper functions (menu display, etc.)

**Test Categories:**
- ✅ **Unit Tests** - Individual function testing
- ✅ **Integration Tests** - Full workflow testing
- ✅ **Error Path Tests** - Edge cases and failure modes

**Testing Philosophy:**
- Use real subprocess calls (no mocks for bash functions)
- Test command-line interfaces as users would use them
- Verify error handling and graceful degradation
- Ensure compatibility across different environments

### Logging Standards

**Structured Logging Functions:**
```bash
# Context-aware logging with timestamps
log_with_context "INFO" "message" "context"

# Error logging with troubleshooting
log_pipeline_error "stage_name" "error_msg" "exit_code" "step1" "step2"

# Resource usage tracking
log_resource_usage "stage_name" "duration" "additional_metrics"
```

**Error Handling Patterns:**
```bash
# Before: Manual error logging
log_error "Pipeline failed at Stage X"
log_info "  Troubleshooting:"
log_info "    - Check this"
log_info "    - Check that"

# After: Structured error logging
log_pipeline_error "Stage X" "failure reason" "$exit_code" \
    "Check this" \
    "Check that"
```

**Progress Tracking:**
- `log_stage_progress` - Enhanced stage logging with ETA and resource monitoring
- `STAGE_RESULTS[]` and `STAGE_DURATIONS[]` - Track pipeline execution metrics
- Resource usage logging for performance monitoring

**Log File Format:**
- ANSI color codes stripped for log files
- Consistent timestamp and context formatting
- Structured output for programmatic parsing

### Error Context and Troubleshooting

**Standardized Error Messages:**
- All pipeline errors include exit codes and troubleshooting steps
- Function names and line numbers included in error context
- Actionable guidance provided for common failure scenarios

**Graceful Degradation:**
- Optional stages (LLM review) fail gracefully without stopping pipeline
- Clear messaging when features are unavailable
- Fallback behavior documented and tested

## Key Takeaway

**Root scripts are generic entry points:**
- ✅ Work with ANY project
- ✅ Discover `project/scripts/`
- ✅ Coordinate build stages
- ❌ Never implement analysis
- ❌ Never duplicate logic

**Project scripts are specific to each research:**
- ✅ Implement domain-specific logic
- ✅ Import from `projects/{name}/src/`
- ✅ Use infrastructure tools
- ❌ Never duplicate root orchestration
