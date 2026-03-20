# Results

`template/` was evaluated through a multi-project pipeline execution, measuring test coverage, pipeline timing, output integrity, and steganographic performance across three heterogeneous exemplar projects.

## Multi-Project Pipeline Execution

All three projects were executed through the full eight-stage pipeline using the `run.sh` interactive orchestrator with the "all projects core (fast)" configuration, which skips infrastructure tests and LLM review to isolate project-level performance.

| Project | Stages | Duration | Tests | Coverage |
|---------|--------|----------|-------|----------|
| `code_project` | 7 | ~40s | 39/39 | 90%+ |
| `act_inf_metaanalysis` | 7 | ~60s | 505/505 | 90%+ |
| `template` | 7 | ~25s | 65/65 | 90%+ |

**Overall success rate**: 100.0% (3/3 projects)
**Total pipeline duration**: ~125s
**Average per project**: ~42s

*Timing measured on Apple M-series hardware with SSD; analysis scripts use fixed random seeds. Figures are representative; actual duration scales with system load, test suite size, and manuscript complexity.*

The `act_inf_metaanalysis` project, with its 505 tests and programmatically generated figures, represents the most computationally intensive exemplar—yet completes in under one minute, confirming that the Zero-Mock policy's real-method overhead remains tractable at this scale.

## Infrastructure Test Suite

The infrastructure layer is validated by a separate test suite of significant scale:

| Metric | Value |
|--------|-------|
| Test files | 163+ |
| Total tests | ~3,083 |
| Infrastructure coverage threshold | 60% (achieved: 83%+) |
| Zero-mock violations | 0 |
| Real filesystem operations | ✓ |
| Real subprocess invocations | ✓ |

This test suite exercises all twelve infrastructure modules, including the rendering pipeline (Pandoc/XeLaTeX integration), steganographic operations (alpha-channel overlay, QR injection), and LLM client interactions (real HTTP calls to Ollama).

## Infrastructure Module Inventory

The introspection module (`template.introspection`) programmatically enumerates the infrastructure layer, confirming the following module distribution:

| Module | Python Files | Key Exports |
|--------|:-----------:|-------------|
| `core` | 28 | `get_logger`, `load_config`, `TemplateError` |
| `documentation` | 6 | `FigureManager`, `generate_glossary` |
| `llm` | 30 | LLM review, literature search, translation |
| `project` | 2 | `discover_projects`, workspace management |
| `publishing` | 9 | Citation generation (APA, BibTeX, MLA), Zenodo |
| `rendering` | 12 | PDF rendering, Pandoc filters, HTML reports |
| `reporting` | 14 | Coverage parsing, executive reports |
| `scientific` | 6 | `check_numerical_stability`, `benchmark_function` |
| `steganography` | 8 | Metadata injection, QR overlays, hashing |
| `validation` | 22 | PDF validation, Markdown checking, CLI |
| (+ config, docker) | — | Configuration, containerization |
| **Total** | **~150** | |

*The ~150 figure includes approximately 13 additional modules in the `config/` and `docker/` subpackages (configuration schemas and containerization utilities) not enumerated individually above.*

All 12 modules have 100% documentation coverage at Tiers 1–2 (`AGENTS.md`, `README.md`); the 10 active subpackages additionally carry `SKILL.md` for Tier-3 agentic skill discovery. This places `template/` among the first research software frameworks to implement an MCP-aligned skill layer [@anthropic2024mcp] across its infrastructure stack.

## Agentic Skill Documentation Coverage

The three-tier [skill protocol](#documentation-duality-and-the-agentic-skill-architecture) achieves complete coverage across all infrastructure modules:

| Documentation Layer | Files | Coverage |
|--------------------|:-----:|:---------:|
| System (`CLAUDE.md`) | 1 | 100% |
| Structural (`AGENTS.md`) | 12+ per-directory | 100% |
| Skill (`SKILL.md`) | 12 modules | 100% |
| PAI (`PAI.md`) | 1 (infrastructure-level) | — |
| Human (`README.md`) | 12+ per-directory | 100% |

This four-layer coverage creates 12 fully described, MCP-mappable tool endpoints that a sufficiently capable agent could invoke without any source-code access. The aggregate documentation footprint (145+ files) represents a deliberate engineering investment: each documentation file is not commentary but a specification, enforcing architectural constraints through structured natural language [@lau2025aicoding].

## Pipeline Stage Execution

The eight pipeline stages execute sequentially with strict error propagation:

| Stage | Script | Responsibility | Failure Mode |
|---|------------|---------------|--------------|
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
| `code_project` | ~20 | < 0.3s | < 0.05s | < 0.8s | < 0.4s | < 1.5s |
| `act_inf_metaanalysis` | ~80 | < 0.3s | < 0.05s | < 2.0s | < 0.4s | < 2.8s |
| `template` | ~30 | < 0.3s | < 0.05s | < 0.9s | < 0.4s | < 1.6s |

*Performance measured on Apple M-series hardware with SSD, single-threaded execution. Values represent wall-clock time; actual performance scales with PDF page count and system I/O.*

The steganographic watermark survives standard PDF operations (viewing, printing) but is detectable through pixel-level analysis of the alpha channel. Performance scales linearly with page count, dominated by the alpha-channel overlay phase.

## Self-Referential Analysis

This manuscript is itself a product of the `template/` pipeline, demonstrating its self-productive capability. The `template` project's `src/template/introspection.py` module programmatically analyzes the repository and generates four architecture figures, all presented below. The numeric values in the tables above—module counts, test counts, file totals—were not typed by hand but injected at build time by the `${variable}` substitution system described in the Methods, reading live metrics from the repository's own structure. The figures below were rendered by the same `architecture_viz.py` module whose font-size constraints are specified in the [Quality Assurance](#quality-assurance) section. In this way, the manuscript does not merely *describe* but *enacts* the pipeline it documents.

![Two-Layer Architecture Overview](figures/architecture_overview.png)
**Figure 1**: Two-Layer Architecture separating the generic, reusable infrastructure layer (12 subpackages, upper panel) from domain-specific project workspaces (lower panel), connected by the eight-stage pipeline. Each module box displays its Python file count and a documentation badge (A = `AGENTS.md`, R = `README.md`, S = `SKILL.md`, P = `PAI.md`; a dot `·` means absent). Project boxes show chapter and test counts. All labels are drawn from live repository introspection at render time; font sizes follow the 16 pt [accessibility floor](#visualization-standards).

![Pipeline Stage Flow](figures/pipeline_stages.png)
**Figure 2**: Sequential eight-stage build pipeline (Stage 00–07, plus a pre-step clean stage). Viridis colour progression encodes stage ordering. Each box includes a short description of the stage's primary action. Stage names and descriptions are generated from `PipelineStage` objects returned by `report.pipeline_stages`, ensuring the figure reflects the actual pipeline.

![Infrastructure Module Inventory](figures/module_inventory.png)
**Figure 3**: Python source-file count per infrastructure subpackage, sorted descending. Bar colour intensity scales with file count. Documentation badges `[ARSP]` appear to the right of each count (A = `AGENTS.md`, R = `README.md`, S = `SKILL.md`, P = `PAI.md`; a dot `·` means absent). Total file count is annotated at chart bottom.

## Comparative Feature Analysis

To contextualize `template/`'s contributions, we compare its feature set against nine established tools. The full capability matrix (14 capabilities × 10 tools) is rendered as a colour-coded heatmap in Figure 4 and reproduced as a text table in Appendix F. Rows are grouped into three categories — *Core Pipeline*, *Quality & Security*, and *Ecosystem* — separated by horizontal dividers.

![Comparative Feature Analysis Heatmap](figures/comparative_feature_matrix.png)
**Figure 4**: Comparative feature matrix (14 capabilities × 10 tools). Colour scale: green **✓** = full native support; yellow **◐** = partial / plugin-based; red **—** = absent. The `template/` column is outlined in blue. Capabilities are grouped into *Core Pipeline* (rows 1–2), *Quality & Security* (rows 3–8), and *Ecosystem* (rows 9–14). `template/` is, to our knowledge, the only open-source system that integrates all twelve unique capabilities (pipeline orchestration through zero-mock policy, plus optional containerization) within a single cohesive architecture. Snakemake, Nextflow, and CWL provide superior distributed execution support not yet in `template/`.

¹ Nextflow 25.04.0: data-lineage provenance tracking at build level, not document level.
² DVC: content-addressed artifact versioning via object store.
³ DVC: remote storage integration (S3, GCS, Azure) without native distributed compute orchestration.

## Test Quality Metrics

The Zero-Mock testing policy produces measurably higher-fidelity tests:

- **Zero mock objects** across all test suites (verified by automated scanning for `unittest.mock`, `MagicMock`, and `patch` imports).
- **Real filesystem operations**: Tests create, read, validate, and delete actual files in temporary directories.
- **Real subprocess calls**: Pipeline stage tests invoke actual `pytest`, `pandoc`, and `xelatex` subprocesses.
- **Marker-based skip logic**: Tests requiring optional services (Ollama, network) use `@pytest.mark.requires_ollama` for graceful degradation.
- **Categorical axiom verification**: The `cognitive_case_diagrams` project tests validate identity morphisms, composition, weight multiplication, and the triangle inequality on real enriched category objects.
