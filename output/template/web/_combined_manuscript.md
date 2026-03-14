# Abstract

The Docxology Template is a modular, high-integrity research environment that unifies computational experimentation, academic manuscript production, and cryptographic provenance verification within a single reproducible pipeline. Built on a Two-Layer Architecture separating ten reusable infrastructure subpackages—totaling 137 Python modules and validated by over 3,000 infrastructure tests—from self-contained project workspaces, the system orchestrates an eight-stage build pipeline that progresses from environment sanitization through test execution, analysis script invocation, Pandoc/XeLaTeX rendering, SHA-256/512 hashing with alpha-channel steganographic watermarking, structural PDF validation, and LLM-assisted review to produce peer-review-ready manuscripts with embedded tamper-evident provenance. Unlike existing workflow managers (Snakemake, Nextflow, CWL) that focus on computational pipeline orchestration, and literate programming tools (Quarto, Jupyter Book, R Markdown) that focus on document rendering, the Docxology Template integrates both concerns with automated testing, documentation generation, and cryptographic provenance in a single coherent system. We enforce a Zero-Mock testing policy where pipeline advancement is contingent on 90% project-level and 60% infrastructure-level coverage thresholds, using exclusively real filesystem operations, subprocess invocations, and network calls—no mock objects, no test doubles. A Documentation Duality standard equips every directory with both human-readable `README.md` files and machine-readable `AGENTS.md` files optimized for AI coding assistants, enabling a novel human–AI collaborative development model. We demonstrate the system's scalability across three heterogeneous exemplar projects—a gradient descent optimization study (58 tests, 96.6% coverage), a categorical linguistics manuscript with 25+ DisCoPy-generated figures (257 tests, ~96% coverage), and this self-referential architectural analysis (36 tests)—achieving 100% pipeline success rates. The Standalone Project Paradigm enables researchers to add arbitrarily many independent studies without modifying the infrastructure layer, while the Thin Orchestrator pattern ensures that all domain logic resides in testable `src/` modules and scripts serve only as stateless wiring between infrastructure services and project-specific code.



---



# Introduction

## The Reproducibility Crisis and Its Structural Roots

The "reproducibility crisis" in computational and biological sciences is not merely a cultural failure but a structural one. When research papers are divorced from the code that generated their figures, when datasets are shared as unlabeled archives, and when build processes exist only as tribal knowledge in a graduate student's shell history, the conditions for irreproducibility are baked into the workflow itself. A 2016 *Nature* survey of 1,576 researchers found that 70% had tried and failed to reproduce another scientist's experiments, and more than half had failed to reproduce their own [@baker2016reproducibility]. The economic cost is staggering: Freedman et al. estimate that the biomedical industry alone loses \$28 billion annually to irreproducible preclinical research [@freedman2015economics].

The root cause is fragmentation. A typical research project scatters its artifacts across disconnected tools: LaTeX editors for prose, Jupyter notebooks for analysis, ad-hoc shell scripts for figure generation, and manual copy-paste for integrating results into manuscripts. Each boundary between tools is a potential locus of desynchronization. The version of the figure in the PDF may not match the version of the code that ostensibly generated it. The test suite, if it exists at all, likely tests the code in isolation from the rendering pipeline. Peng [@peng2011reproducible] argues that reproducibility in computational science requires, at minimum, that the data and code underlying a published result be available for independent verification—yet the tools for enforcing this standard remain ad hoc. Indeed, even the terminology is fractured: Barba [@barba2018terminologies] documents how "reproducibility," "replicability," and "repeatability" carry conflicting definitions across disciplines, undermining cross-field standards.

## Related Work

Gentleman and Temple Lang [@gentleman2007research] introduced the concept of a *research compendium*—a single unit of scholarly communication bundling code, data, and narrative. This vision has driven two decades of tooling, which can be grouped into four categories: workflow managers, literate programming systems, containerization approaches, and best-practice frameworks.

### Workflow Managers

**Snakemake** [@koster2012snakemake] uses a rule-based, Python-derived DSL to specify computational workflows as directed acyclic graphs of file-producing steps. It supports containerized execution via Conda and Singularity environments. However, Snakemake focuses exclusively on computational pipeline orchestration and does not integrate manuscript rendering, testing enforcement, or provenance watermarking.

**Nextflow** [@ditommaso2017nextflow] employs a dataflow programming paradigm with native support for container-based execution across heterogeneous computing environments (local, SLURM, AWS). Like Snakemake, Nextflow excels at bioinformatics pipeline parallelism but does not address manuscript production, document integrity, or the testing–publication coupling that characterizes research reproducibility.

**CWL** (Common Workflow Language) [@amstutz2016cwl] provides a portable, YAML-based standard for describing computational workflows and their dependencies. Its strength lies in interoperability across execution engines (cwltool, Toil, Arvados), but it requires external tooling for manuscript generation and offers no built-in testing or provenance framework.

### Literate Programming and Publication Tools

Knuth's literate programming [@knuth1984literate] established the principle that programs should be authored as documents intended for human comprehension. Schulte et al. [@schulte2012multilanguage] extended this to multi-language computing environments (Org-mode), demonstrating that literate programming could span languages and output formats.

**Quarto** [@allaire2024quarto] extends the R Markdown tradition to support Python, Julia, and Observable, rendering to PDF, HTML, and Word. Quarto integrates code execution with document rendering, achieving a modern form of literate programming, but it does not enforce testing thresholds, manage multi-project repositories, or provide cryptographic provenance.

**Jupyter Book** [@kluyver2016jupyter] builds on Jupyter notebooks to produce publication-quality documents via Sphinx. While powerful for interactive exploration, Jupyter's notebook format introduces execution-order fragility and does not naturally support the separation of logic from orchestration that characterizes maintainable research software.

**R Markdown** [@xie2015dynamic] pioneered knitr-based dynamic documents that weave code and prose. Its ecosystem is rich but R-centric, and it lacks the multi-project management, infrastructure testing, and provenance embedding that characterize the Docxology Template.

### Containerization and Environment Capture

**Docker** [@boettiger2015docker] addresses reproducibility at the environment level—packaging operating system, libraries, and code into portable containers. While Docker solves the "works on my machine" problem, containerization is complementary to, not a replacement for, the architectural concerns addressed here: Docker does not enforce testing, embed provenance, or manage multi-project manuscript workflows.

### Best-Practice Frameworks and Data Standards

Wilson et al. [@wilson2017good] define "good enough" practices for scientific computing, emphasizing version control, testing, and documentation. Sandve et al. [@sandve2013ten] propose ten rules for reproducible computational research. Stodden et al. [@stodden2016enhancing] advocate for enhanced computational method transparency. The FAIR principles [@wilkinson2016fair]—Findable, Accessible, Interoperable, Reusable—establish a standard for data stewardship that has been widely adopted by funding agencies and journals. Barker et al. [@barker2022fair4rs] extend these principles specifically to research software via the FAIR4RS initiative, recognizing that software has distinct requirements—executability, composability, and dependency management—that data-centric FAIR does not address. Garijo et al. [@garijo2024fairsoft] operationalize FAIR4RS through the FAIRsoft evaluator, an automated assessment framework that scores research software against 17+ quality indicators including executability, metadata richness, and documentation completeness. Nüst et al. [@nust2017containerization] introduce the *executable research compendium* (ERC), extending Gentleman and Temple Lang's compendium concept with containerized, interactive reproduction environments. The W3C PROV data model [@moreau2013provdm] provides a formal vocabulary for expressing provenance records, while in-toto [@torresarias2019intoto] provides a framework for end-to-end software supply chain integrity verification. These frameworks articulate *what* reproducible research requires but do not provide integrated *how*—they lack the tooling, enforcement mechanisms, and architectural patterns that translate standards into practice.

### The Gap

Despite advances in FAIR4RS principles [@barker2022fair4rs] and automated FAIR software assessment [@garijo2024fairsoft], no existing system integrates all six concerns into a single enforced pipeline: (1) end-to-end pipeline orchestration with testing enforcement, (2) multi-format manuscript rendering, (3) cryptographic provenance embedding, (4) multi-project repository management, (5) FAIR-aligned software stewardship, and (6) AI-agent collaboration via structured documentation. FAIR4RS provides the vocabulary; the Docxology Template provides the enforcement mechanism.

## The Docxology Template: An Integrated Solution

The *Docxology Template* was conceived as a structural antidote to this fragmentation. Rather than adding reproducibility as an afterthought—a Docker container wrapping an already-disjointed workflow [@boettiger2015docker]—the template enforces integrity at the architectural level. It realizes Gentleman and Temple Lang's research compendium vision [@gentleman2007research] at repository scale, bundling code, data, tests, manuscripts, and provenance into a single, pipeline-enforced system. It stands on four primary pillars:

1. **Ergonomic Modularity**: A Two-Layer Architecture cleanly separates globally shared infrastructure (logging, rendering, validation, steganography) from project-specific logic (manuscripts, scripts, data). Ten infrastructure subpackages comprising 137 Python modules provide reusable services; projects consume them without modification.

2. **Execution Integrity**: A Zero-Mock testing policy where pipeline advancement is contingent on test passage. Infrastructure tests must achieve 60% coverage; project tests must achieve 90%. All tests use real filesystem operations, real subprocess calls, and real network connections—no mock objects, no fake services, no synthetic test doubles. Over 3,000 infrastructure tests and 350+ project tests enforce this standard.

3. **Automated Provenance**: Steganographic watermarking and cryptographic hashing are integrated directly into the rendering pipeline. Every generated PDF carries a SHA-256 fingerprint, an alpha-channel text overlay encoding the build timestamp and commit hash, and optionally a QR code linking to the repository. Provenance is not asserted by policy; it is enforced by architecture.

4. **AI-Agent Collaboration**: A Documentation Duality standard equips every directory with both `README.md` (for human researchers) and `AGENTS.md` (for AI coding assistants). Supplementary `CLAUDE.md` files provide system-level instructions. This enables a novel human–AI pair-programming workflow where AI agents can navigate, modify, and extend the codebase with full architectural awareness.

## Scope and Contributions

This paper is itself a product of the template it describes—a self-referential demonstration of the system's capabilities. Our contributions are:

- A formal description of the Two-Layer Architecture and Standalone Project Paradigm that enables N independent research projects to share infrastructure without coupling.
- A detailed specification of the eight-stage build pipeline, from environment sanitization through LLM-assisted review.
- A comparative analysis positioning the template against Snakemake, Nextflow, CWL, Quarto, and Jupyter Book.
- An empirical evaluation of the system across three heterogeneous exemplar projects, demonstrating scalability, coverage metrics, and pipeline timing.
- A security analysis of the steganographic provenance layer, including threat models and tamper-detection capabilities.
- An open-source reference implementation available at `github.com/docxology/template`.

## Paper Organization

The Methods (§2) describe the Two-Layer Architecture, Thin Orchestrator pattern, pipeline stages, and AI collaboration model. Results (§3) present quantitative metrics from multi-project execution, coverage analysis, and steganographic benchmarks. The Discussion (§4) addresses implications, limitations, and future directions. The Infrastructure Module Reference (§5) provides detailed documentation for all ten subpackages. Security and Provenance (§6) describes the steganographic and cryptographic integrity layer. Appendices (§7) provide pipeline, configuration, and comparative references.



---



# Methods

The Docxology Template's architecture is deliberately bifurcated into a globally shared `infrastructure/` layer and project-specific `projects/` silos. This section describes the four core design patterns, the eight-stage pipeline that operationalizes them, and the AI collaboration model that distinguishes this system from conventional research templates.

## The Two-Layer Architecture

The repository is organized into two strictly separated layers:

**Infrastructure Layer** (`infrastructure/`): Ten Python subpackages comprising 137 modules and providing reusable services. Each subpackage is independently importable, has its own `__init__.py`, `AGENTS.md`, and `README.md`, and exports a well-defined public API. The infrastructure layer knows nothing about any specific project—it provides generic capabilities (logging, rendering, validation, steganography) that any project may consume.

**Project Layer** (`projects/`): Self-contained research workspaces. Each project directory contains:

| Directory | Purpose |
|-----------|---------|
| `manuscript/` | Markdown chapters and `config.yaml` |
| `scripts/` | Thin orchestrator scripts (Stage 02) |
| `src/` | Project-specific Python modules |
| `tests/` | Project-specific test suite |
| `data/` | Input datasets and generated data |
| `output/` | Pipeline artifacts: PDF, figures, reports, logs |
| `docs/` | Project-specific architecture documentation |

The two layers communicate exclusively through Python imports and filesystem paths. No project modifies infrastructure code; no infrastructure module references a specific project by name (except via runtime project discovery).

## The Standalone Project Paradigm

Projects are designed to be completely self-contained. Adding a new project requires no changes to the infrastructure layer, no modifications to `pyproject.toml`, and no updates to the pipeline orchestrator. A project is automatically discovered if and only if it satisfies two conditions:

1. It exists as a subdirectory of `projects/`.
2. It contains the file `manuscript/config.yaml`.

This paradigm enables horizontal scaling: N researchers can maintain N independent projects within a single repository, sharing infrastructure without coupling. Each project declares its own testing tolerances, manuscript metadata, LLM review preferences, and rendering configuration in its `config.yaml`. The system currently hosts three exemplar projects spanning numerical optimization, category-theoretic linguistics, and meta-architectural analysis.

## The Thin Orchestrator Pattern

All scripts in `scripts/` (both infrastructure-level and project-level) follow the Thin Orchestrator pattern [@gamma1995design]:

- **No domain logic**: Scripts contain zero algorithmic implementation. They import functions from `src/` modules and wire them to infrastructure services.
- **Configuration-driven**: Behavior is parameterized by `config.yaml`, not by hardcoded values.
- **Stateless**: Scripts read inputs, call functions, write outputs. They maintain no persistent state between invocations.
- **Logged**: Every significant action is logged via `infrastructure.core.logging_utils.get_logger`.

This pattern ensures that all testable logic lives in `src/` where it is subject to the Zero-Mock testing policy, while scripts remain thin enough to be audited by visual inspection. The separation draws on the Mediator pattern from Gamma et al. [@gamma1995design], where scripts mediate between infrastructure services and project-specific code without implementing any logic of their own.

## The Eight-Stage Pipeline

The build pipeline is orchestrated by `scripts/execute_pipeline.py`, which invokes numbered stage scripts sequentially. Each stage is a standalone Python script that exits cleanly or raises an exception to halt the pipeline.

### Stage 00: Environment Setup (`00_setup_environment.py`)

Validates the Python environment, checks dependency availability, creates output directories, and initializes logging. Ensures `PYTHONPATH` includes both the repository root and the active project's `src/` directory.

### Stage 01: Test Execution (`01_run_tests.py`)

Executes pytest with coverage measurement against both infrastructure tests (`tests/`) and project tests (`projects/<name>/tests/`). Enforces configurable failure tolerances:

- `max_infra_test_failures`: Maximum permitted infrastructure test failures (typically 3).
- `max_project_test_failures`: Maximum permitted project test failures (typically 0).
- Coverage thresholds: 60% infrastructure, 90% project.

The stage generates coverage JSON files for downstream reporting and saves test results in both JSON and Markdown formats. The infrastructure test suite alone contains over 3,000 tests across 148 test files.

### Stage 02: Analysis Execution (`02_run_analysis.py`)

Discovers and executes all Python scripts in `projects/<name>/scripts/` in alphabetical order. Each script is expected to generate figures in `output/figures/` and data in `output/data/`. Scripts follow the Thin Orchestrator pattern, importing logic from `src/` modules. For example, `cognitive_case_diagrams` generates 25+ programmatic figures via 17 DisCoPy renderers during this stage.

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

The `secure_run.sh` orchestrator is a strict superset of `run.sh`: it executes the standard eight-stage pipeline and then appends steganographic post-processing. For each rendered PDF, it applies metadata injection, cryptographic hashing, alpha-channel text overlay, and QR code injection, producing a provenance-embedded output alongside the original. It supports the same project selection and mode flags as `run.sh`.

## Documentation Duality and AI Collaboration

Every directory at every level of the repository hierarchy contains two documentation files:

- **`README.md`**: Human-readable overview, quick-start instructions, and directory structure.
- **`AGENTS.md`**: Machine-readable technical specification optimized for AI coding assistants. Contains API tables, dependency graphs, implementation patterns, and architectural constraints.

This Documentation Duality standard serves two purposes. First, it ensures that both human researchers and AI agents can navigate the codebase efficiently—`AGENTS.md` files provide the structured context that language models need to make informed code modifications without hallucinating API signatures or violating architectural invariants. Second, it creates a self-documenting feedback loop: as AI agents modify the codebase, they update the corresponding `AGENTS.md` files, keeping documentation synchronized with implementation. Lau and Guo's survey of 90 AI coding assistant systems [@lau2025aicoding] identifies contextual code understanding as a primary bottleneck; the Documentation Duality standard addresses this by providing pre-structured context at every directory level.

The template additionally includes `CLAUDE.md` at the repository root, providing system-level instructions for AI coding assistants—architectural principles, testing requirements, and naming conventions that apply globally. This creates a three-tier documentation architecture: per-directory `AGENTS.md` for local context, root `CLAUDE.md` for global constraints, and `README.md` for human navigation.

### FAIR Alignment

The template's design aligns with both the original FAIR principles [@wilkinson2016fair] and the FAIR for Research Software (FAIR4RS) principles [@barker2022fair4rs] at the repository level. FAIR4RS recognizes that software has requirements distinct from data—executability, composability, and dependency management—and the template addresses each. Outputs are *Findable* through standardized directory structures, manifest files, and machine-readable metadata embedded in PDFs. They are *Accessible* via open-source distribution on GitHub, with metadata embedded in the artifact itself rather than in a separate registry. *Interoperability* is achieved through standard formats (PDF, JSON, BibTeX, YAML) and well-defined module APIs that enable cross-project composition. *Reusability* is ensured by the Standalone Project Paradigm—any project can be extracted and reused independently—and by the Documentation Duality standard, which satisfies FAIRsoft's inspectability and documentation quality indicators [@garijo2024fairsoft]. The pipeline's automated testing and coverage enforcement directly operationalize the FAIR4RS executability requirement: software that cannot pass its own test suite cannot produce publishable output.

## Quality Assurance

### Zero-Mock Testing Policy

All tests use real methods exclusively [@martin2008clean]. No `unittest.mock`, no `MagicMock`, no `patch` decorators. Tests that require external services (Ollama, network) use `pytest.mark` markers for conditional execution. We adopt and extend Martin's "Clean Code" principle that tests should validate behavior, not assumptions about behavior [@martin2008clean]. To our knowledge, no prior research software engineering framework has formalized a zero-mock policy as an architectural invariant enforced by pipeline gates—the concept of "mockless testing" does not appear in the software engineering literature as a named practice, making this a novel contribution of the Docxology Template.

### Visualization Standards

All generated figures must meet accessibility requirements:

- Minimum 16pt font size for all text elements.
- Colorblind-safe palettes (IBM Design / Wong palette).
- 150–300 DPI rendering for publication quality.
- Descriptive axis labels and figure titles.



---



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



---



# Discussion

## The Zero-Mock Tradeoff

The Zero-Mock testing policy is the template's most distinctive design decision. By prohibiting all mock objects, we gain confidence that tests exercise real code paths—a pytest run against the template genuinely invokes `pandoc`, writes to disk, and parses real YAML. The cost is test duration: the full infrastructure test suite (3,053 tests) takes 2–4 minutes, compared to sub-second execution typical of heavily-mocked suites.

We argue this tradeoff is strongly favorable for research software. Unlike web applications where millisecond latency and thousands of daily deploys demand fast feedback loops, research pipelines run infrequently (once per manuscript revision) and correctness vastly outweighs speed. A mocked test that passes while the real renderer fails is worse than a slow test that catches the failure. As Peng [@peng2011reproducible] argues, the standard for computational reproducibility is that results can be independently verified—mock objects, by definition, prevent such verification. Garijo et al.'s FAIRsoft evaluator [@garijo2024fairsoft] identifies *executability*—the ability to actually install and run research software—as a primary quality indicator, yet the majority of evaluated tools fail this test. The Zero-Mock policy goes further: it requires not merely that the software can be installed, but that every integration pathway has been exercised against real dependencies under test.

However, the policy requires careful management of external dependencies. Tests requiring Ollama (the local LLM backend) use `@pytest.mark.requires_ollama` and are skipped in environments where the service is unavailable. This marker system preserves the Zero-Mock principle while acknowledging that not all environments provide all services.

## Scalability: From 1 to N Projects

The Standalone Project Paradigm enables horizontal scaling: adding a new project requires creating a directory with `manuscript/config.yaml` and nothing else. No infrastructure code changes, no `pyproject.toml` modifications, no CI configuration updates. The `run.sh` orchestrator automatically discovers new projects and presents them in its interactive menu.

We have validated this scaling model with three heterogeneous projects:

- **`code_project`**: Numerical optimization with gradient descent, 58 tests, 96.6% coverage.
- **`cognitive_case_diagrams`**: Category-theoretic linguistics with 25+ DisCoPy-generated figures from 17 renderers, 257 tests, ~96% coverage, 79 BibTeX references spanning 17 research areas.
- **`template`**: This self-referential architectural analysis, 36 tests, 90%+ coverage.

These projects share no code with each other. They share only the infrastructure layer—ten modules, 137 Python files—which provides logging, rendering, validation, steganography, and reporting services identically to each project. This validates the Two-Layer Architecture's claim that infrastructure and project concerns can be cleanly separated.

## Comparison to Existing Tools

The Docxology Template occupies a unique niche in the reproducible research ecosystem. Unlike Snakemake [@koster2012snakemake] and Nextflow [@ditommaso2017nextflow], which excel at parallelizing computational pipelines but do not manage manuscript production or testing enforcement, the template integrates the entire research lifecycle from code to publication. Snakemake 8.x (2024) introduced a plugin architecture for extended execution backends, yet its scope remains computational workflow orchestration—it does not integrate manuscript rendering, documentation standards, or cryptographic provenance. Unlike Quarto [@allaire2024quarto] and R Markdown [@xie2015dynamic], which integrate code execution with document rendering but do not enforce coverage thresholds or embed cryptographic provenance, the template treats testing and provenance as first-class architectural concerns rather than optional plugins.

The key differentiator is the *enforcement* mechanism. The FAIR4RS principles [@barker2022fair4rs] represent a significant advance in articulating what research software quality requires—executability, interoperability, comprehensive metadata—and FAIRsoft [@garijo2024fairsoft] provides automated scoring against these criteria. Yet FAIR4RS compliance is assessed observationally rather than enforced architecturally: a tool may score well on FAIRsoft metrics today and regress tomorrow without detection. The Docxology Template operationalizes FAIR4RS by coupling quality metrics to pipeline gates: the pipeline will not advance past Stage 01 if project test coverage falls below 90%. Provenance is not documented in a README; it is cryptographically embedded in the PDF per the W3C PROV model's principle that provenance should be machine-readable and tamper-evident [@moreau2013provdm]. Documentation is not a best-effort companion; it is a structural requirement enforced by the Documentation Duality standard. In this sense, the template bridges the gap between FAIR4RS as a descriptive standard and FAIR4RS as an enforced invariant.

In Gentleman and Temple Lang's terminology [@gentleman2007research], the Docxology Template is a *research compendium* scaled to the repository level—bundling not just one study's code and data but N studies, with shared infrastructure, automated testing, and embedded provenance. Nüst et al.'s executable research compendium (ERC) [@nust2017containerization] extends this vision with containerized reproduction environments; the Docxology Template complements containerization by adding the testing enforcement, multi-project management, and provenance embedding layers that ERCs do not address.

## The AI Collaboration Model

The Documentation Duality standard (`README.md` + `AGENTS.md` at every directory level) emerged from practical experience with AI coding assistants. Language models perform significantly better when provided with structured, machine-readable context about architectural constraints, API surfaces, and testing requirements. The `AGENTS.md` files serve as a form of "prompt engineering embedded in the codebase"—they preempt common failure modes such as hallucinated API signatures, violation of the Thin Orchestrator pattern, and introduction of mock objects. Lau and Guo [@lau2025aicoding] identify contextual code understanding as a primary bottleneck across 90 surveyed AI coding assistant systems; the Documentation Duality standard addresses this by providing pre-structured context at every directory level, reducing the surface area for hallucination.

This model creates a positive feedback loop: as AI agents modify the codebase, they update the corresponding documentation, which in turn provides better context for future modifications. The supplementary `CLAUDE.md` file at the repository root provides system-level instructions (the Two-Layer Architecture, Zero-Mock policy, naming conventions) that apply globally, creating a three-tier documentation architecture:

1. **Repository-level** (`CLAUDE.md`): Global constraints and architectural principles.
2. **Directory-level** (`AGENTS.md`): Local API surfaces, file inventories, and integration patterns.
3. **Human-level** (`README.md`): Quick-start guides and navigation aids.

This three-tier model is, to our knowledge, novel in the research software engineering literature. As AI coding assistants evolve from reactive suggestion engines toward agentic systems capable of autonomous multi-file modifications [@lau2025aicoding], the need for machine-readable architectural context becomes not a convenience but a prerequisite for safe AI-assisted software evolution.

## The Learning Curve

The Thin Orchestrator pattern imposes a cognitive overhead on researchers accustomed to writing monolithic scripts. The requirement to factor all logic into `src/` modules and use scripts only as stateless wiring introduces an additional layer of indirection. We mitigate this through:

1. **Template examples**: The `code_project` serves as a fully worked exemplar with comprehensive comments.
2. **Documentation Duality**: Every directory has both `README.md` (for humans) and `AGENTS.md` (for AI collaborators), reducing the cost of navigation.
3. **Interactive orchestrator**: `run.sh` provides a TUI menu that abstracts pipeline complexity.
4. **Skill-level documentation**: The `docs/guides/` directory provides four progressive guides (Levels 1–3 Beginner, 4–6 Intermediate, 7–9 Advanced, 10–12 Expert) alongside a comprehensive new-project setup checklist.

## Limitations

- **LaTeX dependency**: The rendering pipeline requires a full TeX distribution (TeX Live or MiKTeX), which is a 4–6 GB install. This is the largest single dependency.
- **Python-centric**: The infrastructure layer is Python-only. Projects in other languages can use the rendering and steganography stages but cannot leverage the `scientific` or `validation` modules.
- **Single-machine**: The pipeline runs locally. Distributed execution (e.g., across a compute cluster) is not natively supported.
- **Steganographic robustness**: Alpha-channel overlays are stripped by aggressive PDF optimization tools (e.g., `qpdf --optimize`). QR codes are visible and removable. Neither provides non-repudiation without digital signatures.
- **Test duration**: The Zero-Mock policy increases test execution time from sub-second (mocked) to multi-minute (real) for the full infrastructure suite. This is acceptable for research workflows but may not suit continuous deployment scenarios.

## Future Directions

1. **Supply-chain provenance**: Integration with software supply chain frameworks such as in-toto [@torresarias2019intoto] and SLSA (Supply-chain Levels for Software Artifacts) to provide end-to-end attestation from source commit through build pipeline to published artifact. The template's existing steganographic layer embeds document-level provenance; supply-chain frameworks would add build-level provenance, closing the gap between "this PDF was produced by this pipeline" and "this pipeline was executed with this verified source code."
2. **Decentralized provenance**: Integration with IPFS or Arweave for immutable publication records, extending the SHA-256-based tamper detection to content-addressed storage networks.
3. **Digital signatures**: GPG or X.509 signing integrated into the steganographic layer, providing cryptographic non-repudiation in addition to tamper detection.
4. **Continuous integration**: GitHub Actions workflows that execute the pipeline on every push, with PDF artifacts as release assets and automated DOI registration via Zenodo.
5. **Multi-language support**: Extension of the Thin Orchestrator pattern to R, Julia, and Rust projects, enabling polyglot research workflows within the Two-Layer Architecture.
6. **Automated FAIR4RS assessment**: Periodic self-scoring against FAIRsoft metrics [@garijo2024fairsoft], with quality indicators (executability, documentation completeness, metadata richness) tracked as pipeline artifacts alongside test coverage and rendering status.
7. **Knowledge graph integration**: Connecting pipeline outputs to Active Inference Knowledge Base entries for automated meta-analysis and cross-project citation tracking.
8. **Formal verification**: Static analysis tooling to enforce the Thin Orchestrator pattern—verifying that scripts contain no algorithmic logic and that `src/` modules do not import from `scripts/`.

# Conclusion

The Docxology Template demonstrates that high-integrity, reproducible research need not be onerous. By embedding provenance, testing, and documentation into the architecture itself—rather than layering them atop a fragmented workflow—the template transforms "best practices" from aspirational guidelines into enforced invariants [@wilson2017good; @sandve2013ten]. The Two-Layer Architecture ensures that infrastructure improvements propagate to all projects without coupling. The Zero-Mock policy ensures that tests reflect reality. The steganographic provenance layer ensures that published artifacts carry their own authentication. The FAIR4RS principles [@barker2022fair4rs] articulate what research software quality requires; the Docxology Template demonstrates how to enforce it.

The template is not merely a build tool; it is an epistemological commitment. It asserts that a research paper is not a static document but a build artifact—reproducible, verifiable, and traceable to the code that generated it. As Knuth observed, programs should be written for humans to read and only incidentally for machines to execute [@knuth1984literate]. We extend this dictum: research manuscripts should be *built* for verification and only incidentally for reading. In an era of generative AI and synthetic media, where the boundary between human-authored and machine-generated text grows increasingly indeterminate [@gruenpeter2021research], the provenance chain from source code to published PDF is not an administrative convenience—it is the epistemic ground on which scientific trust must be rebuilt.



---



# Infrastructure Module Reference

This section provides a detailed reference for all ten infrastructure subpackages, documenting their purpose, key classes, public API, and integration points within the pipeline. The infrastructure layer comprises 137 Python modules validated by 3,053 tests.

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



---



# Security and Provenance

Research integrity requires more than reproducibility; it requires verifiable authorship. In an era of generative AI, automated scraping, and synthetic media, the ability to prove that a document was produced by a specific pipeline at a specific time is a critical defense against fabrication and misattribution. The W3C PROV data model [@moreau2013provdm] establishes a formal vocabulary for expressing provenance records—entities, activities, and agents connected by derivation, generation, and attribution relations. The Docxology Template implements a domain-specific provenance layer that embeds these relations directly into the PDF artifact itself, using four complementary steganographic and cryptographic mechanisms.

## Threat Model

The steganography subsystem defends against three classes of threats:

1. **Unauthorized redistribution**: A manuscript is scraped and republished without attribution. The steganographic watermark survives the redistribution and can be used to prove original authorship.
2. **Content tampering**: Figures or text are modified after publication. The SHA-256 hash embedded in the PDF metadata detects any modification to the file contents.
3. **Provenance forgery**: An attacker claims to have produced a document they did not author. The build timestamp, commit hash, and pipeline metadata embedded in the watermark provide a verifiable chain of custody.

## Steganographic Layers

The system applies four complementary layers of provenance information:

### Layer 1: PDF Metadata Injection

The `inject_pdf_metadata` function writes structured metadata into both the PDF Info dictionary and an XMP (Extensible Metadata Platform) packet:

- `/Creator`: Pipeline identifier
- `/Producer`: Module path (`infrastructure.steganography`)
- `/CreationDate`: UTC timestamp in ISO 8601 format
- `/Author`: From `config.yaml`
- `/Title`: From `config.yaml`
- Custom fields: DOI, ORCID, repository URL

### Layer 2: Cryptographic Hashing

Before watermarking, a SHA-256 hash of the rendered PDF is computed and stored in:

- The output manifest (`output/manifest.json`)
- The PDF metadata (`/Subject` field)
- An external hash file (`output/<name>.sha256`)

This enables post-hoc verification: anyone with the hash can verify that the PDF has not been modified since rendering.

### Layer 3: Alpha-Channel Text Overlay

A semi-transparent text overlay is applied to each page of the PDF, encoding:

- Build timestamp
- Git commit hash (short SHA)
- Project name
- Pipeline version

The overlay is rendered at low opacity (typically 3–5% alpha) to be invisible during normal viewing but detectable through image analysis. It survives printing (as a faint watermark) and standard PDF operations.

### Layer 4: QR Code Injection

An optional QR code is generated containing a URL pointing to the repository (e.g., `github.com/docxology/template`). The QR code is placed in a configurable position (default: bottom-right corner of the last page) at a specified size.

## The `secure_run.sh` Orchestrator

The steganographic pipeline is orchestrated by `secure_run.sh`, a Bash script that wraps the standard `run.sh` pipeline with post-processing steganography:

1. Execute the standard 8-stage pipeline for the target project.
2. Locate the rendered PDF in `output/`.
3. Apply metadata injection, hashing, text overlay, and QR code injection.
4. Save the secured PDF alongside the original.
5. Generate a steganography report in JSON format.

The orchestrator processes either a single specified project or all discovered projects sequentially.

## Tamper Detection

Verification is performed by comparing the stored SHA-256 hash against a freshly computed hash of the distributed PDF. Any modification—even a single bit flip—produces a hash mismatch. The alpha-channel overlay provides a secondary, visual verification channel that does not require access to the original hash.

## Limitations

- Alpha-channel overlays are stripped by some PDF optimization tools (e.g., `qpdf --optimize`).
- QR codes are visible and may be removed by a determined attacker.
- The system does not provide non-repudiation in the cryptographic sense—it does not use digital signatures with private keys. Future versions may integrate GPG or X.509 signing.
- The provenance model is pipeline-centric rather than PROV-compliant; future work will generate machine-readable PROV-O [@moreau2013provdm] records alongside the embedded watermarks.

## Relationship to Software Supply Chain Integrity

The steganographic provenance layer operates at the *document level*—it certifies the integrity of a specific PDF artifact. A complementary concern is *build-level* provenance: certifying that the pipeline itself was executed with verified source code and dependencies. Frameworks such as in-toto [@torresarias2019intoto] and SLSA (Supply-chain Levels for Software Artifacts) address this concern by defining attestation chains from source commit through build steps to final artifact. Future versions of the Docxology Template may generate SLSA-compatible provenance attestations alongside the steganographic watermarks, creating a two-layer provenance model: in-toto attests that the build pipeline was executed with the claimed source code, while the steganographic layer attests that the PDF was produced by that pipeline at a specific time.

## Relationship to FAIR and Formal Provenance Standards

The steganographic layer supports the FAIR for Research Software (FAIR4RS) principles [@barker2022fair4rs] at the artifact level. PDFs carry embedded metadata (Findability) in standardized XMP format (Interoperability). The SHA-256 hash manifest enables persistent integrity verification (a prerequisite for Reusability). The Documentation Duality standard ensures that the software producing the artifact is inspectable and well-documented (satisfying FAIRsoft [@garijo2024fairsoft] metadata and documentation indicators). Full PROV-compliant provenance traces—capturing the derivation chain from source data through analysis scripts to rendered PDF—are a natural extension and a primary target for future development.



---



# Appendices

## Appendix A: Pipeline Stage Reference

| Stage | Script | Input | Output | Failure Mode |
|-------|--------|-------|--------|--------------|
| 00 | `00_setup_environment.py` | System environment | Validated env, directories | Hard fail |
| 01 | `01_run_tests.py` | `tests/`, `projects/*/tests/` | Coverage JSON, test reports | Configurable |
| 02 | `02_run_analysis.py` | `projects/*/scripts/*.py` | Figures, data files | Hard fail |
| 03 | `03_render_pdf.py` | `manuscript/*.md`, `config.yaml` | PDF in `output/` | Hard fail |
| 04 | `04_validate_output.py` | `output/` contents | Validation report | Warning |
| 05 | `05_copy_outputs.py` | `output/` artifacts | Organized copies | Soft fail |
| 06 | `06_llm_review.py` | Rendered manuscript | Executive summary, reviews | Skippable |
| 07 | `07_generate_executive_report.py` | All stage outputs | JSON + Markdown report | Soft fail |

## Appendix B: Configuration Reference (`config.yaml`)

```yaml
paper:
  title: "Paper Title"
  subtitle: "Optional Subtitle"
  version: "1.0"
  date: "2026-03-08"

authors:
  - name: "Author Name"
    orcid: "0000-0000-0000-0000"
    email: "author@example.com"
    affiliation: "Institution"
    corresponding: true

publication:
  doi: "10.5281/zenodo.XXXXXX"
  journal: "Target Journal"
  volume: "1"
  pages: "1-10"
  year: "2026"

keywords:
  - "keyword1"
  - "keyword2"

metadata:
  license: "Apache License 2.0"
  language: "en"

llm:
  reviews:
    enabled: true
    types: [executive_summary, quality_review]
  translations:
    enabled: false

testing:
  max_test_failures: 0
  max_infra_test_failures: 3
  max_project_test_failures: 0
```

## Appendix C: Repository Directory Structure

```
docxology/template/
├── infrastructure/           # Layer 1: Shared services (137 .py files)
│   ├── core/                 # 28 files — logging, config, exceptions
│   ├── documentation/        # 6 files — figure management, glossary
│   ├── llm/                  # 30 files — Ollama integration, literature
│   ├── project/              # 2 files — project discovery
│   ├── publishing/           # 9 files — citation generation, Zenodo
│   ├── rendering/            # 12 files — Pandoc + XeLaTeX + reports
│   ├── reporting/            # 14 files — coverage parsing, reports
│   ├── scientific/           # 6 files — stability, benchmarking
│   ├── steganography/        # 8 files — watermarking, hashing
│   └── validation/           # 22 files — PDF + Markdown validation
├── scripts/                  # Pipeline orchestration
│   ├── 00_setup_environment.py
│   ├── 01_run_tests.py
│   ├── 02_run_analysis.py
│   ├── 03_render_pdf.py
│   ├── 04_validate_output.py
│   ├── 05_copy_outputs.py
│   ├── 06_llm_review.py
│   ├── 07_generate_executive_report.py
│   └── execute_pipeline.py
├── projects/                 # Layer 2: Research workspaces
│   ├── code_project/         # Gradient descent exemplar
│   ├── cognitive_case_diagrams/  # Category theory + linguistics
│   └── template/             # This self-referential project
├── tests/                    # Infrastructure test suite (148 files, 3,053 tests)
├── docs/                     # Repository documentation (90+ files, 12 subdirectories)
├── run.sh                    # Interactive TUI orchestrator
├── secure_run.sh             # Steganographic pipeline wrapper
├── AGENTS.md                 # System-level AI agent documentation
├── CLAUDE.md                 # Global AI coding assistant instructions
├── README.md                 # Human-readable project overview
└── pyproject.toml            # Root project configuration (uv)
```

## Appendix D: Exemplar Project Summary

| Project | Domain | src/ Modules | Test Count | Coverage | Figures | Pages |
|---------|--------|:-----------:|:----------:|:--------:|:-------:|:-----:|
| `code_project` | Numerical optimization | `optimizer.py` (248 lines) | 58 | 96.6% | 6 | ~20 |
| `cognitive_case_diagrams` | Category theory / linguistics | 12 modules, 17 DisCoPy renderers | 257 | ~96% | 25+ | ~77 |
| `template` | Meta-architecture | `introspection.py` | 36 | 90%+ | 3 | ~5 |

## Appendix E: Documentation Inventory

The repository maintains documentation at three levels:

| Level | Files | Purpose |
|-------|:-----:|---------|
| Repository root | `AGENTS.md`, `CLAUDE.md`, `README.md`, `RUN_GUIDE.md` | Global navigation and AI agent context |
| `docs/` directory | 90+ files across 12 subdirectories | User guides, API reference, troubleshooting |
| Per-directory | `AGENTS.md` + `README.md` at every directory | Documentation Duality standard |

The `docs/` subdirectories cover: `core/` (essential docs), `guides/` (skill levels 1–12), `architecture/` (system design), `usage/` (content authoring), `operational/` (build, config, logging, troubleshooting), `reference/` (API, FAQ, glossary), `modules/` (10 infrastructure modules), `development/` (contributing, testing), `best-practices/` (version control, migration), `prompts/` (9 AI prompt templates), `security/` (steganography, hashing), and `audit/` (review reports).

## Appendix F: Comparative Tool Matrix

| Capability | Docxology | Snakemake | Nextflow | CWL | Quarto | Jupyter Book | R Markdown |
|------------|:---------:|:---------:|:--------:|:---:|:------:|:------------:|:----------:|
| Pipeline orchestration | ✓ | ✓ | ✓ | ✓ | — | — | — |
| Manuscript rendering | ✓ | — | — | — | ✓ | ✓ | ✓ |
| Code execution | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Testing enforcement | ✓ | — | — | — | — | — | — |
| Coverage thresholds | ✓ | — | — | — | — | — | — |
| Cryptographic provenance | ✓ | — | — | — | — | — | — |
| Steganographic watermarking | ✓ | — | — | — | — | — | — |
| Multi-project management | ✓ | — | — | — | — | — | — |
| AI-agent documentation | ✓ | — | — | — | — | — | — |
| Interactive TUI | ✓ | — | — | — | — | — | — |
| Container support | — | ✓ | ✓ | ✓ | — | — | — |
| Distributed execution | — | ✓ | ✓ | ✓ | — | — | — |
| DAG parallelism | — | ✓ | ✓ | ✓ | — | — | — |
| Multi-language (R/Julia) | — | ✓ | — | ✓ | ✓ | ✓ | ✓ |
