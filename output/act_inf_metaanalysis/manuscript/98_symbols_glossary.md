# Notation, Abbreviations, and Hypothesis Definitions

## Mathematical Symbols and Notation

| Symbol | Description |
| --- | --- |
| $\mathcal{F}$ | Variational free energy |
| $\mathbf{F}$ | Expected free energy (for policy selection) |
| $D_{\mathrm{KL}}$ | Kullback--Leibler divergence |
| $q(\cdot)$ | Approximate posterior (recognition density) |
| $p(\cdot)$ | Generative model (prior and likelihood) |
| $\mathbf{s}$ | Hidden states |
| $\mathbf{o}$ | Observations |
| $\pi$ | Policy (sequence of actions) |
| $\mathbf{A}$ | Likelihood mapping (observation model) |
| $\mathbf{B}$ | Transition model (state dynamics) |
| $\mathbf{C}$ | Prior preferences over observations |
| $\mathbf{D}$ | Prior over initial states |
| $N$ | Corpus size (total deduplicated papers) |
| $n$ | Subfield paper count |
| $T$ | Time span in years (for CAGR computation) |
| $N_{\text{start}}$ | Publication count in the first year of the corpus |
| $N_{\text{end}}$ | Publication count in the last year of the corpus |
| $w(a)$ | Citation-weighted assertion score: $\log(1 + \text{citations}) \cdot \text{confidence}$ |
| $\text{score}(H)$ | Aggregate evidence score for hypothesis $H$, range $[-1, 1]$ |
| $S(H)$ | Set of supporting assertions for hypothesis $H$ |
| $C(H)$ | Set of contradicting assertions for hypothesis $H$ |
| $A(H)$ | Set of all assertions for hypothesis $H$ |
| $c$ | Assertion confidence, range $[0, 1]$ |
| $d$ | Assertion direction: supports, contradicts, or neutral |
| $\mathbf{V}$ | Document-term matrix (NMF input) |
| $\mathbf{W}$ | Document-topic matrix (NMF factor) |
| $\mathbf{H}$ | Topic-term matrix (NMF factor) |
| $k$ | Number of latent topics |
| $\epsilon$ | Numerical stability constant ($10^{-10}$) |
| $\text{CAGR}$ | Compound annual growth rate |
| $t_d$ | Publication doubling time |
| $\bar{g}$ | Mean annual year-over-year growth rate |
| $\kappa$ | Cohen's kappa (inter-annotator agreement) |

## Abbreviations and Acronyms Used

| Abbreviation | Definition |
| --- | --- |
| AIF | Active Inference |
| API | Application Programming Interface |
| CAGR | Compound Annual Growth Rate |
| CI | Confidence Interval |
| DCM | Dynamic Causal Modelling |
| DOI | Digital Object Identifier |
| DPI | Dots Per Inch (figure resolution) |
| EEG | Electroencephalography |
| EFE | Expected Free Energy |
| ERP | Event-Related Potential |
| FEP | Free Energy Principle |
| fMRI | Functional Magnetic Resonance Imaging |
| GML | Graph Modelling Language (network serialization format) |
| JSON | JavaScript Object Notation |
| JSONL | JSON Lines (newline-delimited JSON) |
| KG | Knowledge Graph |
| KL | Kullback--Leibler (divergence) |
| LLM | Large Language Model |
| NMF | Non-negative Matrix Factorization |
| NLP | Natural Language Processing |
| ORCID | Open Researcher and Contributor ID |
| OWL | Web Ontology Language |
| PCA | Principal Component Analysis |
| POMDP | Partially Observable Markov Decision Process |
| RDF | Resource Description Framework |
| RL | Reinforcement Learning |
| RNG | Random Number Generator |
| SPARQL | SPARQL Protocol and RDF Query Language |
| SPM | Statistical Parametric Mapping |
| TF-IDF | Term Frequency--Inverse Document Frequency |
| URI | Uniform Resource Identifier |
| YAML | YAML Ain't Markup Language (configuration format) |
| YoY | Year-over-Year |

## Standard Hypothesis Definitions and Identifiers

| ID | Hypothesis | Scope |
| --- | --- | --- |
| H1 | FEP Universality: The Free Energy Principle applies universally to all self-organizing systems | A (Core Theory) |
| H2 | AIF Optimality: Active Inference agents achieve optimal decision-making under uncertainty | B (Tools) |
| H3 | Markov Blanket Realism: Markov blankets correspond to real physical boundaries | A (Core Theory) |
| H4 | Predictive Coding: Cortical hierarchies minimize prediction errors via predictive coding | C1 (Neuroscience) |
| H5 | Scalability: Active Inference scales to complex, high-dimensional environments | B (Tools) |
| H6 | Clinical Utility: Active Inference provides clinically useful models of psychiatric conditions | C4 (Psychiatry) |
| H7 | Morphogenesis: The FEP explains morphogenetic and developmental processes | C5 (Biology) |
| H8 | Language AIF: Active Inference provides a viable framework for language processing | C3 (Language) |

## Glossary of Key Terms

| Term | Definition |
| --- | --- |
| **Active Inference** | A framework in which agents minimize expected free energy to select actions, unifying perception, learning, and decision-making under the Free Energy Principle. |
| **Assertion** | A directed, confidence-scored claim linking a paper to a hypothesis (supports, contradicts, or neutral). The basic unit of evidence in the knowledge graph. |
| **Canonical ID** | The unique identifier assigned to each paper during deduplication, following the priority scheme: DOI > arXiv ID > Semantic Scholar ID > OpenAlex ID > title hash. |
| **Expected Free Energy** | A quantity combining epistemic value (information gain) and pragmatic value (goal achievement) that active inference agents minimize over policies. |
| **Free Energy Principle** | The principle that self-organizing systems minimize variational free energy, an upper bound on surprise, to maintain their structural integrity. |
| **Generative Model** | A probabilistic model specifying the joint distribution over hidden states and observations, encoding an agent's beliefs about how observations are generated. |
| **Knowledge Graph** | A directed graph encoding papers, assertions, hypotheses, and their relationships, serialized in an RDF-compatible format. |
| **Markov Blanket** | A statistical boundary separating internal states from external states, defined as the set of nodes that renders a system conditionally independent of its environment. |
| **Nanopublication** | A minimal, self-contained unit of publishable knowledge consisting of an assertion, provenance metadata, and publication context. |
| **Precision** | The inverse variance of a probability distribution; in active inference, precision weighting determines the influence of prediction errors at different levels of a hierarchy. |
| **Variational Free Energy** | An upper bound on surprise (negative log-evidence) that can be decomposed into complexity (KL divergence from prior) and accuracy (expected log-likelihood). |
| **Louvain Algorithm** | A greedy modularity-maximization algorithm for community detection in networks. Applied to the citation graph to identify clusters of densely interconnected papers. |
| **PageRank** | A centrality metric originally designed for web page ranking. In citation networks, PageRank identifies highly influential papers that serve as hubs connecting otherwise disconnected subgraphs. |
| **Ward Linkage** | A hierarchical clustering method that minimizes the total within-cluster variance at each merge step. Used to compute dendrograms of domain centroids from mean TF-IDF vectors. |
| **Checkpoint** | A JSON Lines snapshot of LLM extraction progress, recording which papers have been processed and the resulting assertions, enabling incremental resume after interruption. |
| **Incremental Resume** | The pipeline's ability to continue from where a previous run stopped, loading existing corpus/assertions and processing only new papers, controlled by `--clear-corpus` and `--clear-assertions` CLI flags. |
| **LLM Config** | A configuration object specifying the Ollama model name, API URL, temperature, maximum retries, and retry delay for LLM-based assertion extraction. |
| **Domain Timeline** | Per-domain yearly publication counts showing temporal evolution of research activity across the eight tracked categories (A1–A2, B, C1–C5). |
| **Progressive Parsing** | The pipeline's multi-stage JSON recovery strategy for handling malformed LLM output: direct parse → strip code fences → extract first JSON array → individual element recovery. |
| **Wong Palette** | The colorblind-safe 8-color palette from Wong (2011), used as the standard visualization palette throughout all pipeline-generated figures. |
