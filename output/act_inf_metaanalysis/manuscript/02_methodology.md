# Methodology: Pipeline Design and Formal Definitions

This section describes the six components of our computational meta-analysis pipeline: literature retrieval, canonical deduplication, LLM-based assertion extraction, probabilistic knowledge graph construction, hypothesis scoring, and end-to-end orchestration. The pipeline extends the systematic literature analysis approach of Knight et al. \citep{knight2022fep}—which combined manual annotation with ontology-based automated analysis—by substituting manual coding with fully automated, LLM-driven assertion extraction and citation-weighted hypothesis scoring.

## Multi-Source Literature Retrieval

We retrieve papers from three complementary academic databases to maximize coverage and enable cross-source deduplication:

**arXiv.** We query the arXiv Atom API using the phrase-matched search `all:"active inference" OR all:"free energy principle"`. The `all:` prefix searches titles, abstracts, and full text; phrase matching reduces contamination from unrelated physics papers that mention "free energy" in thermodynamic contexts.

**Semantic Scholar.** We query the Semantic Scholar Graph API \citep{kinney2023semantic} with the same terms. Semantic Scholar provides citation graphs, abstract embeddings, and links to published versions. Retry logic with exponential backoff handles rate limiting.

**OpenAlex.** We query OpenAlex \citep{priem2022openalex} to capture journal-published work that may not appear on arXiv, including clinical studies and neuroscience experiments in domain-specific venues. The `referenced_works` field populates citation links for each paper.

After retrieval, papers are assigned a canonical identifier using the priority scheme: DOI $>$ arXiv ID $>$ Semantic Scholar ID $>$ OpenAlex ID $>$ title hash. When the same paper appears in multiple sources, the record with the highest metadata completeness is retained. This deduplication produces $N = 1208$ unique papers spanning 1972--2026.

### Curation and Keyword Limitations

We emphasize that this process relies fundamentally on keyword search strategies across divergent APIs. In any complex research field, there is no single optimal word or threshold for definitive inclusion or exclusion. Different information sources and repositories yield differing schemas and representations, inevitably introducing both false positives (extraneous papers overlapping in terminology, such as unrelated database or biological toolkits) and false negatives (relevant papers employing alternative nomenclature without standard keywords).

Consequently, this pipeline is not intended to produce a static, "golden" list of canonical papers. Rather, it is designed as an open-source software package that can be modularly updated and versioned. Researchers can configure the pipeline to operate on custom literature bibliographies curated for specific relevance criteria through time, treating the initial query-based retrieval as a programmatic starting point rather than an absolute boundary.

## Canonical Identifier Deduplication

For each incoming paper, we compute a canonical ID applying the cascading priority scheme detailed above. Should a paper with an identical canonical ID already exist within the dataset, the two records are comparatively evaluated on metadata completeness—defined as the count of non-empty attributes among \{abstract, DOI, arXiv ID, venue, citation count\}. The pipeline reliably retains the structurally richer record; in the event of a tie, the incumbent is preserved. This "merge-on-add" strategy automatically aggregates the richest available metadata without mandating an expensive downstream reconciliation pass.

The priority hierarchy naturally tracks bibliographic realities: DOIs serve as the most stable cross-platform identifiers; arXiv IDs guarantee consistency across the preprint ecosystem; source-specific API IDs serve as reliable fallbacks; and exact title hashing provides a robust final failsafe for edge case papers devoid of structured identifiers.

After deduplication, a **relevance filter** removes papers whose titles and abstracts lack any core Active Inference terminology (e.g., ``active inference,''``free energy principle,'' ``variational free energy''), eliminating off-topic results introduced by broad keyword overlap across heterogeneous databases.

## LLM-Based Assertion Extraction

We extract assertions by prompting a locally hosted LLM (Ollama \citep{ollama2024}) to assess each paper's abstract against eight standard hypotheses. The model receives a structured prompt containing the paper title, abstract, and hypothesis definitions, and returns a JSON array where each element specifies a hypothesis ID, direction (supports, contradicts, neutral, or irrelevant), a confidence score $c \in [0, 1]$, and a reasoning string. Assertions marked "irrelevant" are discarded; confidence values are clamped to $[0, 1]$; and responses are validated against the known hypothesis ID set. Papers lacking abstracts are skipped.

Each assertion is encoded as a nanopublication \citep{groth2010anatomy, kuhn2016decentralized}—formally, a tuple $(p, h, d, c)$ where $p$ is the paper identifier, $h$ the hypothesis identifier, $d \in \{\text{supports}, \text{contradicts}, \text{neutral}\}$ the direction, and $c$ the confidence. Provenance metadata records the LLM model, timestamp, and paper identifier.

## Subfield Classification

Each paper is classified into one of eight categories organized across three domains: **A – Core Theory** (A1: quantitative and formal mathematical theory; A2: qualitative philosophy and general FEP theory), **B – Tools \& Translation** (algorithms, scaling, and software development), and **C – Application Domains** (C1: neuroscience, C2: robotics, C3: language processing, C4: computational psychiatry, C5: biology and morphogenesis). Classification uses word-boundary-aware keyword matching against curated lists applied to titles and abstracts. A priority system ensures that specific application domains (C1–C5, priority 1) take precedence over tools (B, priority 2), formal theory (A1, priority 3), and the broad qualitative philosophy catch-all (A2, priority 4). Within a priority tier, the domain with the most keyword matches wins. A1's keyword set includes mathematical indicators such as *theorem*, *proof*, *convergence*, *posterior*, *equation*, and *Fokker–Planck*, ensuring that papers with mathematical content are classified as formal theory rather than defaulting to the philosophy category.

## Knowledge Graph Schema

The knowledge graph is an RDF-compatible directed graph with three node types: **paper nodes** (metadata: title, abstract, authors, year, venue, citation count, domain), **assertion nodes** (claim text, direction, hypothesis ID, confidence), and **hypothesis nodes** (the eight standard hypotheses). Edges encode three relations: `aif:asserts` (paper $\to$ assertion), `aif:cites` (paper $\to$ paper), and `aif:supports`/`aif:contradicts` (assertion $\to$ hypothesis). The namespace `http://activeinference.org/ontology/` defines all predicates.

The graph is serialized using rdflib \citep{rdflib2023} and persisted as JSON Lines, with the schema designed for migration to full RDF triplestores.

## Citation-Weighted Hypothesis Scoring

For each hypothesis $H$, we compute a citation-weighted evidence score:

$$
\text{score}(H) = \frac{\sum_{a \in S(H)} w(a) - \sum_{a \in C(H)} w(a)}{\sum_{a \in A(H)} w(a)}
$$

where $S(H)$, $C(H)$, and $A(H)$ are the sets of supporting, contradicting, and all assertions for $H$, and the weight function is:

$$
w(a) = \log(1 + \text{citations}(a)) \cdot \text{confidence}(a)
$$

The logarithmic citation weighting ensures that highly cited papers carry more influence without allowing any single paper to dominate. The score lies in $[-1, 1]$. Temporal trends are computed by evaluating the cumulative score at each year, using only assertions from papers published up to that year. A full derivation appears in the Technical Appendix (A.1).

## Tally-Based Evidence Aggregation

We emphasize that this algorithmic scoring formula constitutes a **tally-based approach** to evidence synthesis: each nanopublication assertion operates as an independent evidential vote, mathematically weighted by citation impact and the extraction model's semantic confidence. The aggregation is deliberately linear and additive—supporting and contradicting assertions are summed and differenced, independent from modeling dependencies, correlated evidence clustering, or topological causal structure among claims. This intentional design choice prioritizes operational transparency, rigorous reproducibility, and computational tractability over abstract statistical sophistication.

The tally-based framing introduces three distinct constraints. First, assertions extracted from methodologically related papers (e.g., iterative publications originating from a single research group validating the same structural model) are counted identically and independently, inherently amplifying correlated evidence. Second, the scoring metric imposes symmetrical treatment across assertion source types: an affirmative assertion parsed from a theoretical review and one sourced from an empirical randomized controlled trial carry equivalent leverage at a matched confidence bound. Finally, temporal scoring tracks *cumulative running totals* rather than dynamic probabilistic estimates; the score at year $t$ computes the absolute integrated momentum of all historical evidence, rather than a decaying posterior that incrementally downweights early foundational texts.

We embrace these constraints deliberately. The tally-based execution furnishes a stable, highly interpretable baseline upon which superior configurations can be systematically evaluated. Section 5 scopes these concrete extensions—specifically encompassing hierarchical Bayesian scoring frameworks, causal evidence directed acyclic graphs (DAGs), and evidential diversity indices that geometrically constrain correlated research amplification.

## Growth-Rate Estimation

We estimate field dynamics via two complementary metrics. The **mean year-over-year growth rate** $\bar{g}$ is the arithmetic mean of annual growth rates for years with non-zero prior-year publications. The **doubling time** $t_d = \ln 2 / \ln(1 + \bar{g})$. The **compound annual growth rate** (CAGR) captures the annualized rate across the full temporal span. Mathematical details are provided in the Technical Appendix (A.3).

## Pipeline Architecture and Reproducibility

The complete pipeline operates in five stages:

1. **Literature Search** (`01_literature_search.py`). Query arXiv, Semantic Scholar, and OpenAlex; merge into a deduplicated corpus; persist as JSONL.

2. **Meta-Analysis** (`02_meta_analysis_pipeline.py`). Classify domains (A/B/C); compute temporal metrics; build TF-IDF matrix \citep{salton1975vector}; extract NMF topics \citep{lee1999nmf}; construct citation network; compute network metrics.

3. **Knowledge Graph** (`03_build_knowledge_graph.py`). Extract LLM-based assertions from abstracts; wrap in nanopublications; score hypotheses; compute temporal trends. Assertions are **incrementally saved** to `nanopublications.jsonl` at configurable checkpoint intervals (default: every 50 papers), enabling the pipeline to resume from where it left off after interruption without re-processing already-analyzed papers.

4. **Figure Generation** (`04_generate_figures.py`). Render 16 publication-ready visualizations from analysis outputs: field summary, domain distribution, growth curve, domain timeline, citation network, degree distribution, hypothesis dashboard, evidence timeline, assertion breakdown, assertion summary, word cloud, PCA embeddings, term heatmap, dendrogram, topic-term bars, and co-occurrence matrix.

5. **Variable Injection** (`05_inject_variables.py`). Compute dynamic variables from pipeline outputs (e.g., corpus counts, temporal metrics, hypothesis scores) and inject them into the manuscript Markdown templates.

All computation resides in tested library modules; scripts act as thin orchestrators that import methods and handle file I/O. The test suite uses real data and computation without mocking. The pipeline is deterministic given fixed random seeds and API responses. Source code, configuration, and outputs are available under CC-BY-4.0.
