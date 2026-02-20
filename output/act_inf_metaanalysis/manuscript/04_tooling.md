# Tooling and Infrastructure: Software Ecosystem, Knowledge Graph Deployment, and Quality Assurance \label{sec:tooling}

The practical utility of a computational meta-analysis depends on robust tooling at each pipeline stage: assertion extraction, modeling and simulation, knowledge graph infrastructure, and quality assurance.

## LLM-Based Assertion Extraction

Extracting structured assertions from unstructured text is the most labor-intensive component of knowledge graph construction. Manual annotation produces high-quality results but does not scale to corpora of thousands of papers—a constraint demonstrated by Knight et al. \citep{knight2022fep}, whose systematic literature analysis of FEP and Active Inference publications required manual coding of structural, visual, and mathematical features for hundreds of annotated papers. We implement a hybrid approach: LLMs perform initial extraction, with human review for validation and correction.

Our extraction pipeline deploys a locally hosted LLM through Ollama \citep{ollama2024}. Each paper's abstract is assessed against the eight hypothesis definitions in a structured prompt requesting a JSON array of assessments. Unlike keyword matching, which detects only topical terms, the LLM evaluates the *semantic relationship* between a paper's claims and each hypothesis. Papers critiquing the FEP correctly receive "contradicts" assessments for FEP Universality (H1), while methodology tutorials receive "neutral" assessments reflecting their pedagogical character. Detailed prompt engineering, schemas, and failure modes are documented in the supplementary extraction pipeline (see \hyperref[sec:extraction_pipeline]{Section 4a}).

<!-- See 04a_extraction_pipeline.md for detailed pipeline documentation -->

## Software Ecosystem

The Active Inference community has developed several specialized software tools, though the ecosystem remains highly fragmented—no single package spans the full spectrum from theoretical simulation to empirical data analysis:

**pymdp.** The pymdp library \citep{heins2022pymdp} provides a Python implementation of active inference for discrete state-space POMDPs, supporting message passing on factor graphs, policy inference via expected free energy, and hierarchical generative models. It has become the standard entry point for algorithm development.

**SPM.** The SPM package (Wellcome Centre for Human Neuroimaging) includes MATLAB implementations of Dynamic Causal Modeling and variational Bayesian inference under the FEP. It remains the reference implementation for neuroimaging applications.

**RxInfer.jl.** RxInfer is a Julia package for reactive message-passing-based Bayesian inference, supporting real-time and streaming inference suitable for robotics and online learning. The release of version 4.0.0 in early 2025 \citep{rxinfer2025} substantially enhanced its probabilistic programming framework, introducing projected constraints and adaptive qualities specifically optimized for dynamic streams of data and autonomous systems.

### Comparative Feature Matrix

| Feature | pymdp | SPM | RxInfer.jl |
| --- | --- | --- | --- |
| **Language** | Python | MATLAB | Julia |
| **State Spaces** | Discrete | Discrete + Continuous | Continuous (factor graphs) |
| **Inference** | Message passing | Variational Bayes | Reactive message passing |
| **Deep AIF** | Partial | No | Via custom factors |
| **Real-time** | No | No | Yes (streaming) |
| **Hierarchical** | Yes | Yes (DCM) | Yes |
| **License** | MIT | GPL | MIT |
| **Primary Use** | Research prototyping | Neuroimaging | Robotics / online learning |

The complementary strengths across these packages reveal a structurally fragmented ecosystem: `pymdp` provides an accessible, Python-native entry point for discrete prototyping; `SPM` remains the clinical gold standard for continuous neuroimaging; and `RxInfer.jl` addresses the real-time constraints of embedded robotics. The absence of a unified, cross-regime computational infrastructure represents both a critical operational bottleneck and a major opportunity for framework unification.

## Knowledge Graph Infrastructure

Our knowledge graph uses an RDF-compatible schema deployable on standard semantic web infrastructure. The engineering trade-offs among the three deployment options are straightforward:

**Nanopublication servers** provide decentralized, content-addressed storage. Our current JSON Lines implementation prioritizes simplicity; the schema supports migration to the nanopublication network for public deployment.

**RDF stores** (e.g., Apache Jena Fuseki, Blazegraph, Oxigraph) enable SPARQL queries such as "find all papers supporting hypothesis H published after 2020 in the neuroscience domain (C1)." The cost is operational overhead and query latency.

**Property graph databases** (e.g., Neo4j) prioritize traversal performance for path queries and community detection, at the expense of semantic web compatibility.

The namespace `http://activeinference.org/ontology/` ensures integration with external ontologies and linked data resources.

## Multi-Level Quality Assurance

Quality assurance operates at four levels.

### Assertion-Level Validation

Assertions below a configurable confidence threshold (default 0.5) are flagged for review. Inter-annotator agreement ($\kappa$) is computed when multiple annotators assess the same paper.

### Graph-Level Consistency Checks

Consistency checks verify that all nodes link to valid targets and no orphan nodes exist. Coverage metrics track the proportion of annotated papers.

### Score-Level Unit Testing

Hypothesis scoring is validated through unit tests with synthetic data verifying boundary conditions (all-support → +1, all-contradict → −1, balanced → 0). Sensitivity analysis varies confidence thresholds and citation weighting.

### Pipeline-Level Test Coverage

Test-driven development enforces 90\% minimum code coverage on project modules and 60\% on shared infrastructure, with real data and computation (no mocking).

### Quality Thresholds

| Level | Metric | Threshold | On Failure |
| --- | --- | --- | --- |
| Assertion | Confidence | $\geq 0.5$ | Flag for review |
| Assertion | Inter-annotator $\kappa$ | $\geq 0.6$ | Re-annotate |
| Graph | Orphan node ratio | $= 0$ | Reject build |
| Graph | Corpus coverage | $\geq 80\%$ | Warning |
| Score | Boundary tests | All pass | Block release |
| Pipeline | Code coverage | $\geq 90\%$ | Block merge |
| Pipeline | Test pass rate | $100\%$ | Block release |

The hypothesis evidence results, temporal dynamics of evidence accumulation, and assertion analysis are presented in the dedicated hypothesis results section (see \hyperref[sec:hypothesis_results]{Section 4b}).
