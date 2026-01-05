# scripts/ - Quick Reference

Generic entry point orchestrators for template pipeline. Work with any project structure.

## Overview

Root-level scripts are **generic orchestrators** that:
- Coordinate build pipeline stages
- Discover and invoke `projects/{name}/scripts/`
- Handle I/O and orchestration
- Work with ANY project

Project-specific analysis scripts go in `projects/{name}/scripts/`, not here.

## Entry Points

The template provides **two entry points** for manuscript operations:

### Primary: Main Entry Point (`./run.sh`)

**Recommended entry point** - Routes to manuscript operations:

```bash
./run.sh
```

This routes directly to the manuscript pipeline operations menu.

**Non-Interactive Mode:**
```bash
./run.sh [options]  # Pass options to manuscript operations
./run.sh --help    # Show help
```

### Main Entry Point (`./run.sh`)

**Manuscript pipeline orchestrator** - Interactive menu with manuscript operations:

```bash
./run.sh
```

This presents a menu with manuscript operations:

```
============================================================
  Manuscript Pipeline - Main Menu
============================================================

Core Pipeline Scripts:
  0. Setup Environment
  1. Run Tests
  2. Run Analysis
  3. Render PDF
  4. Validate Output
  5. LLM Review (requires Ollama)
  6. LLM Translations (requires Ollama)

Orchestration:
  8. Run Full Pipeline (9 stages: [1/9] to [9/9])
============================================================
```

**Non-Interactive Mode:**
```bash
# Core Build Operations
./run.sh --pipeline          # Extended pipeline (9 stages displayed as [1/9] to [9/9], includes LLM)
./run.sh --pipeline --resume # Resume from last checkpoint
./run.sh --infra-tests       # Run infrastructure tests only
./run.sh --project-tests     # Run project tests only
./run.sh --render-pdf        # Render PDF manuscript only

# LLM Operations (requires Ollama)
./run.sh --reviews            # LLM manuscript review only
./run.sh --translations       # LLM translations only

./run.sh --help               # Show all options
```

### Alternative: Python Orchestrators (`execute_pipeline.py`, `execute_multi_project.py`)

**Programmatic entry points**:

```bash
# Single project (core pipeline, no LLM)
python3 scripts/execute_pipeline.py --project code_project --core-only

# All projects (core pipeline, no LLM)
python3 scripts/execute_multi_project.py --no-llm
```

**Notes:**
- Checkpoint/resume support is available via `scripts/execute_pipeline.py --resume`.

## Pipeline Architecture

```mermaid
flowchart TD
    subgraph EntryPoints["Entry Points"]
        RUNSH[./run.sh<br/>Interactive Menu<br/>9-stage pipeline]
        PYTHON[execute_pipeline.py<br/>Programmatic<br/>Core pipeline]
        MULTI[execute_multi_project.py<br/>Multi-project<br/>Cross-project execution]
    end

    subgraph CoreStages["Core Pipeline Stages"]
        STAGE00[00_setup_environment.py<br/>Environment Setup<br/>Dependency validation]
        STAGE01[01_run_tests.py<br/>Test Execution<br/>Infrastructure + Project]
        STAGE02[02_run_analysis.py<br/>Analysis Orchestration<br/>Discover project scripts]
        STAGE03[03_render_pdf.py<br/>PDF Rendering<br/>Markdown → LaTeX → PDF]
        STAGE04[04_validate_output.py<br/>Output Validation<br/>Quality assurance]
        STAGE05[05_copy_outputs.py<br/>Copy Deliverables<br/>Final outputs]
    end

    subgraph ExtendedStages["Extended Pipeline Stages"]
        STAGE06[06_llm_review.py<br/>LLM Review<br/>Scientific analysis]
        STAGE07[07_generate_executive_report.py<br/>Executive Report<br/>Multi-project summary]
    end

    subgraph ProjectScripts["Project Scripts"]
        PROJ_SCRIPTS[projects/{name}/scripts/<br/>Analysis workflows<br/>Domain-specific]
    end

    RUNSH --> STAGE00
    PYTHON --> STAGE00
    MULTI --> STAGE00

    STAGE00 --> STAGE01
    STAGE01 --> STAGE02
    STAGE02 --> PROJ_SCRIPTS
    PROJ_SCRIPTS --> STAGE03
    STAGE03 --> STAGE04
    STAGE04 --> STAGE05

    RUNSH --> STAGE06
    STAGE05 --> STAGE06
    STAGE06 --> STAGE07

    classDef entry fill:#e3f2fd,stroke:#1565c0,stroke-width:3px
    classDef core fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef extended fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef project fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class RUNSH,PYTHON,MULTI entry
    class STAGE00,STAGE01,STAGE02,STAGE03,STAGE04,STAGE05 core
    class STAGE06,STAGE07 extended
    class PROJ_SCRIPTS project
```

## Pipeline Stages

### Core Pipeline (Stages 00-05)

Both entry points support these core stages:

| Stage | Script | Purpose |
|-------|--------|---------|
| 00 | `00_setup_environment.py` | Environment setup & validation |
| 01 | `01_run_tests.py` | Run test suite |
| 02 | `02_run_analysis.py` | Discover & run `projects/{name}/scripts/` |
| 03 | `03_render_pdf.py` | PDF rendering orchestration |
| 04 | `04_validate_output.py` | Output validation & reporting |
| 05 | `05_copy_outputs.py` | Copy final deliverables to output/ |

### Extended Pipeline Stages (`./run.sh` only)

Additional stages available in the interactive orchestrator:

| Stage | Script | Purpose |
|-------|--------|---------|
| 8 | `06_llm_review.py` | LLM Scientific Review (optional, requires Ollama) |
| 9 | `06_llm_review.py` | LLM Translations (optional, requires Ollama) |

**Stage Numbering:**
- `./run.sh`: 9 stages displayed as [1/9] to [9/9] in logs (Clean Output Directories, Environment Setup, Infrastructure Tests, Project Tests, Project Analysis, PDF Rendering, Output Validation, LLM Scientific Review, LLM Translations, Copy Outputs)
- `scripts/execute_pipeline.py`: core vs full pipeline is selected by flags (no fixed stage numbering in filenames)

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
```

## Generated Reports

The pipeline automatically generates reports in `projects/{name}/output/reports/`:

- **`pipeline_summary.txt`** - Human-readable pipeline summary (printed to console)
  - Generated by `scripts/execute_pipeline.py` at end of pipeline
  - Includes stage results and durations

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

### Stage 01: Run Tests
- Executes infrastructure tests (`tests/infrastructure/`) with 60%+ coverage threshold
- Executes project tests (`projects/{name}/tests/`) with 90%+ coverage threshold
- Supports quiet mode (`--quiet` or `-q`) to suppress individual test names
- Supports verbose mode (`--verbose` or `-v`) to show all test names
- Generates structured test reports (JSON, Markdown) to `projects/{name}/output/reports/`
- Generic - does not implement tests

### Stage 02: Run Analysis
- **Discovers** `projects/{name}/scripts/`
- **Executes** each script in order
- Generic orchestrator (not analysis)
- Works with ANY project

### Stage 03: Render PDF
- Processes `projects/{name}/manuscript/` markdown
- Converts to LaTeX via pandoc
- Compiles to PDF via xelatex
- Generic - does not implement rendering

### Stage 04: Validate Output
- Checks generated PDFs for issues
- Validates markdown references
- Checks figure integrity
- Generates validation reports (JSON, Markdown) with actionable recommendations
- Reports saved to `projects/{name}/output/reports/validation_report.{json,md}`
- Generic validation

### Stage 05: Copy Outputs
- Cleans top-level `output/` directory
- Copies combined PDF manuscript
- Copies all presentation slides (PDF)
- Copies all web outputs (HTML)
- Validates all files copied

### Executive Report Generation (Multi-Project Only)
- Discovers all projects in repository
- Collects comprehensive metrics across all projects
- Generates cross-project comparisons and recommendations
- Creates visual dashboards (PNG, PDF, HTML)
- Saves reports to `output/executive_summary/`
- Requires 2+ projects (designed for multi-project comparisons)

### Stage 8: LLM Scientific Review (Optional)
- Checks Ollama availability
- Extracts full text from combined PDF
- Generates four types of reviews with detailed metrics
- Uses improved progress indicators (spinner, streaming progress) for better feedback
- Saves reviews to `output/llm/` with generation stats
- **Requires**: Running Ollama server with at least one model


## Checkpoint and Resume

The pipeline supports automatic checkpointing and resume capability:

### Automatic Checkpointing

- Checkpoints are saved after each successful stage
- Location: `projects/{name}/output/.checkpoints/pipeline_checkpoint.json`
- Automatically cleared on successful pipeline completion

### Resuming from Checkpoint

```bash
# Resume from last checkpoint (Python orchestrator)
python3 scripts/execute_pipeline.py --project code_project --core-only --resume

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
cat projects/code_project/output/.checkpoints/pipeline_checkpoint.json | python3 -m json.tool

# Clear checkpoint manually
rm -f projects/code_project/output/.checkpoints/pipeline_checkpoint.json
```

See [`docs/CHECKPOINT_RESUME.md`](../docs/CHECKPOINT_RESUME.md) for complete documentation.

## Project-Specific Scripts

Analysis scripts belong in `projects/{name}/scripts/`:

```
project/scripts/
├── analysis_pipeline.py     # Project-specific analysis
├── example_figure.py        # Project-specific figures
└── README.md                # Project docs
```

These scripts:
- Import from `projects/{name}/src/` (computation)
- Import from `infrastructure/` (utilities)
- Are discovered and executed by `02_run_analysis.py`
- Follow thin orchestrator pattern

## Pipeline Architecture

```mermaid
graph TB
    subgraph EntryPoints["Entry Points"]
        RUNSH[./run.sh<br/>Interactive menu<br/>Full pipeline control]
        EXECPIPE[execute_pipeline.py<br/>Programmatic<br/>Single project pipeline]
    end

    subgraph Orchestrators["Generic Orchestrators<br/>scripts/"]
        SETUP[00_setup_environment.py<br/>Environment validation]
        TESTS[01_run_tests.py<br/>Test execution<br/>Infrastructure + Project]
        ANALYSIS[02_run_analysis.py<br/>Project script discovery<br/>Execute projects/{name}/scripts/]
        RENDER[03_render_pdf.py<br/>Manuscript rendering<br/>Markdown → PDF]
        VALIDATE[04_validate_output.py<br/>Quality validation<br/>PDF + Markdown checks]
        COPY[05_copy_outputs.py<br/>Deliverable copying<br/>Output → root/]
        LLMREVIEW[06_llm_review.py<br/>LLM manuscript review<br/>Optional, requires Ollama]
    end

    subgraph ProjectCode["Project-Specific Code<br/>project/"]
        PROJECTSRC[projects/{name}/src/<br/>Scientific algorithms<br/>Data processing, analysis]
        PROJECTSCRIPTS[projects/{name}/scripts/<br/>Analysis workflows<br/>Figure generation, reports]
        MANUSCRIPT[projects/{name}/manuscript/<br/>Research content<br/>Markdown sections]
    end

    subgraph Outputs["Generated Outputs<br/>output/ & project/output/"]
        PDF[pdf/<br/>Manuscript PDFs<br/>Individual + combined]
        FIGURES[figures/<br/>Generated plots<br/>PNG, PDF formats]
        DATA[data/<br/>Analysis datasets<br/>CSV, NPZ files]
        REPORTS[reports/<br/>Validation reports<br/>JSON, HTML, Markdown]
    end

    RUNSH --> SETUP
    EXECPIPE --> SETUP

    SETUP --> TESTS
    TESTS --> ANALYSIS
    ANALYSIS --> PROJECTSCRIPTS
    ANALYSIS --> RENDER
    RENDER --> VALIDATE
    VALIDATE --> COPY
    COPY --> LLMREVIEW

    PROJECTSCRIPTS --> FIGURES
    PROJECTSCRIPTS --> DATA

    RENDER --> PDF
    VALIDATE --> REPORTS

    PROJECTSRC -.->|Import for computation| PROJECTSCRIPTS
    MANUSCRIPT -.->|Content source| RENDER

    classDef entry fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef orchestrator fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef project fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef output fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class RUNSH,RUNALL entry
    class SETUP,TESTS,ANALYSIS,RENDER,VALIDATE,COPY,LLMREVIEW orchestrator
    class PROJECTSRC,PROJECTSCRIPTS,MANUSCRIPT project
    class PDF,FIGURES,DATA,REPORTS output
```

## Detailed Execution Flow

```mermaid
flowchart TD
    START([Pipeline Start]) --> ENTRY{Choose Entry Point}

    ENTRY -->|Interactive| RUNSH[./run.sh<br/>Show menu]
    ENTRY -->|Programmatic| EXECPIPE[execute_pipeline.py<br/>Direct execution]

    RUNSH --> MENU[Display Options:<br/>0-9 Pipeline Stages]
    MENU --> CHOICE[User selects<br/>pipeline option]
    CHOICE --> SETUP

    RUNALL --> SETUP[Stage 00:<br/>Environment Setup]

    SETUP -->|✅ Python, deps, tools OK| TESTS[Stage 01:<br/>Test Execution]
    SETUP -->|❌ Missing deps| FAIL([Pipeline Failed<br/>Install dependencies])

    TESTS -->|✅ Tests pass + coverage| ANALYSIS[Stage 02:<br/>Analysis Discovery]
    TESTS -->|❌ Tests fail| FAIL

    ANALYSIS -->|✅ Scripts found| EXECUTE_SCRIPTS[Execute projects/{name}/scripts/<br/>Generate figures & data]
    ANALYSIS -->|❌ No scripts| SKIP_SCRIPTS[Continue without analysis]

    EXECUTE_SCRIPTS --> RENDER[Stage 03:<br/>PDF Rendering]
    SKIP_SCRIPTS --> RENDER

    RENDER -->|✅ Markdown → LaTeX → PDF| VALIDATE[Stage 04:<br/>Output Validation]
    RENDER -->|❌ LaTeX errors| FAIL

    VALIDATE -->|✅ Quality checks pass| COPY[Stage 05: Copy Outputs]
    VALIDATE -->|❌ Quality issues| WARN([Continue with warnings])

    COPY -->|✅ Files copied| SUCCESS([Pipeline Complete<br/>Outputs in output/])
    WARN --> SUCCESS

    COPY --> LLM{LLM Available?}
    LLM -->|✅ Ollama running| LLM_REVIEW[Stage 06: LLM Review]
    LLM -->|❌ No Ollama| SKIP_LLM[Skip LLM stages]

    LLM_REVIEW --> LLM_TRANSLATE[Stage 07: LLM Translations]
    LLM_TRANSLATE --> SUCCESS
    SKIP_LLM --> SUCCESS

    FAIL --> END([Exit with error code])

    classDef start fill:#e3f2fd,stroke:#1565c0,stroke-width:3px
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px
    classDef failure fill:#ffebee,stroke:#c62828,stroke-width:3px
    classDef process fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#4a148c,stroke-width:2px

    class START start
    class SUCCESS success
    class FAIL,END failure
    class SETUP,TESTS,ANALYSIS,EXECUTE_SCRIPTS,RENDER,VALIDATE,COPY,LLM_REVIEW,LLM_TRANSLATE process
    class ENTRY,LLM decision
```

## Script Execution Details

```mermaid
flowchart TD
    A[scripts/02_run_analysis.py<br/>Analysis Stage] --> B[Discover Scripts]
    B --> C{Find Python files<br/>in project/scripts/}

    C -->|✅ Scripts found| D[Sort by filename<br/>in projects/{name}/scripts/]
    C -->|❌ No scripts| E[Continue to rendering]

    D --> F[Execute each script<br/>in order]
    F --> G{Execution successful?}

    G -->|✅ Success| H[Collect stdout outputs<br/>Capture file paths]
    G -->|❌ Failed| I[Log error<br/>Continue with others]

    H --> J[Validate outputs exist]
    I --> J

    J --> K{Feedback to<br/>validation stage}
    E --> K

    K --> L[scripts/04_validate_output.py<br/>Validation Stage]
    L --> M[Check PDF integrity]
    L --> N[Verify figure references]
    L --> O[Validate markdown links]

    classDef discovery fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef execution fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef validation fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef error fill:#ffebee,stroke:#c62828,stroke-width:2px

    class A,B,C,D discovery
    class F,G,H,I,J execution
    class L,M,N,O validation
    class K error
```

**Execution Flow:**
1. **Entry Points** → Choose interactive (`run.sh`) or programmatic (`execute_pipeline.py`)
2. **Environment Setup** → Validate system requirements and dependencies
3. **Test Execution** → Run test suites (infrastructure + project)
4. **Analysis Discovery** → Find and execute project-specific scripts
5. **Manuscript Rendering** → Convert markdown to professional PDFs
6. **Quality Validation** → Verify output integrity and academic standards
7. **Output Delivery** → Copy final deliverables to accessible locations

**Key Relationships:**
- **Generic Orchestrators** (`scripts/`) coordinate pipeline stages
- **Project Code** (`project/`) implements domain-specific logic
- **Outputs** are generated and validated throughout the pipeline

```
Main Entry Point (run.sh):
  → Interactive Menu → Choose Manuscript Operations

Manuscript Operations (run.sh):
Menu Option 8 (--pipeline) → Full Pipeline:
  STAGE 0: Clean Output Directories
    └─ PASS → STAGE 1
  STAGE 1: Setup Environment
    └─ PASS → STAGE 2
  STAGE 2: Infrastructure Tests (60%+ coverage)
    └─ PASS → STAGE 3
  STAGE 3: Project Tests (90%+ coverage)
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

## Generic vs Project-Specific

### Root Scripts (Generic)
- Coordinate build pipeline
- Discover `project/scripts/`
- Handle stages (setup, test, analysis, pdf, validate)
- Work with ANY project

### Project Scripts (Specific)
- Implement domain-specific analysis
- Import from `projects/{name}/src/`
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
  └─ 06_llm_review.py → LLM manuscript review (optional)

projects/{name}/scripts/ (Project-Specific)
  ├─ analysis_pipeline.py → Your analysis
  └─ example_figure.py → Your figures
```

## Shared Utilities

`run.sh` sources shared utilities from `scripts/bash_utils.sh`:
- Color codes and formatting
- Logging functions (log_header, log_success, log_error, etc.)
- Utility functions (format_duration, get_elapsed_time, parse_choice_sequence)
- File logging functions

This follows the thin orchestrator pattern: utilities in source, scripts orchestrate.

## Deploying with Different Project

1. Create new `projects/{name}/` with your research
2. Add code to `projects/{name}/src/`
3. Add scripts to `projects/{name}/scripts/`
4. Run `./run.sh` - it auto-discovers your code

Root entry points work with **ANY** project following this structure.

## See Also

- [`AGENTS.md`](AGENTS.md) - Complete documentation
- [`../RUN_GUIDE.md`](../RUN_GUIDE.md) - Unified runner guide
- [`projects/code_project/scripts/README.md`](../projects/code_project/scripts/README.md) - Project scripts guide
- [`../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Pattern details
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation
