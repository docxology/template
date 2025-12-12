# Pipeline Orchestration Guide

## Overview

The Research Project Template provides **three main entry points** for pipeline operations:

1. **`run.sh`** - Main dispatcher menu (routes to manuscript or literature operations)
2. **`run_manuscript.sh`** - Manuscript pipeline operations (10 stages: 0-9)
3. **`run_literature.sh`** - Literature search and management operations (7 menu options)

**Alternative Entry Point**: For a simpler 6-stage core pipeline without LLM features, use `python3 scripts/run_all.py` instead.

## Entry Point 1: Main Dispatcher (`run.sh`)

`run.sh` is a **dispatcher script** that provides a simple menu to choose between manuscript and literature operations:

```bash
./run.sh
```

### Dispatcher Menu

```
============================================================
  Research Project Template - Main Menu
============================================================

Select operation type:

  1. Manuscript Operations
     (Setup, Tests, Analysis, PDF Rendering, Validation, LLM Review)

  2. Literature Operations
     (Search, Download, Extract, Summarize, Advanced LLM Operations)

  3. Exit
============================================================
```

### Dispatcher Usage

**Interactive Mode (Default)**:
```bash
./run.sh
```

**Non-Interactive Mode**:
```bash
# Route to manuscript operations
./run.sh --manuscript [options]

# Route to literature operations
./run.sh --literature [options]

# Examples:
./run.sh --manuscript --pipeline        # Run manuscript full pipeline
./run.sh --literature --search          # Run literature search
./run.sh --help                         # Show help
```

**Direct Access**: You can also run the specialized scripts directly:
```bash
./run_manuscript.sh [options]   # Direct access to manuscript operations
./run_literature.sh [options]  # Direct access to literature operations
```

## Entry Point 2: Manuscript Operations (`run_manuscript.sh`)

`run_manuscript.sh` provides an interactive menu for all manuscript pipeline operations:

```bash
./run_manuscript.sh
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
  5. Copy Outputs (05_copy_outputs.py)
  6. LLM Review (requires Ollama) (06_llm_review.py --reviews-only)
  7. LLM Translations (requires Ollama) (06_llm_review.py --translations-only)

Orchestration:
  8. Run Full Pipeline (10 stages: 0-9)
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
Executes the complete test suite with coverage validation.
- Runs infrastructure tests (`tests/infrastructure/`) with 60%+ coverage threshold
- Runs project tests (`project/tests/`) with 90%+ coverage threshold
- Generates HTML coverage reports for both suites
- Generates structured test reports (JSON, Markdown)

**Coverage Reports**: `htmlcov/index.html`

#### Option 2: Run Analysis
Executes project analysis scripts with enhanced progress tracking.
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
Validates build quality with enhanced reporting.
- Checks generated PDFs for issues
- Validates markdown references
- Checks figure integrity
- Generates enhanced validation reports (JSON, Markdown)

#### Option 5: Copy Outputs
Copies final deliverables to top-level output directory.
- Cleans top-level `output/` directory
- Copies combined PDF manuscript
- Copies all presentation slides (PDF format)
- Copies all web outputs (HTML format)

#### Option 6: LLM Review
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
Executes the complete 10-stage build pipeline (stages 0-9):

| Stage | Name | Purpose |
|-------|------|---------|
| 0 | Clean Output Directories | Prepare fresh output directories |
| 1 | Setup Environment | Verify Python, dependencies, build tools |
| 2 | Infrastructure Tests | Test generic modules (60%+ coverage) |
| 3 | Project Tests | Test project code (90%+ coverage) |
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

**Checkpoint/Resume**: Supports `--resume` flag to resume from last checkpoint

### Manuscript Non-Interactive Mode

```bash
# Core Build Operations
./run_manuscript.sh --pipeline          # Run full pipeline (10 stages: 0-9, includes LLM)
./run_manuscript.sh --pipeline --resume # Resume from last checkpoint
./run_manuscript.sh --infra-tests        # Run infrastructure tests only
./run_manuscript.sh --project-tests      # Run project tests only
./run_manuscript.sh --render-pdf         # Render PDF manuscript only

# LLM Operations (requires Ollama)
./run_manuscript.sh --reviews            # LLM manuscript review only (English)
./run_manuscript.sh --translations       # LLM translations only

# Show help
./run_manuscript.sh --help
```

## Entry Point 3: Literature Operations (`run_literature.sh`)

`run_literature.sh` provides an interactive menu for all literature search and management operations:

```bash
./run_literature.sh
```

### Literature Menu (Options 0-7)

```
============================================================
  Literature Operations Menu
============================================================

Current Library Status:
  • Total papers: X
  • With PDFs: Y
  • With summaries: Z

Orchestrated Pipelines:
  0. Full Pipeline (search → download → extract → summarize)

Individual Operations (via 07_literature_search.py):
  1. Search Only (network only - add to bibliography)
  2. Download Only (network only - download PDFs)
  3. Extract Text (local only - extract text from PDFs)
  4. Summarize (requires Ollama - generate summaries)
  5. Cleanup (local files only - remove papers without PDFs)
  6. Advanced LLM Operations (requires Ollama)

  7. Exit
============================================================
```

### Literature Menu Options

#### Option 0: Full Pipeline
Runs orchestrated literature pipeline: search → download → extract → summarize.
- Searches academic databases for keywords
- Downloads PDFs from available sources
- Extracts text from PDFs (save to extracted_text/)
- Generates AI-powered summaries (requires Ollama)

**Requires**: Network access. Summarization requires Ollama.

#### Option 1: Search Only
Searches for papers and adds to bibliography (network only, no Ollama required).
- Searches arXiv and Semantic Scholar APIs
- Adds papers to bibliography (`literature/references.bib`)
- Updates library index (`literature/library.json`)
- Does NOT download PDFs or generate summaries

**Requires**: Network access only

**Output**: `literature/references.bib`, `literature/library.json`

#### Option 2: Download Only
Downloads PDFs for existing bibliography entries (network only, no Ollama required).
- Downloads PDFs for papers in bibliography without PDFs
- Saves PDFs to `literature/pdfs/`
- Updates library index
- Does NOT search for new papers or generate summaries

**Requires**: Network access only

**Output**: `literature/pdfs/`

#### Option 3: Extract Text
Extracts text from downloaded PDFs (local operation, no network or Ollama required).
- Processes PDFs in `literature/pdfs/`
- Extracts text content
- Saves extracted text to `literature/extracted_text/`
- Does NOT require network or Ollama

**Requires**: Local file access only

**Output**: `literature/extracted_text/`

#### Option 4: Summarize
Generates AI summaries for papers with PDFs (requires Ollama).
- Analyzes all papers in `literature/library.json`
- Generates summaries for papers with PDFs but without summaries
- Saves summaries to `literature/summaries/`
- Does NOT search for new papers or download PDFs

**Requires**: Ollama server running with at least one model installed

**Output**: `literature/summaries/`

#### Option 5: Cleanup
Removes papers without PDFs from library (local files only, no Ollama required).
- Removes entries from `literature/library.json` that don't have PDFs
- Updates `literature/references.bib` accordingly
- Does NOT require network or Ollama

**Requires**: Local file access only

**Output**: Updated `literature/library.json` and `literature/references.bib`

#### Option 6: Advanced LLM Operations
Performs advanced LLM operations on selected papers (requires Ollama).

Available operations:
- Literature review synthesis
- Science communication narrative
- Comparative analysis
- Research gap identification
- Citation network analysis

**Requires**: Ollama server running with at least one model installed

**Output**: Generated analysis files in `literature/`

### Literature Non-Interactive Mode

```bash
# Literature Operations:
./run_literature.sh --search             # Search literature (network only, add to bibliography)
./run_literature.sh --download           # Download PDFs (network only, for bibliography entries)
./run_literature.sh --extract-text       # Extract text from PDFs
./run_literature.sh --summarize          # Generate summaries (requires Ollama, for papers with PDFs)
./run_literature.sh --cleanup            # Cleanup library (local files only, remove papers without PDFs)
./run_literature.sh --llm-operation      # Advanced LLM operations (requires Ollama)

# Show help
./run_literature.sh --help
```

## Entry Point 4: Python Orchestrator (`scripts/run_all.py`)

For programmatic access or CI/CD integration, use the Python orchestrator:

```bash
# Core pipeline (6 stages) - Python orchestrator
python3 scripts/run_all.py
```

**Features**:
- 6-stage core pipeline (stages 00-05)
- No LLM dependencies required
- Suitable for automated environments
- Zero-padded stage numbering (Python convention)
- Checkpoint/resume support: `python3 scripts/run_all.py --resume`

### Core Pipeline Stages (00-05)

| Stage | Script | Purpose |
|-------|--------|---------|
| 00 | `00_setup_environment.py` | Environment setup & validation |
| 01 | `01_run_tests.py` | Run complete test suite (infrastructure + project) |
| 02 | `02_run_analysis.py` | Discover & run `project/scripts/` |
| 03 | `03_render_pdf.py` | PDF rendering orchestration |
| 04 | `04_validate_output.py` | Output validation & reporting |
| 05 | `05_copy_outputs.py` | Copy final deliverables to `output/` |

## Entry Point Comparison

| Entry Point | Pipeline Stages | LLM Support | Use Case |
|-------------|----------------|--------------|----------|
| `./run.sh` | Dispatcher (routes to others) | Via routing | Interactive menu selection |
| `./run_manuscript.sh --pipeline` | 10 stages (0-9) | Optional | Full manuscript pipeline with LLM |
| `./run_literature.sh` | 7 menu options | Optional | Literature search and management |
| `python3 scripts/run_all.py` | 6 stages (00-05) | None | Core pipeline, CI/CD automation |

## Usage Examples

### Interactive Mode

```bash
# Main dispatcher
./run.sh

# Direct access to manuscript operations
./run_manuscript.sh

# Direct access to literature operations
./run_literature.sh
```

### Non-Interactive Mode

```bash
# Run full manuscript pipeline
./run_manuscript.sh --pipeline

# Resume manuscript pipeline from checkpoint
./run_manuscript.sh --pipeline --resume

# Run literature search
./run_literature.sh --search

# Run core pipeline (Python)
python3 scripts/run_all.py
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
python3 scripts/07_literature_search.py --search-only     # Search only
python3 scripts/07_literature_search.py --download-only   # Download only
python3 scripts/07_literature_search.py --extract-text     # Extract text
python3 scripts/07_literature_search.py --summarize        # Summarize
python3 scripts/07_literature_search.py --cleanup         # Cleanup library
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
./run_manuscript.sh --pipeline
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
chmod +x run.sh run_manuscript.sh run_literature.sh
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
