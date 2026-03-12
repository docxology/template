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
