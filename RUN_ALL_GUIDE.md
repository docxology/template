# run_all.sh - Complete Pipeline Orchestration Guide

## Overview

`run_all.sh` is the master orchestration script that runs the complete research project pipeline in a single command:

```bash
./run_all.sh
```

This executes all stages sequentially: environment setup, infrastructure tests, project tests, analysis, PDF rendering, output validation, and output copying.

## Pipeline Stages

### Stage 0: Clean Output Directories
**Purpose**: Prepare for fresh pipeline execution

- Removes all contents from `project/output/` and `output/` directories
- Recreates essential subdirectory structure (`pdf/`, `figures/`, `data/`, `reports/`, `simulations/`, `slides/`, `web/`, `llm/`)
- Ensures each pipeline run starts with clean state
- Prevents stale outputs from previous runs

**Exit**: Always succeeds (creates directories if they don't exist)

### Stage 1: Setup Environment
**Purpose**: Verify environment is ready for execution

- Checks Python version (3.8+)
- Verifies dependencies (numpy, matplotlib, pytest, scipy)
- Confirms build tools (pandoc, xelatex)
- Validates directory structure
- Sets environment variables

**Exit**: Fails if any check fails

### Stage 2: Infrastructure Tests
**Purpose**: Test generic infrastructure modules with coverage validation

- Runs all infrastructure module tests
- Validates coverage meets 70%+ threshold
- Covers: core, build, documentation, literature, llm, publishing, rendering, scientific, validation
- Generates HTML coverage report

**Coverage Report**: `htmlcov/index.html`

### Stage 3: Project Tests
**Purpose**: Test project-specific scientific code with coverage validation

- Runs project-specific tests from `project/tests/`
- Ignores integration tests (non-critical)
- Validates coverage meets 70%+ threshold for `project/src/`
- Generates HTML coverage report

**Coverage Report**: `htmlcov/index.html`

### Stage 4: Project Analysis
**Purpose**: Generate figures and analysis outputs

- Discovers all scripts in `project/scripts/`
- Executes each script in order
- Generates figures in `project/output/figures/`
- Generates data files in `project/output/data/`

**Output**: `project/output/figures/`, `project/output/data/`

### Stage 5: PDF Rendering
**Purpose**: Generate professional PDFs from markdown sources

- Processes markdown in `project/manuscript/`
- Converts to LaTeX via pandoc
- Compiles to PDF via xelatex
- Generates individual section PDFs
- Generates combined manuscript PDF

**Output**: `project/output/pdf/`

### Stage 6: Output Validation
**Purpose**: Validate all generated outputs

- Checks PDF files for validity
- Validates markdown formatting
- Verifies output directory structure
- Generates validation report

**Output**: Validation report in console

### Stage 7: Copy Outputs
**Purpose**: Copy final deliverables to top-level output directory

- Cleans top-level `output/` directory
- Copies combined PDF: `project_combined.pdf`
- Copies presentation slides: `slides/*.pdf`
- Copies web outputs: `web/*.html`
- Validates all files copied successfully

**Output**: `output/`, `output/slides/`, `output/web/`

### Stage 8: LLM Manuscript Review
**Purpose**: Generate AI-powered manuscript analysis (optional, requires Ollama)

- Checks Ollama availability and selects best model
- Extracts full text from combined manuscript PDF
- Generates executive summary of key findings
- Generates writing quality and methodology review
- Generates improvement suggestions with actionable recommendations
- Validates review quality and retries if needed
- Saves all reviews to `output/llm/` with detailed metrics

**Output**: `output/llm/` directory with review files and metadata
**Optional**: Skips gracefully if Ollama not running

## Usage

### Basic Usage
```bash
# From repository root
./run_all.sh

# Or with explicit shell
bash run_all.sh
```

### Output
The script provides:
- **Progress indicators**: Shows current stage and progress
- **Timing information**: Reports time for each stage
- **Error messages**: Clear error messages on failure
- **Final summary**: Report of all stages with pass/fail status

### Example Output
```
════════════════════════════════════════════════════════════════
  COMPLETE RESEARCH PROJECT PIPELINE
════════════════════════════════════════════════════════════════
  Repository: /Users/4d/Documents/GitHub/template
  Python: Python 3.11.0

[1/8] Setup Environment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Environment setup complete

[2/8] Infrastructure Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Running infrastructure module tests...
✓ Infrastructure tests passed

... (additional stages) ...

════════════════════════════════════════════════════════════════
  PIPELINE SUMMARY
════════════════════════════════════════════════════════════════
✓ All stages completed successfully!

Stage Results:
  ✓ Stage 0: Clean Output Directories (1s)
  ✓ Stage 1: Setup Environment (12s)
  ✓ Stage 2: Infrastructure Tests (45s)
  ✓ Stage 3: Project Tests (38s)
  ✓ Stage 4: Project Analysis (5s)
  ✓ Stage 5: PDF Rendering (120s)
  ✓ Stage 6: Output Validation (8s)
  ✓ Stage 7: Copy Outputs (2s)
  ✓ Stage 8: LLM Manuscript Review (15s)

Total Execution Time: 3m 45s

Generated Outputs:
  • Coverage reports: htmlcov/
  • PDF files: project/output/pdf/
  • Figures: project/output/figures/
  • Data files: project/output/data/
  • LLM reviews: output/llm/ (if Ollama available)
  • Final deliverables: output/

✓ Pipeline complete - ready for deployment
```

## Exit Codes

- **0**: All stages succeeded - ready for deployment
- **1**: One or more stages failed - review errors and fix issues

## Environment Variables

The script automatically sets:
- `PROJECT_ROOT`: Repository root directory
- `PYTHONPATH`: Includes root, infrastructure, and project/src

You can override by setting before running:
```bash
export LOG_LEVEL=0  # Enable debug logging
./run_all.sh
```

## Error Handling

The script uses strict error handling:
- Stops immediately on first failure
- Provides clear error messages
- Shows which stage failed
- Lists all successful stages

**Example error output**:
```
✗ Pipeline failed at Stage 3 (Project Tests)

Review errors above and fix issues before retrying
```

**Example with Stage 8 failure**:
```
✗ Pipeline failed at Stage 8 (LLM Manuscript Review)

Ollama is not running. Please start Ollama with 'ollama serve' and retry,
or remove Stage 8 from the pipeline if LLM reviews are not needed.
```

## Comparison: Shell vs Python

Both orchestrators run the complete pipeline with equivalent functionality:

### Shell Script (`run_all.sh`)
- ✅ Recommended for interactive use - just type `./run_all.sh`
- ✅ Better progress reporting with colors
- ✅ Automatic environment configuration
- ✅ 8 stages + 1 clean stage with visual progress indicators
- ✅ Native bash execution (no Python startup overhead)

### Python Orchestrator (`python3 scripts/run_all.py`)
- ✅ Programmatic access for CI/CD integration
- ✅ Better for automated pipelines
- ✅ Consistent Python logging across all stages
- ✅ 6 stages + 1 clean stage (tests combined into single stage)
- ✅ Easier integration with Python tooling

### Stage Mapping

| Shell (`run_all.sh`) | Python (`run_all.py`) |
|----------------------|----------------------|
| Stage 0: Clean Output Directories | Stage 0: Clean Output Directories |
| Stage 1: Setup Environment | Stage 1: Setup Environment |
| Stage 2: Infrastructure Tests | Stage 2: Run Tests (both) |
| Stage 3: Project Tests | *(combined above)* |
| Stage 4: Project Analysis | Stage 3: Analysis |
| Stage 5: PDF Rendering | Stage 4: PDF Rendering |
| Stage 6: Output Validation | Stage 5: Validation |
| Stage 7: Copy Outputs | Stage 6: Copy Outputs |
| Stage 8: LLM Manuscript Review | *(not implemented)* |

Both run identical tests and produce identical outputs. Choose based on preference.

## Configuration Files

The pipeline uses the following configuration files:

- `pyproject.toml` - All Python configuration (pytest, coverage, dependencies)
  - `[tool.pytest.ini_options]` - Test discovery and pytest options
  - `[tool.coverage.run]` - Coverage collection settings
  - `[tool.coverage.report]` - Coverage report and thresholds
- `conftest.py` - Test path configuration and fixtures

These are automatically managed - no manual configuration needed.

## Troubleshooting

### "Permission denied: ./run_all.sh"
Make the script executable:
```bash
chmod +x run_all.sh
```

### Tests fail with import errors
Verify `conftest.py` is in the repository root and contains proper path setup.

### Coverage threshold not met
Check `pyproject.toml` `[tool.coverage.report]` for `fail_under = 70`. Increase test coverage in `tests/` and `project/tests/`.

### PDF rendering fails
Ensure pandoc and xelatex are installed:
```bash
# macOS
brew install pandoc
brew install --cask mactex

# Ubuntu/Debian
sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended
```

## See Also

- [`scripts/README.md`](scripts/README.md) - Stage orchestrators documentation
- [`AGENTS.md`](AGENTS.md) - Complete system documentation
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) - Development workflow
- [`docs/BUILD_SYSTEM.md`](docs/BUILD_SYSTEM.md) - Detailed build system reference

