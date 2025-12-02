# scripts/ - Quick Reference

Generic entry point orchestrators for template pipeline. Work with any project structure.

## Overview

Root-level scripts are **generic orchestrators** that:
- Coordinate build pipeline stages
- Discover and invoke `project/scripts/`
- Handle I/O and orchestration
- Work with ANY project

Project-specific analysis scripts go in `project/scripts/`, not here.

## Unified Entry Point

### Interactive Menu (Recommended)

```bash
./run.sh
```

This presents a menu with all available operations:

```
============================================================
  Research Project Template - Main Menu
============================================================
  1. Run infrastructure tests
  2. Run project tests
  3. Render PDF manuscript
  4. Run full pipeline (tests + analysis + PDF + validate)
  5. Run LLM manuscript review
  6. Literature search and PDF download
  7. Generate summaries for downloaded PDFs
  8. Exit
============================================================
```

### Non-Interactive Mode

```bash
./run.sh --option 4    # Run full pipeline
./run.sh --pipeline    # Same as --option 4
./run.sh --search      # Literature search (option 6)
./run.sh --summarize   # Generate summaries (option 7)
./run.sh --help        # Show all options
```

## Pipeline Stages

| Stage | Script | Purpose |
|-------|--------|---------|
| 00 | `00_setup_environment.py` | Environment setup & validation |
| 01 | `01_run_tests.py` | Run complete test suite |
| 02 | `02_run_analysis.py` | Discover & run `project/scripts/` |
| 03 | `03_render_pdf.py` | PDF rendering orchestration |
| 04 | `04_validate_output.py` | Output validation & reporting |
| 05 | `05_copy_outputs.py` | Copy final deliverables to output/ |
| 06 | `06_llm_review.py` | LLM manuscript review (optional) |
| 07 | `07_literature_search.py` | Literature search & summarization |

## Running Individual Stages

```bash
python3 scripts/00_setup_environment.py  # Setup environment
python3 scripts/01_run_tests.py          # Run tests only
python3 scripts/02_run_analysis.py       # Run project scripts
python3 scripts/03_render_pdf.py         # Render PDFs only
python3 scripts/04_validate_output.py    # Validate outputs only
python3 scripts/05_copy_outputs.py       # Copy final deliverables
python3 scripts/06_llm_review.py         # LLM manuscript review
python3 scripts/07_literature_search.py --search     # Search for papers
python3 scripts/07_literature_search.py --summarize  # Generate summaries
```

## Entry Points

### Stage 00: Setup Environment
- Checks Python version
- Verifies dependencies
- Confirms build tools (pandoc, xelatex)
- Validates directory structure

### Stage 01: Run Tests
- Executes `project/tests/` with pytest
- Verifies coverage meets threshold (70%+)
- Generic - does not implement tests

### Stage 02: Run Analysis
- **Discovers** `project/scripts/`
- **Executes** each script in order
- Generic orchestrator (not analysis)
- Works with ANY project

### Stage 03: Render PDF
- Processes `project/manuscript/` markdown
- Converts to LaTeX via pandoc
- Compiles to PDF via xelatex
- Generic - does not implement rendering

### Stage 04: Validate Output
- Checks generated PDFs for issues
- Validates markdown references
- Checks figure integrity
- Generic validation

### Stage 05: Copy Outputs
- Cleans top-level `output/` directory
- Copies combined PDF manuscript
- Copies all presentation slides (PDF)
- Copies all web outputs (HTML)
- Validates all files copied

### Stage 06: LLM Manuscript Review (Optional)
- Checks Ollama availability
- Extracts full text from combined PDF
- Generates four types of reviews with detailed metrics
- Saves reviews to `output/llm/` with generation stats
- **Requires**: Running Ollama server with at least one model

### Stage 07: Literature Search
- Searches arXiv and Semantic Scholar
- Downloads PDFs to `literature/pdfs/`
- Generates AI summaries for papers
- **Requires**: Running Ollama server for summarization

**Usage**:
```bash
# Search mode (interactive keyword input)
python3 scripts/07_literature_search.py --search

# Search with specific keywords
python3 scripts/07_literature_search.py --search --keywords "machine learning,optimization"

# Generate summaries for existing PDFs
python3 scripts/07_literature_search.py --summarize

# Both operations
python3 scripts/07_literature_search.py --search --summarize
```

## Project-Specific Scripts

Analysis scripts belong in `project/scripts/`:

```
project/scripts/
├── analysis_pipeline.py     # Project-specific analysis
├── example_figure.py        # Project-specific figures
└── README.md                # Project docs
```

These scripts:
- Import from `project/src/` (computation)
- Import from `infrastructure/` (utilities)
- Are discovered and executed by `02_run_analysis.py`
- Follow thin orchestrator pattern

## Pipeline Architecture

```
Unified Entry Point (run.sh):
Menu Option 4 → Full Pipeline:
  STAGE 0: Clean Output Directories
    └─ PASS → STAGE 1
  STAGE 1: Setup Environment
    └─ PASS → STAGE 2
  STAGE 2: Infrastructure Tests (49%+ coverage)
    └─ PASS → STAGE 3
  STAGE 3: Project Tests (70%+ coverage)
    └─ PASS → STAGE 4
  STAGE 4: Project Analysis
    └─ PASS → STAGE 5
  STAGE 5: PDF Rendering
    └─ PASS → STAGE 6
  STAGE 6: Output Validation
    └─ PASS → STAGE 7
  STAGE 7: Copy Outputs
    └─ PASS → STAGE 8
  STAGE 8: LLM Review (Optional)
    └─ PASS/SKIP → COMPLETE
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `1` | Logging verbosity (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR) |
| `LLM_MAX_INPUT_LENGTH` | `500000` | Max chars to send to LLM. Set to `0` for unlimited. |
| `LITERATURE_DEFAULT_LIMIT` | `25` | Results per source per keyword |
| `MAX_PARALLEL_SUMMARIES` | `1` | Parallel summarization workers |

## Generic vs Project-Specific

### Root Scripts (Generic)
- Coordinate build pipeline
- Discover `project/scripts/`
- Handle stages (setup, test, analysis, pdf, validate)
- Work with ANY project

### Project Scripts (Specific)
- Implement domain-specific analysis
- Import from `project/src/`
- Use `infrastructure/` tools
- Are executed by `02_run_analysis.py`

## Architecture Diagram

```
scripts/ (Generic Entry Points)
  ├─ 00_setup_environment.py → Check environment
  ├─ 01_run_tests.py → Run tests
  ├─ 02_run_analysis.py → Discover & run project/scripts/
  ├─ 03_render_pdf.py → Build manuscript
  ├─ 04_validate_output.py → Validate outputs
  ├─ 05_copy_outputs.py → Copy deliverables
  ├─ 06_llm_review.py → LLM manuscript review (optional)
  └─ 07_literature_search.py → Literature search & summarization

project/scripts/ (Project-Specific)
  ├─ analysis_pipeline.py → Your analysis
  └─ example_figure.py → Your figures
```

## Deploying with Different Project

1. Create new `project/` with your research
2. Add code to `project/src/`
3. Add scripts to `project/scripts/`
4. Run `./run.sh` - it auto-discovers your code

Root entry points work with **ANY** project following this structure.

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../RUN_GUIDE.md`](../RUN_GUIDE.md) - Unified runner guide
- [`project/scripts/README.md`](../project/scripts/README.md) - Project scripts guide
- [`../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Pattern details
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation
