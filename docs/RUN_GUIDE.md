# Pipeline Orchestration Guide

## Overview

The Research Project Template provides **two main entry points** for pipeline operations:

1. **`run.sh`** - Main entry point for manuscript pipeline operations (interactive menu and flags)
2. **`uv run python scripts/execute_pipeline.py --project {name} --core-only`** - Core pipeline via [`infrastructure/core/pipeline/pipeline.yaml`](../infrastructure/core/pipeline/pipeline.yaml): **8** DAG stages (clean → copy) with **`llm`-tagged stages removed**; the full default graph has **10** stages including LLM review and translations

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
│  scripts/00_*.py … scripts/07_*.py → infrastructure/ modules  │
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

- **`scripts/00_*.py`–`scripts/07_*.py`**: Import from `infrastructure/` for business logic (numbered stage entry points; not all run in a single `--core-only` pass)
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

    E --> I[infrastructure.core.runtime.environment]
    F --> J[infrastructure.reporting.test_reporter]
    G --> K[infrastructure.core.runtime.script_discovery]
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

Projects are discovered dynamically from `projects/` (see `infrastructure.project.discovery.discover_projects()`). **Authoritative names:** [_generated/active_projects.md](_generated/active_projects.md) (see [_generated/README.md](_generated/README.md) for policy and regeneration). **Examples in this guide** use **`code_project`** as the stable control-positive layout under `projects/`.

Archived and in-progress work lives under `projects_archive/` and `projects_in_progress/` and is not executed by `./run.sh` until moved into `projects/`.

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
⚙️  INDIVIDUAL STAGES
    0  Setup Environment          00_setup_environment.py
    1  Run Tests                  01_run_tests.py
    2  Run Analysis               02_run_analysis.py
    3  Render PDF                 03_render_pdf.py
    4  Validate Output            04_validate_output.py
    5  Copy Outputs               05_copy_outputs.py
    6  LLM Review                 06_llm_review.py
    7  LLM Translations           06_llm_review.py

🚀 ORCHESTRATION
    8  Core Pipeline              [+infra] [-LLM] Core stages
    9  Full Pipeline              [+infra] [+LLM] All 10 stages
    f  Full Pipeline (fast)       [-infra] [+LLM] Skip infra tests

📚 MULTI-PROJECT
    a  All projects full          [+infra] [+LLM] [+report]
    b  All projects full (fast)   [-infra] [+LLM] [+report]
    c  All projects core          [+infra] [-LLM] [+report]
    d  All projects core (fast)   [-infra] [-LLM] [+report]

📁 PROJECT
    p  Change Active Project      i  Show Project Info
    q  Quit
```

Progress logs use a **pre-step** `[0/9] Clean Output Directories`, then **`[1/9]` through `[9/9]`** for the nine tracked steps in `run.sh` (see `STAGE_NAMES` in [`run.sh`](../run.sh)). The **Python executor** follows [`pipeline.yaml`](../infrastructure/core/pipeline/pipeline.yaml) (10 named stages, including clean and both LLM steps).

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
- Runs project tests (`projects/{name}/tests/`) with 90%+ coverage threshold
- Generates HTML coverage reports for both suites
- Generates structured test reports (JSON, Markdown)

**Coverage Reports**: `htmlcov/index.html`

#### Option 2: Run Analysis

Executes project analysis scripts with progress tracking.

- Discovers scripts in `projects/{name}/scripts/`
- Executes each script in order with progress tracking
- Collects outputs to `projects/{name}/output/`

#### Option 3: Render PDF

Generates manuscript PDFs with progress tracking.

- Processes `projects/{name}/manuscript/` markdown files
- Converts to LaTeX via pandoc
- Compiles to PDF via xelatex
- Also runs analysis scripts first (option 2)

**Output**: `projects/{name}/output/pdf/`

#### Option 4: Validate Output

Validates build quality with reporting.

- Checks generated PDFs for issues
- Validates markdown references
- Checks figure integrity
- Generates validation reports (JSON, Markdown)

#### Option 5: Copy Outputs

Copies final deliverables into the repo-level `output/{name}/` tree (and related publishing outputs per project settings).

#### Option 6: LLM Review

Generates AI-powered manuscript reviews using local Ollama LLM.

- Checks Ollama availability and selects best model
- Extracts full text from combined PDF manuscript
- Generates executive summary, quality review, methodology review, and improvement suggestions
- Saves all reviews to `projects/{name}/output/llm/`

**Requires**: Running Ollama server with at least one model installed. Skips gracefully if unavailable.

#### Option 7: LLM Translations

Generates multi-language technical abstract translations.

- Translates abstract to configured languages (see `projects/{name}/manuscript/config.yaml`)
- Uses local Ollama LLM for translation
- Saves translations to `projects/{name}/output/llm/`

**Requires**: Running Ollama server and translation configuration in `config.yaml`.

#### Menu `8`: Core Pipeline

Runs `execute_pipeline.py` with **`--core-only`** (default [`pipeline.yaml`](../infrastructure/core/pipeline/pipeline.yaml): **8** stages, no LLM-tagged steps).

- Stops on first failure with clear error messages
- Suitable for CI/CD environments

#### Menu `9`: Full Pipeline

Runs the **full** default DAG (**10** stages in `pipeline.yaml`, including clean, both LLM stages, and copy).

- LLM stages are optional at runtime (exit code 2 skip) if Ollama is unavailable
- Bash progress lines use `[0/9]` for clean, then `[1/9]`–`[9/9]` for the nine entries in `STAGE_NAMES` in [`run.sh`](../run.sh) (see menu block above)

#### Menu `f`: Full Pipeline (fast)

Same as full pipeline but **skips infrastructure tests** (`--skip-infra` / fast path in `run.sh`).

### Manuscript Non-Interactive Mode

```bash
# Core Build Operations
./run.sh --pipeline          # Full DAG (10 stages in pipeline.yaml; bash shows [0/9] clean + [1/9]–[9/9] tracked steps)
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
# Core pipeline (8 DAG stages in default pipeline.yaml — excludes LLM-tagged stages)
uv run python scripts/execute_pipeline.py --project {name} --core-only
```

**Features**:

- **Eight** DAG stages by default: clean → setup → infrastructure tests → project tests → analysis → PDF → validation → copy. Omit infrastructure tests with `--skip-infra` (**seven** stages).
- No LLM-tagged stages (`06_llm_review.py` / `07_generate_executive_report.py` are not part of `--core-only`; `07` is for multi-project executive reporting)
- No LLM dependencies required for `--core-only`
- Suitable for automated environments
- Checkpoint/resume support: `uv run python scripts/execute_pipeline.py --project {name} --core-only --resume`

### Core Pipeline Stages + Executive Reporting

| Stage | Script | Purpose |
|-------|--------|---------|
| 00 | `00_setup_environment.py` | Environment setup & validation |
| 01 | `01_run_tests.py` | Run test suite (infrastructure + project) |
| 02 | `02_run_analysis.py` | Discover & run `projects/{name}/scripts/` |
| 03 | `03_render_pdf.py` | PDF rendering orchestration |
| 04 | `04_validate_output.py` | Output validation & reporting |
| 05 | `05_copy_outputs.py` | Copy final deliverables to `output/` |
| 06 | `06_llm_review.py` | LLM manuscript review & translations (optional, requires Ollama) |
| 07 | `07_generate_executive_report.py` | Executive summaries & dashboards (multi-project only) |

`--core-only` runs the executor stages through copy outputs and does **not** run `06` or `07`; those are optional or multi-project entry points.

## Entry Point Comparison

| Entry Point | Pipeline Stages | LLM Support | Use Case |
|-------------|----------------|--------------|----------|
| `./run.sh` | Main entry point | Optional | Interactive menu or manuscript pipeline with LLM |
| `./run.sh --pipeline` | Full DAG (**10** stages in default `pipeline.yaml`) | Optional | Manuscript pipeline with LLM stages present in the graph |
| `uv run python scripts/execute_pipeline.py --project {name} --core-only` | Core DAG (**8** stages; LLM stages omitted) | None | Core pipeline, CI/CD automation |

## Usage Examples

### Interactive Mode

```bash
./run.sh   # main dispatcher (project menu + pipeline options)
```

### Non-Interactive Mode

```bash
# Run manuscript pipeline
./run.sh --pipeline

# Resume manuscript pipeline from checkpoint
./run.sh --pipeline --resume


# Run core pipeline (Python)
uv run python scripts/execute_pipeline.py --project {name} --core-only
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
- `PYTHONPATH`: Includes root, infrastructure, and `projects/{name}/src`

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

Check `pyproject.toml` `[tool.coverage.report]` for coverage thresholds. Increase test coverage in `tests/` and `projects/{name}/tests/`.

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

- [`scripts/README.md`](../scripts/README.md) — Stage orchestrators
- [`scripts/AGENTS.md`](../scripts/AGENTS.md) — `scripts/` technical guide
- [`AGENTS.md`](AGENTS.md) — Documentation hub (`docs/`)
- [`../AGENTS.md`](../AGENTS.md) — Repository system reference
- [`CLOUD_DEPLOY.md`](CLOUD_DEPLOY.md) — Headless / cloud server deployment
- [`core/workflow.md`](core/workflow.md) — Development workflow

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
