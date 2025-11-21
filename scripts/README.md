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

### Master Orchestrator (One-Line Execution)
```bash
python3 scripts/run_all.py
```

Executes the complete 5-stage pipeline end-to-end:

| Stage | Script | Purpose |
|-------|--------|---------|
| **00** | `00_setup_environment.py` | Environment setup & validation |
| **01** | `01_run_tests.py` | Test suite with coverage |
| **02** | `02_run_analysis.py` | Discover & run `project/scripts/` |
| **03** | `03_render_pdf.py` | PDF rendering orchestration |
| **04** | `04_validate_output.py` | Output validation & reporting |

### Individual Stage Scripts

Each stage can also be run independently:

```bash
python3 scripts/00_setup_environment.py  # Setup environment
python3 scripts/01_run_tests.py          # Run tests only
python3 scripts/02_run_analysis.py       # Run project scripts
python3 scripts/03_render_pdf.py         # Render PDFs only
python3 scripts/04_validate_output.py    # Validate outputs only
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
STAGE 00: Environment Setup
  └─ Verify dependencies, create directories
     └─ PASS → STAGE 01
     
STAGE 01: Run Tests
  └─ Execute project/tests/ with coverage
     └─ PASS → STAGE 02
     
STAGE 02: Run Analysis
  └─ Discover & execute project/scripts/
     └─ PASS → STAGE 03
     
STAGE 03: Render PDF
  └─ Build project/manuscript/ → PDFs
     └─ PASS → STAGE 04
     
STAGE 04: Validate Output
  └─ Validate PDFs and outputs
     └─ PASS → COMPLETE ✅
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
  └─ 04_validate_output.py → Validate outputs

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
