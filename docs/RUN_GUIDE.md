# Pipeline Orchestration Guide

## Overview

The Research Project Template provides **two main entry points** for pipeline operations:

1. **`run.sh`** - Main entry point for manuscript pipeline operations (9 stages displayed as [1/9] to [9/9], with an initial clean step shown as [0/9])
2. **`uv run scripts/execute_pipeline.py --core-only`** - Core 8-stage pipeline without LLM features

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
✅ **Extensibility**: New projects inherit infrastructure

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

Projects are discovered dynamically from `projects/` (see `infrastructure.project.discovery.discover_projects()`), so this guide avoids hard-coding a canonical list.

In this repository right now, examples under `projects/` include:

- **`biology_textbook`**
- **`code_project`**
- **`project`**

Archived and in-progress projects live outside `projects/` and are not executed by default.

### Multi-Project Commands

```bash
# Interactive project selection
./run.sh

# Run specific project
./run.sh --project code_project --pipeline

# Run all projects sequentially
./run.sh --all-projects --pipeline

# Alternative orchestrator (all projects)
uv run scripts/execute_multi_project.py
```

## Entry Point 1: Manuscript Operations (`run.sh`)

`run.sh` provides an interactive menu for all manuscript pipeline operations:

```bash
./run.sh
```

### Manuscript Menu

```text
============================================================
  Manuscript Pipeline - Main Menu
============================================================

⚙️  CORE STAGES
    0  Setup Environment
    1  Run Tests (infra + project)
    2  Run Analysis Scripts
    3  Render PDF
    4  Validate Output
    5  LLM Scientific Review
    6  LLM Translations

🚀 ORCHESTRATION
    7  Core Pipeline              [+infra] [-LLM] Stages [1/9]..[9/9] (no LLM stages)
    8  Full Pipeline              [+infra] [+LLM] Stages [1/9]..[9/9] + optional LLM stages
    9  Full Pipeline (fast)       [-infra] [+LLM] Skip infra tests

📚 MULTI-PROJECT
    a  All projects full          [+infra] [+LLM] [+report]
    b  All projects full (fast)   [-infra] [+LLM] [+report]
    c  All projects core          [+infra] [-LLM] [+report]
    d  All projects core (fast)   [-infra] [-LLM] [+report]

🔧 PROJECT MANAGEMENT
    p  Change Active Project      [Current: <project_name>]
    i  Show Project Info
    q  Quit
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

- Runs infrastructure tests (`tests/infra_tests/`) with 60%+ coverage threshold
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

Executes the 9-stage pipeline (displayed as [1/9] to [9/9], with an initial clean step shown as [0/9]):

- Includes all core stages plus LLM review and translations
- manuscript generation with AI assistance
- Automatic checkpointing and resume capability

**Note**: The pipeline stages are displayed as [1/9] to [9/9] in progress logs. Clean Output Directories is displayed as a pre-step ([0/9]).

#### Option 9: Run Full Pipeline (skip infrastructure tests)

Executes the full pipeline but skips infrastructure tests.

- Useful for multi-project execution where infrastructure tests may have already passed
- Runs project tests only to save time in development workflows

### Manuscript Non-Interactive Mode

```bash
# Core Build Operations
./run.sh --pipeline          # Run pipeline (9 stages displayed as [1/9] to [9/9], clean shown as [0/9], includes optional LLM stages)
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
# Core pipeline (8 stages) - Python orchestrator
uv run scripts/execute_pipeline.py --core-only
```

**Features**:

- 8-stage core pipeline (stages 00-05)
- No LLM dependencies required
- Suitable for automated environments
- Zero-padded stage numbering (Python convention)
- Checkpoint/resume support: `uv run scripts/execute_pipeline.py --core-only --resume`

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
| `./run.sh --pipeline` | 9 stages ([1/9] to [9/9]) + pre-clean ([0/9]) | Optional | Manuscript pipeline with LLM |
| `uv run scripts/execute_pipeline.py --core-only` | 8 stages (00-05) | None | Core pipeline, CI/CD automation |

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
uv run scripts/execute_pipeline.py --core-only
```

### Individual Stage Execution

Individual stages can also be run directly via Python:

```bash
uv run scripts/00_setup_environment.py  # Setup environment
uv run scripts/01_run_tests.py          # Run tests only
uv run scripts/01_run_tests.py --verbose  # Run tests with verbose output
uv run scripts/02_run_analysis.py       # Run project scripts
uv run scripts/03_render_pdf.py         # Render PDFs only
uv run scripts/04_validate_output.py    # Validate outputs only
uv run scripts/05_copy_outputs.py       # Copy final deliverables
uv run scripts/06_llm_review.py         # LLM manuscript review
uv run scripts/06_llm_review.py --reviews-only     # Reviews only
uv run scripts/06_llm_review.py --translations-only # Translations only
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

- [`scripts/README.md`](../scripts/README.md) - Stage orchestrators documentation
- [`scripts/AGENTS.md`](../scripts/AGENTS.md) - scripts documentation
- [`AGENTS.md`](AGENTS.md) - system documentation
- [`CLOUD_DEPLOY.md`](CLOUD_DEPLOY.md) - **Headless / cloud server deployment guide** ⭐
- [`core/workflow.md`](core/workflow.md) - Development workflow
- [`RUN_GUIDE.md`](RUN_GUIDE.md) - Pipeline orchestration reference (this document)

---

## Headless / Cloud Server Deployment

For a fresh headless server (Ubuntu/Debian), all dependencies including `uv` are installed
automatically when you invoke any non-interactive pipeline flag:

```bash
# 1. Install system deps (LaTeX + git + curl)
sudo apt-get update && sudo apt-get install -y \
    curl git python3 pandoc \
    texlive-xetex texlive-latex-extra texlive-fonts-recommended

# 2. Clone the repository
git clone https://github.com/docxology/template.git && cd template

# 3. Run — uv is installed automatically, .venv is synced
./run.sh --pipeline
```

The `MPLBACKEND=Agg` environment variable is required on headless servers (no display):

```bash
export MPLBACKEND=Agg
./run.sh --pipeline
```

> 📖 **Full guide:** See [`CLOUD_DEPLOY.md`](CLOUD_DEPLOY.md) for system prerequisites,
> optional dependency groups, Docker alternative, Ollama setup, and troubleshooting.
