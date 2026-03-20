# Infrastructure Module Reference

This section provides a detailed reference for all ${module_count} infrastructure subpackages, documenting their purpose, key classes, public API, and integration points within the pipeline. The infrastructure layer comprises ~${total_infra_python_files} Python modules validated by ${infra_test_count_approx} tests. Each subpackage follows the Documentation Duality standard: every module directory contains both an `AGENTS.md` machine-readable specification and a `README.md` human-readable guide.

## `infrastructure.core` (28 modules)

**Purpose**: Foundation utilities providing the bedrock services consumed by all other modules and all projects.

**Key Components**:

| Component | Purpose |
|-----------|---------|
| `logging_utils.py` | Structured logger factory (`get_logger`) with colored console output and file rotation |
| `config_loader.py` | YAML config parser (`load_config`) with schema validation and default merging |
| `exceptions.py` | Exception hierarchy: `TemplateError` → `ConfigurationError`, `ValidationError`, `BuildError` |
| `environment.py` | Environment detection, Python command resolution, `PYTHONPATH` management |
| `progress.py` | `ProgressBar` for pipeline stage progress reporting |
| `checkpoint.py` | `CheckpointManager` for resumable pipeline execution |
| `health.py` | `SystemHealthChecker` for pre-pipeline dependency validation |
| `performance.py` | `monitor_performance` context manager for timing and memory tracking |
| `_optional_deps.py` | Lazy loading of optional dependencies (`psutil`, `reportlab`) |

**Integration**: Every module and script imports from `core`. The exception hierarchy is used for pipeline flow control—`ValidationError` triggers stage failure, `BuildError` halts the entire pipeline. The lazy loader in `_optional_deps.py` separates core imports from optional subpackages, preventing cascading import failures in environments with partial dependency sets.

## `infrastructure.documentation` (6 modules)

**Purpose**: Documentation management, figure registration, and API glossary generation.

**Key Components**:

| Component | Purpose |
|-----------|---------|
| `figure_manager.py` | `FigureManager` — maintains a JSON registry of all generated figures with captions, labels, and generation metadata |
| `glossary_gen.py` | `generate_glossary` — programmatic API glossary extraction from Python source files |

**Integration**: Called by project scripts during Stage 02 to register figures for automated cross-referencing in the manuscript. The glossary generator supports the Documentation Duality standard by extracting docstrings and function signatures.

## `infrastructure.llm` (30 modules)

**Purpose**: Local LLM integration for automated manuscript review, translation, and literature search.

**Key Components**:

| Component | Purpose |
|-----------|---------|
| `review.py` | Executive summary and quality review generation |
| `translation.py` | Abstract translation into configured target languages |
| `client.py` | Ollama HTTP client with retry logic and timeout management |
| `literature/` | Literature search subpackage with semantic query support |
| `templates/` | Prompt templates for structured LLM interactions |

**Integration**: Invoked during Stage 06. Requires a running Ollama instance. Gracefully degrades when unavailable. The literature search subpackage enables programmatic discovery of related work during manuscript preparation.

## `infrastructure.project` (2 modules)

**Purpose**: Project discovery and workspace management.

**Key Components**:

| Component | Purpose |
|-----------|---------|
| `discovery.py` | `_discover_project` — finds valid project directories by scanning for `manuscript/config.yaml` |
| `workspace.py` | Workspace initialization and cleanup utilities |

**Integration**: Used by `execute_pipeline.py` and `run.sh` to identify which projects can be built. The discovery algorithm enforces the Standalone Project Paradigm: a directory is a valid project if and only if it contains `manuscript/config.yaml`.

## `infrastructure.publishing` (9 modules)

**Purpose**: Academic publishing metadata and citation generation.

**Key Components**:

| Component | Purpose |
|-----------|---------|
| `models.py` | `PublicationMetadata` dataclass with direct attribute access and dynamic `getattr` fallback |
| `citations.py` | `generate_citation_apa`, `generate_citation_bibtex`, `generate_citation_mla` |
| `zenodo.py` | Zenodo API integration for DOI registration |

**Integration**: Used during Stage 02 by analysis scripts to extract publishable metadata from results. Citation generators produce correctly formatted strings from `config.yaml` metadata.

## `infrastructure.rendering` (12 modules)

**Purpose**: Multi-format document rendering (Markdown → LaTeX → PDF, HTML reports).

**Key Components**:

| Component | Purpose |
|-----------|---------|
| `pandoc.py` | Pandoc invocation with custom filters and metadata injection |
| `latex.py` | XeLaTeX compilation with auxiliary file management and stale `.aux` cleanup |
| `pdf_builder.py` | End-to-end PDF construction orchestrating Pandoc and XeLaTeX |
| `html_report.py` | HTML executive report generation |
| `markdown_report.py` | Markdown-format report generation |

**Integration**: Core of Stage 03. Reads `manuscript/*.md` and `config.yaml`, produces `output/<project>.pdf`. The auxiliary file cleanup resolves a known rendering hazard where stale `.aux` files cause "Division by 0" LaTeX errors.

## `infrastructure.reporting` (14 modules)

**Purpose**: Pipeline reporting, test result aggregation, and coverage analysis.

**Key Components**:

| Component | Purpose |
|-----------|---------|
| `coverage_parser.py` | Cascading parse strategies for pytest output: `_parse_failures_section`, `_parse_failures_verbose`, `_parse_failures_short`, `_parse_failures_timeout`, `_parse_failures_fallback` |
| `report_generator.py` | Executive report generation in JSON and Markdown |
| `statistics.py` | `collect_output_statistics` — enumerates output directory contents |

**Integration**: Used during Stages 01, 04, and 07 for test result parsing, validation reporting, and executive summary generation. The cascading parser handles all pytest output formats robustly, falling through five strategies to ensure no test failure is silently missed.

## `infrastructure.scientific` (6 modules)

**Purpose**: Scientific computing utilities for numerical analysis and benchmarking.

**Key Components**:

| Component | Purpose |
|-----------|---------|
| `stability.py` | `check_numerical_stability` — tests functions for NaN/Inf behavior across input ranges |
| `benchmarking.py` | `benchmark_function` — measures execution time and memory usage |
| `simulation.py` | Scientific simulation framework with parameter sweeps |

**Integration**: Used by `code_project`'s analysis scripts during Stage 02 for algorithm validation. The stability checker is critical for ensuring that numerical results are reproducible across different floating-point environments.

## `infrastructure.steganography` (8 modules)

**Purpose**: Cryptographic watermarking and provenance embedding for PDF artifacts.

**Key Components**:

| Component | Purpose |
|-----------|---------|
| `metadata.py` | `inject_pdf_metadata` — embeds XMP metadata and PDF Info dictionary entries |
| `config.py` | `DocumentMetadata` dataclass for steganography configuration |
| `overlay.py` | Alpha-channel text overlay with build timestamp and commit hash |
| `qr.py` | QR code generation and injection into PDF pages |
| `hash.py` | SHA-256/SHA-512 hash computation for tamper detection |

**Integration**: Invoked by `secure_run.sh` after the main pipeline completes. Reads the rendered PDF and produces a steganographically watermarked copy with an accompanying `.hashes.json` manifest.

## `infrastructure.validation` (22 modules)

**Purpose**: Quality assurance and integrity verification for all pipeline artifacts.

**Key Components**:

| Component | Purpose |
|-----------|---------|
| `pdf_validator.py` | PDF structural integrity checking (xref table, trailer, page count) |
| `markdown_validator.py` | Markdown linting (heading hierarchy, link integrity, orphan references) |
| `integrity.py` | `verify_output_integrity` — comprehensive output directory validation |
| `cli.py` | Command-line interface for standalone validation operations |

**Integration**: Core of Stage 04. Validates all generated artifacts before they are finalized. The validation module is the most module-dense package (22 files), reflecting the breadth of integrity checks required across PDF, Markdown, image, and manifest formats.

## Infrastructure Maturity Summary

The twelve-module architecture achieves 100% Tier 1–2 documentation coverage (`AGENTS.md`, `README.md`) with Tier-3 `SKILL.md` skill descriptors across all 10 active subpackages, 83%+ aggregate test coverage (exceeding the 60% infrastructure threshold by a wide margin), and zero mock-object violations. Every active module exposes a machine-readable skill descriptor aligned with the Model Context Protocol [@anthropic2024mcp], making the infrastructure layer not merely documented but *programmatically discoverable*—a prerequisite for the agentic research automation paradigm described in the [Documentation Duality](#documentation-duality-and-the-agentic-skill-architecture) and [AI Collaboration](#the-ai-collaboration-model) sections. The combination of high coverage, complete documentation, and protocol-aligned discoverability positions `template/`'s infrastructure as deployment-ready research software rather than a prototype, satisfying the executability and metadata quality indicators defined by Garijo et al.'s FAIRsoft evaluator [@garijo2024fairsoft].
