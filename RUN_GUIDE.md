# Pipeline Orchestration Guide

## Overview

The Research Project Template provides **two main entry points** for pipeline operations:

1. **`run.sh`** - Main entry point for manuscript pipeline operations (9 stages displayed as [1/9] to [9/9])
2. **`python3 scripts/execute_pipeline.py --core-only`** - Core 6-stage pipeline without LLM features

## 🏗️ Thin Orchestration Architecture

The Research Project Template follows a **thin orchestrator pattern** where all business logic resides in `infrastructure/` and `projects/{name}/src/` modules, while entry points and scripts act as lightweight coordinators.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                            │
│  run.sh → execute_pipeline.py → PipelineExecutor            │
└─────────────────────┬───────────────────────────────────────┘
                      │ delegates to
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Orchestration Layer                         │
│  scripts/00-07_*.py → infrastructure/ modules               │
│  projects/{name}/scripts/*.py → projects/{name}/src/        │
└─────────────────────┬───────────────────────────────────────┘
                      │ implements
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic                             │
│  infrastructure/ (reusable) + projects/{name}/src/ (custom) │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles

**Layer 1: Entry Points (Thin Orchestrators)**
- **`run.sh`**: Bash menu system that delegates to Python orchestrators
- **`execute_pipeline.py`**: Python pipeline coordinator using `PipelineExecutor`
- **`execute_multi_project.py`**: Multi-project orchestration using `MultiProjectOrchestrator`
- **Purpose**: User interface and high-level coordination only

**Layer 2: Stage Scripts (Thin Orchestrators)**
- **`scripts/00-07_*.py`**: Import from `infrastructure/` for business logic
- **`projects/{name}/scripts/*.py`**: Import from `projects/{name}/src/` for business logic
- **Purpose**: Stage-specific coordination and I/O handling

**Layer 3: Business Logic (Actual Implementation)**
- **`infrastructure/`**: Generic, reusable algorithms and utilities
- **`projects/{name}/src/`**: Project-specific scientific code and analysis
- **Purpose**: All computational logic and algorithms

### Orchestration Flow

```mermaid
graph TD
    A[User] --> B[run.sh]
    B --> C[execute_pipeline.py]
    C --> D[PipelineExecutor]
    D --> E[scripts/00_setup_environment.py]
    D --> F[scripts/01_run_tests.py]
    D --> G[scripts/02_run_analysis.py]
    D --> H[scripts/03_render_pdf.py]

    E --> I[infrastructure.core.environment]
    F --> J[infrastructure.reporting.test_reporter]
    G --> K[infrastructure.core.script_discovery]
    H --> L[infrastructure.rendering.RenderManager]

    K --> M[projects/{name}/scripts/*.py]
    M --> N[projects/{name}/src/]
```

### Benefits

✅ **Separation of Concerns**: Clear boundaries between orchestration and computation
✅ **Reusability**: Infrastructure modules work across all projects
✅ **Testability**: Business logic isolated and thoroughly tested
✅ **Maintainability**: Changes to algorithms don't affect orchestration
✅ **Extensibility**: New projects inherit complete infrastructure

### Examples

**✅ CORRECT: Thin Orchestrator Pattern**
```python
# scripts/03_render_pdf.py (orchestrator)
from infrastructure.rendering import RenderManager

def run_render_pipeline():
    renderer = RenderManager()  # Import business logic
    pdf = renderer.render_pdf("manuscript.tex")  # Delegate computation
    return validate_output(pdf)  # Orchestrate validation
```

**❌ INCORRECT: Violates Architecture**
```python
# scripts/03_render_pdf.py (WRONG - implements logic)
def render_pdf_to_tex(content):
    # Business logic in orchestrator - WRONG!
    lines = content.split('\n')
    tex_lines = []
    for line in lines:
        if line.startswith('# '):
            tex_lines.append(f'\\section{{{line[2:]}}}')
        # ... complex rendering logic ...
    return '\n'.join(tex_lines)
```

## 🔀 Multi-Project Support

The template now supports **multiple research projects** in a single repository. You can:

- **Run individual projects**: `./run.sh --project <name> --pipeline`
- **Run all projects sequentially**: `./run.sh --all-projects --pipeline`
- **Interactive project selection**: `./run.sh` (shows menu of available projects)

### Available Projects

The template includes three example projects:

- **`project`** - Full-featured research template (default, backward compatible)
- **`prose_project`** - Manuscript-focused with equations and prose
- **`code_project`** - Code-focused with analysis pipeline and figures

### Multi-Project Commands

```bash
# Interactive project selection
./run.sh

# Run specific project
./run.sh --project code_project --pipeline

# Run all projects sequentially
./run.sh --all-projects --pipeline

# Alternative orchestrator (all projects)
python3 scripts/execute_multi_project.py
```

## Entry Point 1: Manuscript Operations (`run.sh`)

`run.sh` provides an interactive menu for all manuscript pipeline operations:

```bash
./run.sh
```

### Manuscript Menu (Options 0-8)

```
============================================================
  Manuscript Pipeline - Main Menu
============================================================

Core Pipeline Scripts (aligned with script numbering):
  0. Setup Environment (00_setup_environment.py)
  1. Run Tests (01_run_tests.py - infrastructure + project)
  2. Run Analysis (02_run_analysis.py)
  3. Render PDF (03_render_pdf.py)
  4. Validate Output (04_validate_output.py)
  5. LLM Review (requires Ollama) (06_llm_review.py --reviews-only)
  6. LLM Translations (requires Ollama) (06_llm_review.py --translations-only)

Orchestration:
  7. Run Core Pipeline (stages 0-7: no LLM)
  8. Run Full Pipeline (9 stages: [1/9] to [9/9])
  9. Run Full Pipeline (skip infrastructure tests)
============================================================
```

### Manuscript Menu Options

#### Option 0: Setup Environment
Verifies the environment is ready for the pipeline.
- Checks Python version (requires >=3.10)
- Verifies dependencies are installed
- Confirms build tools (pandoc, xelatex) are available
- Validates directory structure
- Sets up environment variables

#### Option 1: Run Tests
Executes the test suite with coverage validation.
- Runs infrastructure tests (`tests/infrastructure/`) with 60%+ coverage threshold
- Runs project tests (`project/tests/`) with 90%+ coverage threshold
- Generates HTML coverage reports for both suites
- Generates structured test reports (JSON, Markdown)

**Coverage Reports**: `htmlcov/index.html`

#### Option 2: Run Analysis
Executes project analysis scripts with progress tracking.
- Discovers scripts in `project/scripts/`
- Executes each script in order with progress tracking
- Collects outputs to `project/output/`

#### Option 3: Render PDF
Generates manuscript PDFs with progress tracking.
- Processes `project/manuscript/` markdown files
- Converts to LaTeX via pandoc
- Compiles to PDF via xelatex
- Also runs analysis scripts first (option 2)

**Output**: `project/output/pdf/`

#### Option 4: Validate Output
Validates build quality with reporting.
- Checks generated PDFs for issues
- Validates markdown references
- Checks figure integrity
- Generates validation reports (JSON, Markdown)

#### Option 5: LLM Review
Generates AI-powered manuscript reviews using local Ollama LLM.
- Checks Ollama availability and selects best model
- Extracts full text from combined PDF manuscript
- Generates executive summary, quality review, methodology review, and improvement suggestions
- Saves all reviews to `project/output/llm/`

**Requires**: Running Ollama server with at least one model installed. Skips gracefully if unavailable.

#### Option 6: LLM Translations
Generates multi-language technical abstract translations.
- Translates abstract to configured languages (see `project/manuscript/config.yaml`)
- Uses local Ollama LLM for translation
- Saves translations to `project/output/llm/`

**Requires**: Running Ollama server and translation configuration in `config.yaml`.

#### Option 7: Run Core Pipeline
Executes the core pipeline (stages 0-6) without LLM features.
- Runs all core stages: Setup → Tests → Analysis → PDF → Validate
- Stops on first failure with clear error messages
- Suitable for CI/CD environments

#### Option 8: Run Full Pipeline
Executes the complete 9-stage build pipeline (displayed as [1/9] to [9/9]):
- Includes all core stages plus LLM review and translations
- Comprehensive manuscript generation with AI assistance
- Automatic checkpointing and resume capability

**Note**: The pipeline stages are displayed as [1/9] to [9/9] in progress logs. Clean Output Directories is stage 1.

#### Option 9: Run Full Pipeline (skip infrastructure tests)
Executes the full pipeline but skips infrastructure tests.
- Useful for multi-project execution where infrastructure tests may have already passed
- Runs project tests only to save time in development workflows
Generates AI-powered manuscript reviews using local Ollama LLM.
- Checks Ollama availability and selects best model
- Extracts full text from combined PDF manuscript
- Generates executive summary, quality review, methodology review, and improvement suggestions
- Saves all reviews to `project/output/llm/`

**Requires**: Running Ollama server with at least one model installed. Skips gracefully if unavailable.

#### Option 7: LLM Translations
Generates multi-language technical abstract translations.
- Translates abstract to configured languages (see `project/manuscript/config.yaml`)
- Uses local Ollama LLM for translation
- Saves translations to `project/output/llm/`

**Requires**: Running Ollama server and translation configuration in `config.yaml`.

#### Option 8: Run Full Pipeline
Executes the 9-stage build pipeline (displayed as [1/9] to [9/9]):

| Stage | Name | Purpose |
|-------|------|---------|
| 1 | Clean Output Directories | Prepare fresh output directories |
| 2 | Environment Setup | Verify Python, dependencies, build tools |
| 3 | Infrastructure Tests | Test generic modules (60%+ coverage, may be skipped) |
| 4 | Project Tests | Test project code (90%+ coverage) |
| 5 | Project Analysis | Run analysis scripts, generate figures |
| 6 | PDF Rendering | Generate manuscript PDFs |
| 7 | Output Validation | Validate all outputs |
| 8 | LLM Scientific Review | Generate AI reviews (optional, requires Ollama) |
| 9 | LLM Translations | Multi-language technical abstract generation (optional, requires Ollama) |
| 10 | Copy Outputs | Copy deliverables to top-level output/ |

**Note**: The pipeline stages are displayed as [1/9] to [9/9] in progress logs. Clean Output Directories is stage 1.

**Generated Outputs**:
- Coverage reports: `htmlcov/`
- PDF files: `project/output/pdf/`
- Figures: `project/output/figures/`
- Data files: `project/output/data/`
- LLM reviews: `project/output/llm/` (if Ollama available)
- Pipeline reports: `project/output/reports/` (JSON, HTML, Markdown)

**Checkpoint/Resume**: Supports `--resume` flag to resume from last checkpoint

### Manuscript Non-Interactive Mode

```bash
# Core Build Operations
./run.sh --pipeline          # Run pipeline (9 stages displayed as [1/9] to [9/9], includes LLM)
./run.sh --pipeline --resume # Resume from last checkpoint
./run.sh --infra-tests        # Run infrastructure tests only
./run.sh --project-tests      # Run project tests only
./run.sh --render-pdf         # Render PDF manuscript only

# LLM Operations (requires Ollama)
./run.sh --reviews            # LLM manuscript review only (English)
./run.sh --translations       # LLM translations only

# Show help
./run.sh --help
```

## Entry Point 2: Python Orchestrator (`scripts/execute_pipeline.py`)

For programmatic access or CI/CD integration, use the Python orchestrator:

```bash
# Core pipeline (6 stages) - Python orchestrator
python3 scripts/execute_pipeline.py --core-only
```

**Features**:
- 6-stage core pipeline (stages 00-05)
- No LLM dependencies required
- Suitable for automated environments
- Zero-padded stage numbering (Python convention)
- Checkpoint/resume support: `python3 scripts/execute_pipeline.py --core-only --resume`

### Core Pipeline Stages + Executive Reporting

| Stage | Script | Purpose |
|-------|--------|---------|
| 00 | `00_setup_environment.py` | Environment setup & validation |
| 01 | `01_run_tests.py` | Run test suite (infrastructure + project) |
| 02 | `02_run_analysis.py` | Discover & run `project/scripts/` |
| 03 | `03_render_pdf.py` | PDF rendering orchestration |
| 04 | `04_validate_output.py` | Output validation & reporting |
| 05 | `05_copy_outputs.py` | Copy final deliverables to `output/` |
| 07 | `07_generate_executive_report.py` | Executive summaries & dashboards (multi-project only) |

## Entry Point Comparison

| Entry Point | Pipeline Stages | LLM Support | Use Case |
|-------------|----------------|--------------|----------|
| `./run.sh` | Main entry point | Optional | Interactive menu or manuscript pipeline with LLM |
| `./run.sh --pipeline` | 9 stages ([1/9] to [9/9]) | Optional | Manuscript pipeline with LLM |
| `python3 scripts/execute_pipeline.py --core-only` | 6 stages (00-05) | None | Core pipeline, CI/CD automation |

## Usage Examples

### Interactive Mode

```bash
# Main dispatcher
./run.sh

# Direct access to manuscript operations
./run.sh

```

### Non-Interactive Mode

```bash
# Run manuscript pipeline
./run.sh --pipeline

# Resume manuscript pipeline from checkpoint
./run.sh --pipeline --resume


# Run core pipeline (Python)
python3 scripts/execute_pipeline.py --core-only
```

### Individual Stage Execution

Individual stages can also be run directly via Python:

```bash
python3 scripts/00_setup_environment.py  # Setup environment
python3 scripts/01_run_tests.py          # Run tests only
python3 scripts/01_run_tests.py --verbose  # Run tests with verbose output
python3 scripts/02_run_analysis.py       # Run project scripts
python3 scripts/03_render_pdf.py         # Render PDFs only
python3 scripts/04_validate_output.py    # Validate outputs only
python3 scripts/05_copy_outputs.py       # Copy final deliverables
python3 scripts/06_llm_review.py         # LLM manuscript review
python3 scripts/06_llm_review.py --reviews-only     # Reviews only
python3 scripts/06_llm_review.py --translations-only # Translations only
```

## Exit Codes

- **0**: Operation succeeded
- **1**: Operation failed - review errors and fix issues
- **2**: Operation skipped (e.g., Ollama not available for LLM review)

## Environment Variables

The scripts automatically set:
- `PROJECT_ROOT`: Repository root directory
- `PYTHONPATH`: Includes root, infrastructure, and project/src

You can override by setting before running:
```bash
export LOG_LEVEL=0  # Enable debug logging
./run.sh --pipeline
```

### LLM Review Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MAX_INPUT_LENGTH` | `500000` | Max chars to send to LLM. Set to `0` for unlimited. |
| `LLM_REVIEW_TIMEOUT` | `300` | Timeout per review in seconds |
| `LLM_LONG_MAX_TOKENS` | `4096` | Maximum tokens per review response |

## Error Handling

The scripts use strict error handling:
- Stops immediately on first failure
- Provides clear error messages
- Shows which stage/operation failed
- Returns to menu after each operation (interactive mode)

**Example error output**:
```
✗ Infrastructure tests failed

  Operation completed in 45s

Press Enter to return to menu...
```

## Troubleshooting

### "Permission denied: ./run.sh"

Make the script executable:
```bash
chmod +x run.sh
```

### Tests fail with import errors

Verify `conftest.py` is in the repository root and contains proper path setup.

### Coverage threshold not met

Check `pyproject.toml` `[tool.coverage.report]` for coverage thresholds. Increase test coverage in `tests/` and `project/tests/`.

### PDF rendering fails

Ensure pandoc and xelatex are installed:
```bash
# macOS
brew install pandoc
brew install --cask mactex

# Ubuntu/Debian
sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended
```

### LLM review fails or skips

Ensure Ollama is running:
```bash
# Start Ollama server
ollama serve

# Install a model (if needed)
ollama pull llama3-gradient
```

## See Also

- [`scripts/README.md`](scripts/README.md) - Stage orchestrators documentation
- [`scripts/AGENTS.md`](scripts/AGENTS.md) - Complete scripts documentation
- [`AGENTS.md`](AGENTS.md) - Complete system documentation
- [`docs/core/WORKFLOW.md`](docs/core/WORKFLOW.md) - Development workflow
- [`docs/operational/BUILD_SYSTEM.md`](docs/operational/BUILD_SYSTEM.md) - Detailed build system reference
