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
