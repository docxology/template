# run.sh - Unified Pipeline Orchestration Guide

## Overview

`run.sh` is the unified orchestration script that provides an interactive menu for all pipeline operations:

```bash
./run.sh
```

This presents a menu with options for running tests, rendering PDFs, executing the full pipeline, LLM manuscript review, and literature search operations.

**Alternative Entry Point**: For a simpler 6-stage core pipeline without LLM features, use `python3 scripts/run_all.py` instead.

## Menu Options

```
============================================================
  Research Project Template - Main Menu
============================================================

Core Pipeline Scripts (aligned with script numbering):
  0. Setup Environment (00_setup_environment.py)
  1. Run Tests (01_run_tests.py - infrastructure + project)
  2. Run Analysis (02_run_analysis.py)
  3. Render PDF (03_render_pdf.py)
  4. Validate Output (04_validate_output.py)
  5. Copy Outputs (05_copy_outputs.py)
  6. LLM Review (requires Ollama) (06_llm_review.py --reviews-only)
  7. LLM Translations (requires Ollama) (06_llm_review.py --translations-only)

Orchestration:
  8. Run Full Pipeline (10 stages: 0-9, via run.sh)

Literature Operations (via 07_literature_search.py, not part of core pipeline):
  9. Literature Search (all operations)
  10. Search only (network only)
  11. Download only (network only)
  12. Summarize (requires Ollama)
  13. Cleanup (local files only)
  14. Advanced LLM operations (requires Ollama)

  15. Exit
============================================================
```

### Option 0: Setup Environment

Verifies the environment is ready for the pipeline.

- Checks Python version (requires >=3.10)
- Verifies dependencies are installed
- Confirms build tools (pandoc, xelatex) are available
- Validates directory structure
- Sets up environment variables

**Generic**: Works for any project

### Option 1: Run Tests

Executes the complete test suite with coverage validation.

- Runs infrastructure tests (`tests/infrastructure/`) with 49%+ coverage threshold
- Runs project tests (`project/tests/`) with 70%+ coverage threshold
- Supports quiet mode (default) - shows only summary
- Supports verbose mode (`--verbose`) - shows all test names
- Generates HTML coverage reports for both suites
- Generates structured test reports (JSON, Markdown) to `project/output/reports/test_results.{json,md}`

**Coverage Reports**: `htmlcov/index.html`

**Generic**: Works for any project using pytest

### Option 2: Run Analysis

Executes project analysis scripts with enhanced progress tracking.

- Discovers scripts in `project/scripts/`
- Executes each script in order with progress tracking
- Uses EMA-based ETA for accurate time estimates
- Logs resource usage at start and end of stage
- Validates output generation
- Collects outputs to `project/output/`

**Generic**: Works for any project with analysis scripts

### Option 3: Render PDF

Generates manuscript PDFs with progress tracking.

- Processes `project/manuscript/` markdown files
- Uses progress tracking for multi-file rendering operations
- Converts to LaTeX via pandoc
- Compiles to PDF via xelatex
- Logs resource usage during rendering
- Also runs analysis scripts first (option 2)

**Output**: `project/output/pdf/`

**Generic**: Works for any markdown manuscript

### Option 4: Validate Output

Validates build quality with enhanced reporting.

- Checks generated PDFs for issues
- Validates markdown references
- Checks figure integrity
- Generates enhanced validation reports (JSON, Markdown) with actionable recommendations
- Reports include priority levels, issue categorization, and specific fixes
- Reports saved to `project/output/reports/validation_report.{json,md}`

**Generic**: Works for any project output

### Option 5: Copy Outputs

Copies final deliverables to top-level output directory.

- Cleans top-level `output/` directory
- Copies combined PDF manuscript
- Copies all presentation slides (PDF format)
- Copies all web outputs (HTML format)
- Validates all files copied successfully

**Generic**: Works for any project with rendered outputs

### Option 6: LLM Review

Generates AI-powered manuscript reviews using local Ollama LLM.

- Checks Ollama availability and selects best model
- Extracts full text from combined PDF manuscript
- Generates executive summary, quality review, methodology review, and improvement suggestions
- Generates translations (if configured) - technical abstract in multiple languages
- Uses improved progress indicators (spinner, streaming progress)
- Saves all reviews with detailed metrics to `project/output/llm/` (copied to `output/llm/` during copy stage)

**Requires**: Running Ollama server with at least one model installed. Skips gracefully if unavailable.

**Output Files**:
- `executive_summary.md` - Key findings and contributions
- `quality_review.md` - Writing clarity and style assessment
- `methodology_review.md` - Structure and methods evaluation
- `improvement_suggestions.md` - Actionable recommendations
- `translation_*.md` - Technical abstract translations (if configured)
- `combined_review.md` - All reviews with generation metrics
- `review_metadata.json` - Model, config, and detailed metrics

**Generic**: Works for any project with a combined PDF manuscript

### Option 7: Literature Search

Manages academic literature with combined operations.

- Searches arXiv and Semantic Scholar APIs
- Downloads PDFs for found papers
- Adds papers to bibliography (`literature/references.bib`)
- Generates AI summaries for downloaded papers (requires Ollama)

**Requires**: Network access. Summarization requires Ollama.

**Output**: `literature/` directory

**Generic**: Works for any project needing literature management

### Option 8: Run Full Pipeline

Executes the complete 10-stage build pipeline (stages 0-9):

| Stage | Name | Purpose |
|-------|------|---------|
| 0 | Clean Output Directories | Prepare fresh output directories |
| 1 | Setup Environment | Verify Python, dependencies, build tools |
| 2 | Infrastructure Tests | Test generic modules (49%+ coverage) |
| 3 | Project Tests | Test project code (70%+ coverage) |
| 4 | Project Analysis | Run analysis scripts, generate figures |
| 5 | PDF Rendering | Generate manuscript PDFs |
| 6 | Output Validation | Validate all outputs |
| 7 | Copy Outputs | Copy deliverables to top-level output/ |
| 8 | LLM Scientific Review | Generate AI reviews (optional) |
| 9 | LLM Translations | Multi-language technical abstract generation (optional) |

**Note**: Stage 0 (Clean) is a pre-pipeline cleanup step. The main pipeline stages (1-9) are tracked in the progress display, which shows [1/9] to [9/9] in logs.

**Generated Outputs**:
- Coverage reports: `htmlcov/`
- PDF files: `project/output/pdf/`
- Figures: `project/output/figures/`
- Data files: `project/output/data/`
- LLM reviews: `project/output/llm/` (if Ollama available)
- Pipeline reports: `project/output/reports/` (JSON, HTML, Markdown)
  - `pipeline_report.{json,html,md}` - Consolidated pipeline execution report
  - `test_results.{json,md}` - Structured test results with coverage
  - `validation_report.{json,md}` - Enhanced validation with recommendations
  - `error_summary.{json,md}` - Error aggregation with actionable fixes

**Checkpoint/Resume**: Supports `--resume` flag to resume from last checkpoint

### Option 9: Search Only

Searches for papers and adds to bibliography (network only, no Ollama required).

- Searches arXiv and Semantic Scholar APIs
- Adds papers to bibliography (`literature/references.bib`)
- Updates library index (`literature/library.json`)
- Does NOT download PDFs or generate summaries

**Requires**: Network access only

**Output**: `literature/references.bib`, `literature/library.json`

### Option 10: Download Only

Downloads PDFs for existing bibliography entries (network only, no Ollama required).

- Downloads PDFs for papers in bibliography without PDFs
- Saves PDFs to `literature/pdfs/`
- Updates library index
- Does NOT search for new papers or generate summaries

**Requires**: Network access only

**Output**: `literature/pdfs/`

### Option 11: Summarize

Generates AI summaries for papers with PDFs (requires Ollama).

- Analyzes all papers in `literature/library.json`
- Generates summaries for papers with PDFs but without summaries
- Saves summaries to `literature/summaries/`
- Does NOT search for new papers or download PDFs

**Requires**: Ollama server running with at least one model installed

**Output**: `literature/summaries/`

### Option 12: Cleanup

Removes papers without PDFs from library (local files only, no Ollama required).

- Removes entries from `literature/library.json` that don't have PDFs
- Updates `literature/references.bib` accordingly
- Does NOT require network or Ollama

**Requires**: Local file access only

**Output**: Updated `literature/library.json` and `literature/references.bib`

### Option 13: Advanced LLM Operations

Performs advanced LLM operations on selected papers (requires Ollama).

Available operations:
- Literature review synthesis
- Science communication narrative
- Comparative analysis
- Research gap identification
- Citation network analysis

**Requires**: Ollama server running with at least one model installed

**Output**: Generated analysis files in `literature/`

## Usage

### Interactive Mode (Default)

```bash
# Make executable (first time only)
chmod +x run.sh

# Run with interactive menu
./run.sh
```

### Non-Interactive Mode

For CI/CD integration or scripting:

```bash
# Core Build Operations
./run.sh --pipeline          # Run full pipeline (10 stages: 0-9, includes LLM)
./run.sh --pipeline --resume # Resume from last checkpoint
./run.sh --infra-tests        # Run infrastructure tests only
./run.sh --project-tests      # Run project tests only
./run.sh --render-pdf         # Render PDF manuscript only

# LLM Operations (requires Ollama)
./run.sh --reviews            # LLM manuscript review only (English)
./run.sh --translations       # LLM translations only

# Literature Operations:
./run.sh --search             # Search literature (network only, add to bibliography)
./run.sh --download           # Download PDFs (network only, for bibliography entries)
./run.sh --summarize          # Generate summaries (requires Ollama, for papers with PDFs)
./run.sh --cleanup            # Cleanup library (local files only, remove papers without PDFs)

# Show help
./run.sh --help
```

### Example Output

```
════════════════════════════════════════════════════════════════
  Research Project Template - Main Menu
════════════════════════════════════════════════════════════════

Core Pipeline Scripts (aligned with script numbering):
  0. Setup Environment (00_setup_environment.py)
  1. Run Tests (01_run_tests.py - infrastructure + project)
  2. Run Analysis (02_run_analysis.py)
  3. Render PDF (03_render_pdf.py)
  4. Validate Output (04_validate_output.py)
  5. Copy Outputs (05_copy_outputs.py)
  6. LLM Review (requires Ollama) (06_llm_review.py --reviews-only)
  7. LLM Translations (requires Ollama) (06_llm_review.py --translations-only)

Orchestration:
  8. Run Full Pipeline (10 stages: 0-9, via run.sh)

Literature Operations (via 07_literature_search.py, not part of core pipeline):
  9. Literature Search (all operations)
  10. Search only (network only)
  11. Download only (network only)
  12. Summarize (requires Ollama)
  13. Cleanup (local files only)
  14. Advanced LLM operations (requires Ollama)

  15. Exit
════════════════════════════════════════════════════════════════
  Repository: /Users/4d/Documents/GitHub/template
  Python: Python 3.11.0
════════════════════════════════════════════════════════════════

Select option [0-15]: 8
```

## Exit Codes

- **0**: Operation succeeded
- **1**: Operation failed - review errors and fix issues
- **2**: Operation skipped (e.g., Ollama not available for LLM review)

## Environment Variables

The script automatically sets:
- `PROJECT_ROOT`: Repository root directory
- `PYTHONPATH`: Includes root, infrastructure, and project/src

You can override by setting before running:
```bash
export LOG_LEVEL=0  # Enable debug logging
./run.sh
```

### Literature Search Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LITERATURE_DEFAULT_LIMIT` | `25` | Results per source per keyword |
| `MAX_PARALLEL_SUMMARIES` | `1` | Parallel summarization workers |
| `LLM_SUMMARIZATION_TIMEOUT` | `600` | Timeout for paper summarization (seconds) |

### LLM Review Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MAX_INPUT_LENGTH` | `500000` | Max chars to send to LLM. Set to `0` for unlimited. |
| `LLM_REVIEW_TIMEOUT` | `300` | Timeout per review in seconds |
| `LLM_LONG_MAX_TOKENS` | `4096` | Maximum tokens per review response |

## Error Handling

The script uses strict error handling:
- Stops immediately on first failure
- Provides clear error messages
- Shows which stage/operation failed
- Returns to menu after each operation

**Example error output**:
```
✗ Infrastructure tests failed

  Operation completed in 45s

Press Enter to return to menu...
```

## Python Script Alternative

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
python3 scripts/07_literature_search.py --search-only     # Search only
python3 scripts/07_literature_search.py --download-only   # Download only
python3 scripts/07_literature_search.py --summarize        # Summarize
python3 scripts/07_literature_search.py --cleanup           # Cleanup library
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

### Literature search fails

- **Search/Download operations**: Require network access only (no Ollama)
- **Summarization**: Requires Ollama server running
- **Cleanup**: Requires local file access only (no network or Ollama)

## See Also

- [`scripts/README.md`](scripts/README.md) - Stage orchestrators documentation
- [`scripts/AGENTS.md`](scripts/AGENTS.md) - Complete scripts documentation
- [`AGENTS.md`](AGENTS.md) - Complete system documentation
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) - Development workflow
- [`docs/BUILD_SYSTEM.md`](docs/BUILD_SYSTEM.md) - Detailed build system reference
