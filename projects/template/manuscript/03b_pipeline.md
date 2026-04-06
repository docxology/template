## The Ten-Stage DAG Pipeline

The build pipeline is orchestrated by `scripts/execute_pipeline.py`, which invokes numbered stage scripts sequentially. Each stage is a standalone Python script that exits cleanly or raises an exception to halt the pipeline.

### Stage 00: Environment Setup (`00_setup_environment.py`)

Validates the Python environment, checks dependency availability, creates output directories, and initializes logging. Ensures `PYTHONPATH` includes both the repository root and the active project's `src/` directory.

### Stage 01: Test Execution (`01_run_tests.py`)

Executes pytest with coverage measurement against both infrastructure tests (`tests/`) and project tests (`projects/<name>/tests/`). Enforces configurable failure tolerances:

- `max_infra_test_failures`: Maximum permitted infrastructure test failures (typically 3).
- `max_project_test_failures`: Maximum permitted project test failures (typically 0).
- Coverage thresholds: 60% infrastructure, 90% project.

The stage generates coverage JSON files for downstream reporting and saves test results in both JSON and Markdown formats. The infrastructure test suite alone contains ~${infra_test_count_approx} tests across ${infra_test_file_count}+ test files.

### Stage 02: Analysis Execution (`02_run_analysis.py`)

Discovers and executes all Python scripts in `projects/<name>/scripts/` in alphabetical order. Each script is expected to generate figures in `output/figures/` and data in `output/data/`. Scripts follow the Thin Orchestrator pattern, importing logic from `src/` modules. For example, the `cognitive_case_diagrams` project generates 25+ programmatic figures via 17 DisCoPy renderers during this stage.

### Stage 03: PDF Rendering (`03_render_pdf.py`)

Compiles Markdown manuscript chapters into a unified PDF via a three-phase rendering process:

1. **Pandoc Markdown→LaTeX**: Converts each `manuscript/*.md` file into LaTeX, injecting metadata from `config.yaml` (title, authors, affiliations, DOI).
2. **XeLaTeX Compilation**: Runs `xelatex` with `biber` for bibliography processing. Handles the `aux`→`bbl`→`aux` cycle automatically, with cleanup of stale auxiliary files to prevent corruption.
3. **Post-processing**: Applies font embedding verification and PDF/A compliance checks.

### Stage 04: Output Validation (`04_validate_output.py`)

Validates the structural integrity of all generated artifacts:

- PDF cross-reference table and trailer verification.
- Figure file existence and minimum size checking.
- Manifest generation with SHA-256 hashes for all output files.
- Markdown structural validation (heading hierarchy, link integrity).

### Stage 05: Output Organization (`05_copy_outputs.py`)

Copies finalized artifacts to standardized output locations and generates the pipeline completion manifest.

### Stage 06: LLM Review (`06_llm_review.py`)

Invokes a local LLM (via Ollama) to generate:

- **Executive summary**: A 1-page high-level overview of the manuscript.
- **Quality review**: Detailed feedback on structure, citations, and argumentation.
- **Translations** (optional): Machine translations of the abstract into configured target languages.

This stage is skippable via configuration and gracefully handles Ollama unavailability.

### Stage 07: Executive Report (`07_generate_executive_report.py`)

Aggregates all pipeline metrics—test results, coverage percentages, rendering duration, validation status, LLM review scores—into a comprehensive executive report in both JSON and Markdown formats.

## The Interactive Orchestrators

### `run.sh`: The Standard Orchestrator

The primary user interface is `run.sh`, a Bash TUI (text user interface) that presents an interactive menu for pipeline execution. Features include:

- **Project selection**: Execute a single project or all discovered projects.
- **Mode selection**: Fast (skip infra tests + LLM), Core (skip LLM only), Full (all stages).
- **Non-interactive mode**: `./run.sh --pipeline --project all --core-only` for CI/CD integration.
- **Real-time progress**: Stage timing and status indicators.

### `secure_run.sh`: The Steganographic Superset

The `secure_run.sh` orchestrator is a strict superset of `run.sh`: it executes the standard ten-stage DAG pipeline and then appends steganographic post-processing. For each rendered PDF, it applies metadata injection, cryptographic hashing, alpha-channel text overlay, and QR code injection, producing a provenance-embedded output alongside the original. It supports the same project selection and mode flags as `run.sh`.
