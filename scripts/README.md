# scripts/ - Quick Reference

Generic entry point orchestrators for template pipeline. Work with any project structure.

## Overview

Root-level scripts are **generic orchestrators** that:
- Coordinate build pipeline stages
- Discover and invoke `project/scripts/`
- Handle I/O and orchestration
- Work with ANY project

Project-specific analysis scripts go in `project/scripts/`, not here.

## Entry Points

The template provides **two pipeline orchestrators** with different scope:

### Primary: Interactive Menu (`./run.sh`)

**Recommended entry point** - Interactive menu with all operations:

```bash
./run.sh
```

This presents a menu with all available operations (menu numbering aligns with script numbering):

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
  6. LLM Review (requires Ollama) (06_llm_review.py)
  7. Literature Search (07_literature_search.py)

Orchestration:
  8. Run Full Pipeline (10 stages: 0-9, via run.sh)

Literature Sub-Operations (via 07_literature_search.py):
  9. Search only (network only)
  10. Download only (network only)
  11. Summarize (requires Ollama)
  12. Cleanup (local files only)
  13. Advanced LLM operations (requires Ollama)

  14. Exit
============================================================
```

**Non-Interactive Mode:**
```bash
# Core Build Operations
./run.sh --pipeline          # Extended pipeline (10 stages: 0-9, includes LLM)
./run.sh --pipeline --resume # Resume from last checkpoint
./run.sh --infra-tests        # Run infrastructure tests only
./run.sh --project-tests      # Run project tests only
./run.sh --render-pdf         # Render PDF manuscript only

# LLM Operations (requires Ollama)
./run.sh --reviews            # LLM manuscript review only
./run.sh --translations       # LLM translations only

# Literature Operations:
./run.sh --search             # Search literature (network only, add to bibliography)
./run.sh --download           # Download PDFs (network only, for bibliography entries)
./run.sh --summarize          # Generate summaries (requires Ollama, for papers with PDFs)
./run.sh --cleanup            # Cleanup library (local files only, remove papers without PDFs)

./run.sh --help               # Show all options
```

### Alternative: Python Orchestrator (`run_all.py`)

**Programmatic entry point** - Core pipeline only (6 stages):

```bash
python3 scripts/run_all.py  # Core pipeline (no LLM stages)
```

**Features:**
- 6-stage core pipeline (stages 00-05)
- No LLM dependencies required
- Suitable for automated environments
- Zero-padded stage numbering (Python convention)
- Checkpoint/resume support: `python3 scripts/run_all.py --resume`

## Pipeline Stages

### Core Pipeline (Stages 00-05)

Both entry points support these core stages:

| Stage | Script | Purpose |
|-------|--------|---------|
| 00 | `00_setup_environment.py` | Environment setup & validation |
| 01 | `01_run_tests.py` | Run complete test suite |
| 02 | `02_run_analysis.py` | Discover & run `project/scripts/` |
| 03 | `03_render_pdf.py` | PDF rendering orchestration |
| 04 | `04_validate_output.py` | Output validation & reporting |
| 05 | `05_copy_outputs.py` | Copy final deliverables to output/ |

### Extended Pipeline Stages (`./run.sh` only)

Additional stages available in the interactive orchestrator (stages 8-9):

| Stage | Script | Purpose |
|-------|--------|---------|
| 8 | `06_llm_review.py --reviews-only` | LLM Scientific Review (optional) |
| 9 | `06_llm_review.py --translations-only` | LLM Translations (optional) |

**Note**: Literature operations (menu options 7, 9-13) are standalone operations, not part of the main pipeline stages.

**Stage Numbering:**
- `./run.sh`: Stages 0-9 (10 total). Stage 0 is cleanup (not tracked in progress), stages 1-9 are displayed as [1/9] to [9/9] in logs
- `run_all.py`: Stages 00-05 (zero-padded Python convention, 6 core stages)

## Running Individual Stages

```bash
python3 scripts/00_setup_environment.py  # Setup environment
python3 scripts/01_run_tests.py          # Run tests only (quiet mode by default)
python3 scripts/01_run_tests.py --verbose  # Run tests with verbose output
python3 scripts/02_run_analysis.py       # Run project scripts
python3 scripts/03_render_pdf.py         # Render PDFs only
python3 scripts/04_validate_output.py    # Validate outputs only
python3 scripts/05_copy_outputs.py       # Copy final deliverables
python3 scripts/06_llm_review.py         # LLM manuscript review
python3 scripts/07_literature_search.py --search     # Search for papers
python3 scripts/07_literature_search.py --summarize  # Generate summaries
```

## Generated Reports

The pipeline automatically generates comprehensive reports in `project/output/reports/`:

- **`pipeline_report.{json,html,md}`** - Consolidated pipeline execution report
  - Generated by `scripts/run_all.py` at end of pipeline
  - Includes stage results, test results, validation results, performance metrics
  - HTML version provides visual dashboard with status indicators

- **`test_results.{json,md}`** - Structured test execution report
  - Generated by `scripts/01_run_tests.py`
  - Includes test counts, coverage metrics, execution times
  - Links to detailed HTML coverage reports

- **`validation_report.{json,md}`** - Enhanced validation report
  - Generated by `scripts/04_validate_output.py`
  - Includes actionable recommendations with priority levels
  - Categorizes issues (errors vs warnings)

- **`error_summary.{json,md}`** - Error aggregation report
  - Generated when errors occur during pipeline execution
  - Categorizes errors by type
  - Provides actionable fixes with documentation links

## Entry Points

### Stage 00: Setup Environment
- Checks Python version
- Verifies dependencies
- Confirms build tools (pandoc, xelatex)
- Validates directory structure

**Note**: In `run.sh` pipeline, this is Stage 1 (Stage 0 is Clean Output Directories).

### Stage 01: Run Tests
- Executes infrastructure tests (`tests/infrastructure/`) with 49%+ coverage threshold
- Executes project tests (`project/tests/`) with 70%+ coverage threshold
- Supports quiet mode (`--quiet` or `-q`) to suppress individual test names
- Supports verbose mode (`--verbose` or `-v`) to show all test names
- Generates structured test reports (JSON, Markdown) to `project/output/reports/`
- Generic - does not implement tests

**Note**: In `run.sh` pipeline, this is Stage 2 (after Setup Environment).

### Stage 02: Run Analysis
- **Discovers** `project/scripts/`
- **Executes** each script in order
- Generic orchestrator (not analysis)
- Works with ANY project

**Note**: In `run.sh` pipeline, this is Stage 4 (after Tests).

### Stage 03: Render PDF
- Processes `project/manuscript/` markdown
- Converts to LaTeX via pandoc
- Compiles to PDF via xelatex
- Generic - does not implement rendering

**Note**: In `run.sh` pipeline, this is Stage 5 (after Analysis).

### Stage 04: Validate Output
- Checks generated PDFs for issues
- Validates markdown references
- Checks figure integrity
- Generates enhanced validation reports (JSON, Markdown) with actionable recommendations
- Reports saved to `project/output/reports/validation_report.{json,md}`
- Generic validation

**Note**: In `run.sh` pipeline, this is Stage 6 (after PDF Rendering).

### Stage 05: Copy Outputs
- Cleans top-level `output/` directory
- Copies combined PDF manuscript
- Copies all presentation slides (PDF)
- Copies all web outputs (HTML)
- Validates all files copied

**Note**: In `run.sh` pipeline, this is Stage 7 (after Validation).

### Stage 06: LLM Manuscript Review (Optional)
- Checks Ollama availability
- Extracts full text from combined PDF
- Generates four types of reviews with detailed metrics
- Uses improved progress indicators (spinner, streaming progress) for better feedback
- Saves reviews to `project/output/llm/` with generation stats (copied to `output/llm/` during copy stage)
- **Requires**: Running Ollama server with at least one model

**Note**: In `run.sh` pipeline, this is Stage 8 (LLM Scientific Review).

### Stage 07: Literature Operations (Standalone, not in main pipeline)
- **Search**: Searches arXiv and Semantic Scholar APIs, adds to bibliography (network only, no Ollama required)
- **Download**: Downloads PDFs for existing bibliography entries (network only, no Ollama required)
- **Summarize**: Generates AI summaries for papers with PDFs (requires Ollama)
- **Cleanup**: Removes papers without PDFs from library (local files only, no Ollama required)
- **LLM Operations**: Advanced LLM operations like literature review synthesis (requires Ollama)

**Note**: These are standalone operations (menu options 7, 9-13), not part of the main 10-stage pipeline.

**Usage**:
```bash
# Search only (network only, no Ollama required)
python3 scripts/07_literature_search.py --search-only
python3 scripts/07_literature_search.py --search-only --keywords "machine learning,optimization"

# Download PDFs only (network only, no Ollama required)
python3 scripts/07_literature_search.py --download-only

# Generate summaries (requires Ollama)
python3 scripts/07_literature_search.py --summarize

# Cleanup library (local files only, no Ollama required)
python3 scripts/07_literature_search.py --cleanup

# Advanced LLM operations (requires Ollama)
python3 scripts/07_literature_search.py --llm-operation review
```

## Checkpoint and Resume

The pipeline supports automatic checkpointing and resume capability:

### Automatic Checkpointing

- Checkpoints are saved after each successful stage
- Location: `project/output/.checkpoints/pipeline_checkpoint.json`
- Automatically cleared on successful pipeline completion

### Resuming from Checkpoint

```bash
# Resume from last checkpoint (Python orchestrator)
python3 scripts/run_all.py --resume

# Resume from last checkpoint (Shell orchestrator)
./run.sh --pipeline --resume
```

### Checkpoint Validation

The system validates checkpoints before resuming:
- File existence and format validation
- Stage count consistency checks
- Integrity verification (all completed stages have exit code 0)

If validation fails, the pipeline starts fresh with a warning.

### Manual Checkpoint Management

```bash
# Check if checkpoint exists
python3 -c "from infrastructure.core.checkpoint import CheckpointManager; cm = CheckpointManager(); print('Exists:', cm.checkpoint_exists())"

# View checkpoint contents
cat project/output/.checkpoints/pipeline_checkpoint.json | python3 -m json.tool

# Clear checkpoint manually
rm -f project/output/.checkpoints/pipeline_checkpoint.json
```

See [`docs/CHECKPOINT_RESUME.md`](../docs/CHECKPOINT_RESUME.md) for complete documentation.

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
Menu Option 8 (--pipeline) → Full Pipeline (10 stages: 0-9):
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
  STAGE 8: LLM Scientific Review (Optional)
    └─ PASS/SKIP → STAGE 9
  STAGE 9: LLM Translations (Optional)
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
