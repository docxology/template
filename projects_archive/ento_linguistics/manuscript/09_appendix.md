# Appendix {#sec:appendix}

This appendix provides additional technical details supporting the Ento-Linguistic analysis presented in the main manuscript.

## A. Text Processing Implementation Details

### A.1 Linguistic Preprocessing Pipeline

Our text processing pipeline implements systematic normalization to ensure reliable pattern detection across diverse scientific writing styles:

\begin{equation}\label{eq:text_normalization_detailed}
T_{\text{processed}} = \text{lemmatize}(\text{pos_filter}(\text{tokenize}(\text{lowercase}(\text{unicode_normalize}(T)))))
\end{equation}

where each transformation step preserves semantic content while standardizing linguistic variation.

**Tokenization Strategy**: We employ domain-aware tokenization that recognizes scientific terminology:

\begin{equation}\label{eq:scientific_tokenization}
\tau_{\text{scientific}}(T) = \left\{\begin{array}{ll}
\text{scientific\_term}(t) & \text{if } t \in \mathcal{T}_{\text{domain}} \\
\text{word\_tokenize}(t) & \text{otherwise}
\end{array}\right.
\end{equation}

where $\mathcal{T}_{\text{domain}}$ contains curated entomological terminology that should not be further subdivided.

### A.2 Linguistic Feature Extraction

Our feature extraction combines multiple linguistic indicators:

**Syntactic Features**: Part-of-speech patterns, dependency relations, and grammatical structures characteristic of scientific discourse.

**Semantic Features**: Word embeddings, semantic similarity measures, and domain-specific concept vectors.

**Discourse Features**: Rhetorical markers, argumentative structures, and citation patterns that indicate research traditions.

## B. Terminology Extraction Algorithms

### B.1 Domain-Specific Term Identification

Terminology extraction uses a multi-criteria scoring function:

\begin{equation}\label{eq:term_scoring_detailed}
S(t, d) = w_1 \cdot \text{frequency}(t, d) + w_2 \cdot \text{contextual_coherence}(t, d) + w_3 \cdot \text{semantic_relevance}(t, d)
\end{equation}

where $d$ represents the Ento-Linguistic domain and weights $w_1, w_2, w_3$ are calibrated for each domain.

**Contextual Coherence**: Measures how consistently a term appears in domain-relevant contexts:

\begin{equation}\label{eq:contextual_coherence}
C(t, d) = \frac{|\text{contexts}(t, d)|}{\sum_{d' \in D} |\text{contexts}(t, d')|}
\end{equation}

### B.2 Ambiguity Detection Framework

Ambiguity detection combines statistical and linguistic indicators:

\begin{equation}\label{eq:ambiguity_detection}
A(t) = \alpha \cdot H(\text{contexts}(t)) + \beta \cdot \text{semantic_variance}(t) + \gamma \cdot \text{syntactic_ambiguity}(t)
\end{equation}

where $H(\text{contexts}(t))$ is the entropy of contextual usage patterns.

## C. Network Construction and Analysis

### C.1 Edge Weight Calculation

Network edges are weighted using multiple co-occurrence measures:

\begin{equation}\label{eq:edge_weighting_detailed}
w(u,v) = \frac{1}{3} \left[ \frac{\text{co-occurrence}(u,v)}{\max(\text{freq}(u), \text{freq}(v))} + \text{Jaccard}(u,v) + \text{semantic_similarity}(u,v) \right]
\end{equation}

**Co-occurrence Window**: 50-word sliding windows capture meaningful term relationships while avoiding noise from distant terms.

**Semantic Similarity**: Uses domain-specific embeddings trained on entomological literature.

### C.2 Community Detection Algorithms

We implement multiple community detection approaches for robust network partitioning:

**Modularity Optimization**:

\begin{equation}\label{eq:modularity_optimization}
Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)
\end{equation}

**Domain-Aware Clustering**: Incorporates Ento-Linguistic domain knowledge to ensure communities respect conceptual boundaries.

### C.3 Network Validation Metrics

Network quality is assessed using validation:

\begin{equation}\label{eq:network_validation_detailed}
V(G) = \lambda_1 \cdot \text{modularity}(G) + \lambda_2 \cdot \text{domain_purity}(G) + \lambda_3 \cdot \text{structural_stability}(G)
\end{equation}

where domain purity measures alignment with Ento-Linguistic domain structure.

## D. Framing Analysis Implementation

### D.1 Anthropomorphic Framing Detection

Anthropomorphic language is detected through multiple indicators:

**Lexical Indicators**: Terms suggesting human-like agency, intentionality, or social structures.

**Syntactic Patterns**: Sentence structures implying human-like behavior or cognition.

**Semantic Fields**: Clusters of terms drawing from human social, psychological, or economic domains.

**Detection Algorithm**:

\begin{equation}\label{eq:anthropomorphic_detection}
A_{\text{anthro}}(t) = \sum_{f \in F_{\text{human}}} \text{similarity}(t, f) \cdot w_f
\end{equation}

### D.2 Hierarchical Framing Analysis

Hierarchical structures are identified through:

**Term Relationship Patterns**: Chains of subordination and authority relationships.

**Power Dynamic Indicators**: Terms implying control, dominance, or submission.

**Organizational Metaphors**: Language drawing from human institutional and hierarchical systems.

## E. Validation and Quality Assurance

### E.1 Inter-annotator Agreement Procedures

Terminology validation uses multiple annotators:

**Cohen's Kappa**: Measures agreement between human annotators and automated classification.

**Fleiss' Kappa**: Extends agreement measurement to multiple annotators.

**Bootstrap Validation**: Assesses stability of classifications across subsampling.

### E.2 Statistical Validation Framework

All analyses include rigorous statistical validation:

**Terminology Extraction Validation**:
- **Precision**: Manual verification of extracted terms against expert-curated lists
- **Recall**: Coverage assessment against domain glossaries
- **Domain Accuracy**: Correct classification into Ento-Linguistic domains

**Network Validation**:
- **Structural Validity**: Comparison against null models
- **Domain Correspondence**: Alignment with theoretical domain boundaries
- **Stability Analysis**: Consistency across subsampling procedures

### E.3 Corpus and Data Validation

**Corpus Integrity Checks**:
- Text encoding verification
- Metadata completeness validation
- Duplicate document detection
- Temporal distribution analysis

**Processing Validation**:
- Deterministic output verification
- Cross-platform compatibility testing
- Memory usage monitoring
- Performance regression detection

## F. Computational Environment and Reproducibility

### F.1 Software Dependencies

Analysis conducted using the following software stack:

- **Python**: 3.10+ for analysis implementation
- **spaCy**: 3.7+ for linguistic processing
- **NetworkX**: 3.1+ for network analysis
- **scikit-learn**: 1.3+ for statistical validation
- **pandas**: 2.0+ for data manipulation
- **matplotlib**: 3.7+ for visualization
- **jupyter**: 1.0+ for interactive analysis

### F.2 Hardware Specifications

Computational resources used:

- **CPU**: Intel Xeon E5-2690 v4 (28 cores @ 2.60GHz)
- **Memory**: 128GB DDR4
- **Storage**: 2TB NVMe SSD for data processing
- **OS**: Ubuntu 22.04 LTS

### F.3 Reproducibility Framework

**Version Control**: All code, data, and parameters tracked with git.

**Containerization**: Analysis environments containerized using Docker for exact reproducibility.

**Data Provenance**: audit trail of data processing steps and parameter choices.

**Random Seed Management**: All stochastic operations use fixed seeds for deterministic results.

## G. Extended Mathematical Formulations

### G.1 Conceptual Mapping Framework

The conceptual mapping algorithm formalizes term relationships:

\begin{equation}\label{eq:concept_mapping}
M(t_i, t_j) = \frac{1}{k} \sum_{c=1}^k \text{similarity}(\vec{t_i}^{(c)}, \vec{t_j}^{(c)})
\end{equation}

where $k$ represents the number of contextual embeddings and $\vec{t}^{(c)}$ is the embedding in context $c$.

### G.2 Discourse Pattern Recognition

Discourse pattern detection uses sequence modeling:

\begin{equation}\label{eq:discourse_patterns}
P(d|t_1, \dots, t_n) = \prod_{i=1}^n P(t_i|t_{i-1}, d) \cdot P(d)
\end{equation}

where $d$ represents discourse patterns and $t_i$ are sequential terms.

This technical appendix provides the detailed implementation foundations supporting the Ento-Linguistic analysis presented in the main manuscript.
