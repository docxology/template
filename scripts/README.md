# scripts/ - Quick Reference

Generic entry point orchestrators for template pipeline. Work with any project structure.

## Overview

Root-level scripts are **generic orchestrators** that:
- Coordinate build pipeline stages
- Discover and invoke `project/scripts/`
- Handle I/O and orchestration
- Work with ANY project

Project-specific analysis scripts go in `project/scripts/`, not here.

## Pipeline Orchestration

### Master Orchestor - Complete Pipeline (One-Line Execution)

**Shell Script (Recommended)**:
```bash
./run_all.sh
```

**Python Alternative**:
```bash
python3 scripts/run_all.py
```

The shell script executes the complete 8-stage pipeline, while Python scripts provide fine-grained control:

| Shell Stage | Python Script | Purpose |
|-------------|---------------|---------|
| **0** | *(clean only)* | Clean output directories |
| **1** | `00_setup_environment.py` | Environment setup & validation |
| **2** | *(infrastructure tests)* | Run infrastructure test suite |
| **3** | *(project tests)* | Run project test suite |
| **4** | `02_run_analysis.py` | Discover & run `project/scripts/` |
| **5** | `03_render_pdf.py` | PDF rendering orchestration |
| **6** | `04_validate_output.py` | Output validation & reporting |
| **7** | `05_copy_outputs.py` | Copy final deliverables to top-level output/ |
| **8** | `06_llm_review.py` | LLM manuscript review (optional, requires Ollama) |

**Note**: Shell script combines tests into stages 2-3, Python scripts provide separate test control via `01_run_tests.py`.

### Running Individual Stages

**Via Python Scripts**:
```bash
python3 scripts/00_setup_environment.py  # Setup environment
python3 scripts/01_run_tests.py          # Run tests only
python3 scripts/02_run_analysis.py       # Run project scripts
python3 scripts/03_render_pdf.py         # Render PDFs only
python3 scripts/04_validate_output.py    # Validate outputs only
python3 scripts/05_copy_outputs.py       # Copy final deliverables
```

**Via Shell Script** (runs full pipeline):
```bash
./run_all.sh  # Complete pipeline with both infrastructure and project tests
```

### Understanding the Execution Flow

The shell script (`run_all.sh`) orchestrates:

1. **Environment Setup** - Validates Python, dependencies, build tools, directories
2. **Infrastructure Tests** - Tests generic infrastructure modules (70%+ coverage)
3. **Project Tests** - Tests project-specific code (70%+ coverage)
4. **Analysis** - Runs project analysis scripts and generates figures
5. **PDF Rendering** - Generates PDFs from markdown sources
6. **Validation** - Validates all outputs and generates reports
7. **Copy Outputs** - Copies final deliverables to top-level output/ directory

Each stage stops the pipeline if it fails, providing clear error messages.

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

### Stage 02: Run Analysis ⭐
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
- Extracts full text from combined PDF (no truncation by default)
- Generates four types of reviews with detailed metrics
- Saves reviews to `output/llm/` with generation stats
- **Requires**: Running Ollama server with at least one model

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MAX_INPUT_LENGTH` | `500000` | Max chars to send to LLM. Set to `0` for unlimited. |

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

## Common Operations

### Complete End-to-End Build
```bash
python3 scripts/run_all.py
```

### Running Individual Stages
```bash
python3 scripts/01_run_tests.py
python3 scripts/02_run_analysis.py
python3 scripts/03_render_pdf.py
```

### Running Project Scripts Directly
```bash
python3 project/scripts/analysis_pipeline.py
python3 project/scripts/example_figure.py
```

## Pipeline Architecture

```
Shell Script Pipeline (run_all.sh):
STAGE 0: Clean Output Directories
  └─ Clean project/output/ and output/
    └─ PASS → STAGE 1

STAGE 1: Setup Environment
  └─ Verify dependencies, create directories
    └─ PASS → STAGE 2

STAGE 2: Infrastructure Tests
  └─ Run infrastructure test suite (49%+ coverage)
    └─ PASS → STAGE 3

STAGE 3: Project Tests
  └─ Run project test suite (70%+ coverage)
    └─ PASS → STAGE 4

STAGE 4: Project Analysis
  └─ Discover & execute project/scripts/
    └─ PASS → STAGE 5

STAGE 5: PDF Rendering
  └─ Build project/manuscript/ → PDFs
    └─ PASS → STAGE 6

STAGE 6: Output Validation
  └─ Validate PDFs and outputs
    └─ PASS → STAGE 7

STAGE 7: Copy Outputs
  └─ Copy deliverables to top-level output/
    └─ PASS → STAGE 8

STAGE 8: LLM Review (Optional)
  └─ Generate manuscript reviews with Ollama
    └─ PASS/SKIP → COMPLETE ✅
```

## Generic vs Project-Specific

### Root Scripts (Generic) ✅
- Coordinate build pipeline
- Discover `project/scripts/`
- Handle stages (setup, test, analysis, pdf, validate)
- Work with ANY project

### Project Scripts (Specific) ✅
- Implement domain-specific analysis
- Import from `project/src/`
- Use `infrastructure/` tools
- Are executed by `02_run_analysis.py`

## Key Principles

### Orchestration Pattern
- **Root scripts**: Generic pipeline coordination
- **Project scripts**: Domain-specific implementation
- **No duplication**: Each level has clear responsibility
- **Generic discovery**: Root scripts find project scripts

### Thin Orchestrator
- Import functions, don't implement algorithms
- Coordinate components, don't implement logic
- Handle I/O, don't implement computation
- Testable through component tests

## Architecture Diagram

```
scripts/ (Generic Entry Points)
  ├─ 00_setup_environment.py → Check environment
  ├─ 01_run_tests.py → Run tests
  ├─ 02_run_analysis.py → Discover & run project/scripts/
  ├─ 03_render_pdf.py → Build manuscript
  ├─ 04_validate_output.py → Validate outputs
  ├─ 05_copy_outputs.py → Copy deliverables
  └─ 06_llm_review.py → LLM manuscript review (optional)

project/scripts/ (Project-Specific)
  ├─ analysis_pipeline.py → Your analysis
  └─ example_figure.py → Your figures
```

## Deploying with Different Project

1. Create new `project/` with your research
2. Add code to `project/src/`
3. Add scripts to `project/scripts/`
4. Run root entry points - they auto-discover your code

Root entry points work with **ANY** project following this structure.

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`project/scripts/README.md`](../project/scripts/README.md) - Project scripts guide
- [`../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Pattern details
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation
