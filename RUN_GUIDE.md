# run.sh - Unified Pipeline Orchestration Guide

## Overview

`run.sh` is the unified orchestration script that provides an interactive menu for all pipeline operations:

```bash
./run.sh
```

This presents a menu with options for running tests, rendering PDFs, executing the full pipeline, LLM manuscript review, and literature search operations.

## Menu Options

```
============================================================
  Research Project Template - Main Menu
============================================================

Core Build Operations:
  1. Run infrastructure tests
  2. Run project tests
  3. Render PDF manuscript
  4. Run full pipeline (tests + analysis + PDF + validate)

LLM Operations (requires Ollama):
  5. LLM manuscript review (English)
  6. LLM translations (multi-language)

Literature Operations (requires Ollama):
  7. Search literature and download PDFs
  8. Generate summaries for existing PDFs

  9. Exit
============================================================
```

### Option 1: Run Infrastructure Tests

Tests the generic infrastructure modules with coverage validation.

- Runs all infrastructure module tests from `tests/infrastructure/`
- Validates coverage meets 49%+ threshold
- Covers: core, build, documentation, literature, llm, publishing, rendering, scientific, validation
- Generates HTML coverage report

**Coverage Report**: `htmlcov/index.html`

### Option 2: Run Project Tests

Tests project-specific scientific code with coverage validation.

- Runs project-specific tests from `project/tests/`
- Ignores integration tests (non-critical)
- Validates coverage meets 70%+ threshold for `project/src/`
- Generates HTML coverage report

**Coverage Report**: `htmlcov/index.html`

### Option 3: Render PDF Manuscript

Generates professional PDFs from markdown sources.

- Runs project analysis scripts first
- Processes markdown in `project/manuscript/`
- Converts to LaTeX via pandoc
- Compiles to PDF via xelatex
- Generates individual section PDFs and combined manuscript

**Output**: `project/output/pdf/`

### Option 4: Run Full Pipeline

Executes the complete 8-stage build pipeline:

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
| 8 | LLM Manuscript Review | Generate AI reviews (optional) |

**Generated Outputs**:
- Coverage reports: `htmlcov/`
- PDF files: `project/output/pdf/`
- Figures: `project/output/figures/`
- Data files: `project/output/data/`
- LLM reviews: `project/output/llm/` (if Ollama available)

### Option 5: LLM Manuscript Review (English)

Generates AI-powered manuscript analysis using local Ollama.

- Checks Ollama availability and selects best model
- Extracts full text from combined manuscript PDF
- Generates executive summary, quality review, methodology review, and improvement suggestions
- Saves all reviews to `output/llm/` with detailed metrics

**Requires**: Running Ollama server with at least one model installed.

**Output**: `output/llm/` directory with review files and metadata

### Option 6: LLM Translations (multi-language)

Generates technical abstract translations to multiple languages.

- Uses configured languages from `project/manuscript/config.yaml`
- Generates English technical abstract (~200-400 words)
- Translates to target languages (Chinese, Hindi, Russian, etc.)
- Saves translations to `output/llm/`

**Requires**: Running Ollama server and configured languages in config.yaml.

**Output**: `output/llm/translation_*.md` files

### Option 7: Search Literature and Download PDFs

Searches academic databases and downloads papers.

- Searches arXiv and Semantic Scholar for papers
- Downloads PDFs to `literature/pdfs/`
- Adds entries to BibTeX library (`literature/references.bib`)
- Generates AI summaries for downloaded papers

**Prompts for**:
- Keywords (comma-separated)
- Number of papers per keyword

**Output**: `literature/` directory

### Option 8: Generate Summaries for Existing PDFs

Generates AI summaries for existing PDFs in the library.

- Analyzes all papers in `literature/library.json`
- Downloads missing PDFs if possible
- Generates summaries for papers without summaries

**Output**: `literature/summaries/`

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
./run.sh --pipeline          # Run full pipeline
./run.sh --infra-tests        # Run infrastructure tests
./run.sh --project-tests      # Run project tests
./run.sh --render-pdf         # Render PDF manuscript

# LLM Operations (requires Ollama)
./run.sh --reviews            # LLM manuscript review
./run.sh --translations       # LLM translations

# Literature Operations (requires Ollama)
./run.sh --search             # Search literature and download PDFs
./run.sh --summarize          # Generate summaries for existing PDFs

# Show help
./run.sh --help
```

### Example Output

```
════════════════════════════════════════════════════════════════
  Research Project Template - Main Menu
════════════════════════════════════════════════════════════════

Core Build Operations:
  1. Run infrastructure tests
  2. Run project tests
  3. Render PDF manuscript
  4. Run full pipeline (tests + analysis + PDF + validate)

LLM Operations (requires Ollama):
  5. LLM manuscript review (English)
  6. LLM translations (multi-language)

Literature Operations (requires Ollama):
  7. Search literature and download PDFs
  8. Generate summaries for existing PDFs

  9. Exit

════════════════════════════════════════════════════════════════
  Repository: /Users/4d/Documents/GitHub/template
  Python: Python 3.11.0
════════════════════════════════════════════════════════════════

Select option [1-9]: 4
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
python3 scripts/02_run_analysis.py       # Run project scripts
python3 scripts/03_render_pdf.py         # Render PDFs only
python3 scripts/04_validate_output.py    # Validate outputs only
python3 scripts/05_copy_outputs.py       # Copy final deliverables
python3 scripts/06_llm_review.py         # LLM manuscript review
python3 scripts/07_literature_search.py --search     # Literature search
python3 scripts/07_literature_search.py --summarize  # Generate summaries
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

Ensure Ollama is running (required for summarization). If you only want to download papers without summaries, the feature requires Ollama for AI-powered analysis.

## See Also

- [`scripts/README.md`](scripts/README.md) - Stage orchestrators documentation
- [`scripts/AGENTS.md`](scripts/AGENTS.md) - Complete scripts documentation
- [`AGENTS.md`](AGENTS.md) - Complete system documentation
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) - Development workflow
- [`docs/BUILD_SYSTEM.md`](docs/BUILD_SYSTEM.md) - Detailed build system reference

