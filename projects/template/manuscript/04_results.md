# Results

The Docxology Template was evaluated through a multi-project pipeline execution, measuring test coverage, pipeline timing, output integrity, and steganographic performance across three heterogeneous exemplar projects.

## Multi-Project Pipeline Execution

All three projects were executed through the full eight-stage pipeline using the `run.sh` interactive orchestrator with the "all projects core (fast)" configuration, which skips infrastructure tests and LLM review to isolate project-level performance.

| Project | Stages | Duration | Tests | Coverage |
|---------|--------|----------|-------|----------|
| `code_project` | 7 | 43.4s | 58/58 | 96.6% |
| `cognitive_case_diagrams` | 7 | 56.0s | 257/257 | ~96% |
| `template` | 7 | 22.6s | 36/36 | 90%+ |

**Overall success rate**: 100.0% (3/3 projects)
**Total pipeline duration**: 121.9s
**Average per project**: 40.6s

The `cognitive_case_diagrams` project, with its 257 tests and 25+ programmatically generated figures via 17 DisCoPy renderers, represents the most computationally intensive exemplar—yet completes in under one minute.

## Infrastructure Test Suite

The infrastructure layer is validated by a separate test suite of significant scale:

| Metric | Value |
|--------|-------|
| Test files | 148 |
| Total tests | 3,053 |
| Infrastructure coverage threshold | 60% (achieved: 83%+) |
| Zero-mock violations | 0 |
| Real filesystem operations | ✓ |
| Real subprocess invocations | ✓ |

This test suite exercises all ten infrastructure modules, including the rendering pipeline (Pandoc/XeLaTeX integration), steganographic operations (alpha-channel overlay, QR injection), and LLM client interactions (real HTTP calls to Ollama).

## Infrastructure Module Inventory

The introspection module (`template.introspection`) programmatically enumerates the infrastructure layer, confirming the following module distribution:

| Module | Python Files | Has AGENTS.md | Has README.md | Key Exports |
|--------|:-----------:|:-------------:|:-------------:|-------------|
| `core` | 28 | ✓ | ✓ | `get_logger`, `load_config`, `TemplateError` |
| `documentation` | 6 | ✓ | ✓ | `FigureManager`, `generate_glossary` |
| `llm` | 30 | ✓ | ✓ | LLM review, literature search, translation |
| `project` | 2 | ✓ | ✓ | `_discover_project`, workspace management |
| `publishing` | 9 | ✓ | ✓ | Citation generation (APA, BibTeX, MLA), Zenodo |
| `rendering` | 12 | ✓ | ✓ | PDF rendering, Pandoc filters, HTML reports |
| `reporting` | 14 | ✓ | ✓ | Coverage parsing, executive reports |
| `scientific` | 6 | ✓ | ✓ | `check_numerical_stability`, `benchmark_function` |
| `steganography` | 8 | ✓ | ✓ | Metadata injection, QR overlays, hashing |
| `validation` | 22 | ✓ | ✓ | PDF validation, Markdown checking, CLI |
| **Total** | **137** | **10/10** | **10/10** | |

All ten modules have complete documentation coverage (both `AGENTS.md` and `README.md`), confirming the Documentation Duality standard.

## Pipeline Stage Execution

The eight pipeline stages execute sequentially with strict error propagation:

| Stage | Script | Responsibility | Failure Mode |
|-------|--------|---------------|--------------|
| 00 | `00_setup_environment.py` | Environment validation | Hard fail |
| 01 | `01_run_tests.py` | Test execution + coverage | Configurable tolerance |
| 02 | `02_run_analysis.py` | Script invocation | Hard fail |
| 03 | `03_render_pdf.py` | Pandoc + XeLaTeX | Hard fail |
| 04 | `04_validate_output.py` | PDF integrity | Warning + report |
| 05 | `05_copy_outputs.py` | Output organization | Soft fail |
| 06 | `06_llm_review.py` | LLM-assisted review | Skippable |
| 07 | `07_generate_executive_report.py` | Report aggregation | Soft fail |

## Steganographic Performance

The steganography subsystem (`infrastructure.steganography`) was benchmarked across all three project PDFs:

| Project | Pages | Metadata | SHA-256 | Overlay | QR Code | Total |
|---------|:-----:|:--------:|:-------:|:-------:|:-------:|:-----:|
| `code_project` | 20 | < 0.3s | < 0.05s | < 0.8s | < 0.4s | < 1.5s |
| `cognitive_case_diagrams` | 77 | < 0.3s | < 0.05s | < 2.0s | < 0.4s | < 2.8s |
| `template` | 5 | < 0.3s | < 0.05s | < 0.3s | < 0.4s | < 1.0s |

The steganographic watermark survives standard PDF operations (viewing, printing) but is detectable through pixel-level analysis of the alpha channel. Performance scales linearly with page count, dominated by the alpha-channel overlay phase.

## Self-Referential Analysis

This manuscript is itself a product of the template pipeline, demonstrating its self-referential capability. The `template` project's `src/template/introspection.py` module programmatically analyzes the repository and generates three architecture figures:

![Two-Layer Architecture Overview](figures/architecture_overview.png)
*Figure 1: The Two-Layer Architecture separating infrastructure modules from project workspaces.*

![Pipeline Stage Flow](figures/pipeline_stages.png)
*Figure 2: The eight-stage build pipeline from environment setup through executive reporting.*

![Infrastructure Module Inventory](figures/module_inventory.png)
*Figure 3: Python file count per infrastructure module, with documentation status indicators.*

## Comparative Feature Analysis

To contextualize the Docxology Template's contributions, we compare its feature set against established tools:

| Feature | Docxology | Snakemake | Nextflow | CWL | Quarto | Jupyter Book |
|---------|:---------:|:---------:|:--------:|:---:|:------:|:------------:|
| Pipeline orchestration | ✓ | ✓ | ✓ | ✓ | — | — |
| Manuscript rendering | ✓ | — | — | — | ✓ | ✓ |
| Testing enforcement | ✓ | — | — | — | — | — |
| Coverage thresholds | ✓ | — | — | — | — | — |
| Cryptographic provenance | ✓ | — | — | — | — | — |
| Multi-project management | ✓ | — | — | — | — | — |
| AI-agent documentation | ✓ | — | — | — | — | — |
| Interactive TUI | ✓ | — | — | — | — | — |
| Zero-mock policy | ✓ | — | — | — | — | — |

The Docxology Template is, to our knowledge, the only open-source system that integrates all nine capabilities within a single cohesive architecture.

## Test Quality Metrics

The Zero-Mock testing policy produces measurably higher-fidelity tests:

- **Zero mock objects** across all test suites (verified by automated scanning for `unittest.mock`, `MagicMock`, and `patch` imports).
- **Real filesystem operations**: Tests create, read, validate, and delete actual files in temporary directories.
- **Real subprocess calls**: Pipeline stage tests invoke actual `pytest`, `pandoc`, and `xelatex` subprocesses.
- **Marker-based skip logic**: Tests requiring optional services (Ollama, network) use `@pytest.mark.requires_ollama` for graceful degradation.
- **Categorical axiom verification**: The `cognitive_case_diagrams` project tests validate identity morphisms, composition, weight multiplication, and the triangle inequality on real enriched category objects.
