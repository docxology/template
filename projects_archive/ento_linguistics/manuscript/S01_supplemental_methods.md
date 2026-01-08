# Supplemental Methods {#sec:supplemental_methods}

This section provides detailed methodological information supplementing Section \ref{sec:methodology}, focusing on the computational implementation of Ento-Linguistic analysis.

## S1.1 Text Processing Pipeline Implementation

### S1.1.1 Multi-Stage Text Normalization

Our text processing pipeline implements systematic normalization to ensure reliable pattern detection:

\begin{equation}\label{eq:text_normalization}
T_{\text{normalized}} = \text{lowercase}(\text{strip_punct}(\text{unicode_normalize}(T)))
\end{equation}

where $T$ represents raw text input and each transformation step standardizes linguistic variation while preserving semantic content.

**Tokenization Strategy**: We employ domain-aware tokenization that recognizes scientific terminology:

\begin{equation}\label{eq:domain_tokenization}
\tau(T) = \bigcup_{t \in T} \left\{\begin{array}{ll}
t & \text{if } t \in \mathcal{T}_{\text{scientific}} \\
\text{word\_tokenize}(t) & \text{otherwise}
\end{array}\right.
\end{equation}

where $\mathcal{T}_{\text{scientific}}$ contains curated scientific terminology that should not be further subdivided.

### S1.1.2 Linguistic Preprocessing Pipeline

The preprocessing pipeline includes:

1. **Unicode Normalization**: Standardizing character encodings
2. **Case Folding**: Converting to lowercase for consistency
3. **Punctuation Handling**: Removing or preserving scientific notation
4. **Number Normalization**: Standardizing numerical expressions
5. **Stop Word Filtering**: Domain-aware removal of non-informative terms
6. **Lemmatization**: Reducing words to base forms using scientific dictionaries

## S1.2 Terminology Extraction Algorithms

### S1.2.1 Domain-Specific Term Identification

Terminology extraction uses a multi-criteria approach combining statistical and linguistic features:

\begin{equation}\label{eq:term_extraction_score}
S(t) = \alpha \cdot \text{TF-IDF}(t) + \beta \cdot \text{domain_relevance}(t) + \gamma \cdot \text{linguistic_features}(t)
\end{equation}

where weights $\alpha, \beta, \gamma$ are calibrated for each Ento-Linguistic domain.

**Domain Relevance Scoring**: Terms are scored for relevance to specific domains using:

- **Co-occurrence Patterns**: Terms frequently appearing with domain indicators
- **Semantic Similarity**: Vector similarity to domain seed terms
- **Contextual Features**: Syntactic patterns characteristic of domain usage

### S1.2.2 Ambiguity Detection Framework

Ambiguity detection identifies terms with context-dependent meanings:

\begin{equation}\label{eq:ambiguity_score}
A(t) = \frac{H(\text{contexts}(t))}{\log |\text{contexts}(t)|} \cdot \frac{|\text{meanings}(t)|}{\text{frequency}(t)}
\end{equation}

where $H(\text{contexts}(t))$ is the entropy of contextual usage patterns, measuring dispersion across different research contexts.

## S1.3 Network Construction and Analysis

### S1.3.1 Edge Weight Calculation

Network edges are weighted using multiple co-occurrence measures:

\begin{equation}\label{eq:edge_weight_computation}
w(u,v) = \frac{1}{3} \left[ \frac{\text{co-occurrence}(u,v)}{\max(\text{freq}(u), \text{freq}(v))} + \text{Jaccard}(u,v) + \text{cosine}(\vec{u}, \vec{v}) \right]
\end{equation}

where co-occurrence is measured within sliding windows, Jaccard similarity captures set overlap, and cosine similarity measures semantic relatedness.

### S1.3.2 Community Detection Algorithms

We implement multiple community detection approaches:

**Modularity Optimization**:
\begin{equation}\label{eq:modularity}
Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)
\end{equation}

**Domain-Aware Clustering**: Communities are constrained to respect Ento-Linguistic domain boundaries while allowing cross-domain bridging terms.

### S1.3.3 Network Validation Metrics

Network quality is assessed using:

\begin{equation}\label{eq:network_validation}
V(G) = \alpha \cdot \text{modularity}(G) + \beta \cdot \text{conductance}(G) + \gamma \cdot \text{domain_purity}(G)
\end{equation}

where domain purity measures the extent to which communities correspond to Ento-Linguistic domains.

## S1.4 Framing Analysis Implementation

### S1.4.1 Anthropomorphic Framing Detection

Anthropomorphic language is detected through:

**Lexical Indicators**: Terms suggesting human-like agency or intentionality
**Syntactic Patterns**: Sentence structures implying human-like behavior
**Semantic Fields**: Clusters of terms drawing from human social domains

**Detection Algorithm**:
\begin{equation}\label{eq:anthropomorphic_score}
A_{\text{anthro}}(t) = \sum_{f \in F_{\text{human}}} \text{similarity}(t, f) \cdot w_f
\end{equation}

where $F_{\text{human}}$ contains human social concept features and $w_f$ are calibrated weights.

### S1.4.2 Hierarchical Framing Analysis

Hierarchical structures are identified by:

**Term Relationship Patterns**: Chains of subordination (superior → subordinate)
**Power Dynamic Indicators**: Terms implying authority, control, or submission
**Organizational Metaphors**: Language drawing from human institutional structures

## S1.5 Validation Framework Implementation

### S1.5.1 Computational Validation Procedures

**Terminology Extraction Validation**:
- **Precision**: Manual verification of extracted terms against expert-curated lists
- **Recall**: Coverage assessment against domain glossaries
- **Domain Accuracy**: Correct classification into Ento-Linguistic domains

**Network Validation**:
- **Structural Validity**: Comparison against null models
- **Domain Correspondence**: Alignment with theoretical domain boundaries
- **Stability Analysis**: Consistency across subsampling procedures

### S1.5.2 Theoretical Validation Methods

**Inter-coder Agreement**: Multiple researchers code ambiguous passages to assess consistency.

**Theoretical Saturation**: Iterative analysis until theoretical categories are developed.

**Member Checking**: Expert review of interpretations and categorizations.

## S1.6 Implementation Architecture

### S1.6.1 Modular Software Design

The implementation follows a modular architecture:

```
entolinguistic/
├── text_processing/     # Text normalization and tokenization
├── terminology/         # Term extraction and classification
├── networks/           # Graph construction and analysis
├── framing/            # Framing analysis algorithms
├── validation/         # Validation and quality assurance
└── visualization/      # Result visualization
```

### S1.6.2 Data Structures and Formats

**Terminology Database**:
```python
@dataclass
class TerminologyEntry:
    term: str
    domains: List[str]
    contexts: List[str]
    frequencies: Dict[str, int]
    ambiguities: List[str]
    framings: List[str]
```

**Network Representation**:
```python
@dataclass
class TerminologyNetwork:
    nodes: Dict[str, TerminologyEntry]
    edges: Dict[Tuple[str, str], float]
    communities: Dict[str, List[str]]
    domain_mappings: Dict[str, str]
```

### S1.6.3 Performance Optimization

**Scalability Considerations**:
- Streaming processing for large corpora
- Incremental network updates
- Parallel processing for independent analyses
- Memory-efficient data structures for large networks

**Computational Complexity**:
\begin{equation}\label{eq:method_complexity}
C(n,m,d) = O(n \log n + m \cdot d + e \cdot \log e)
\end{equation}

where $n$ is corpus size, $m$ is extracted terms, $d$ is domains, and $e$ is network edges.

## S1.7 Parameter Calibration and Sensitivity

### S1.7.1 Algorithm Parameters

Critical parameters and their calibration:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|}
\hline
\textbf{Parameter} & \textbf{Default} & \textbf{Range} & \textbf{Impact} & \textbf{Calibration Method} \\
\hline
Window Size & 50 & [20, 100] & High & Cross-validation \\
Similarity Threshold & 0.3 & [0.1, 0.8] & High & Domain expert review \\
Minimum Frequency & 5 & [1, 50] & Medium & Statistical significance \\
Ambiguity Threshold & 0.7 & [0.5, 0.9] & Medium & Manual validation \\
\hline
\end{tabular}
\caption{Algorithm parameter calibration and sensitivity analysis}
\label{tab:parameter_calibration}
\end{table}

### S1.7.2 Sensitivity Analysis Results

Parameter sensitivity testing revealed:

**Window Size**: Optimal at 50 words; smaller windows miss long-range relationships, larger windows introduce noise.

**Similarity Threshold**: 0.3 provides balance between precision and recall; lower values increase false positives, higher values miss subtle relationships.

**Frequency Threshold**: 5 occurrences ensures statistical reliability while maintaining coverage.

## S1.8 Quality Assurance and Reproducibility

### S1.8.1 Automated Quality Checks

**Data Quality Validation**:
- Text encoding verification
- Corpus completeness checks
- Metadata consistency validation

**Algorithmic Validation**:
- Deterministic output verification
- Cross-platform compatibility testing
- Performance regression monitoring

### S1.8.2 Reproducibility Framework

**Version Control**: All code, data, and parameters are version controlled with DOI minting for long-term access.

**Containerization**: Analysis environments are containerized for exact reproducibility.

**Documentation**: documentation of all processing steps, parameters, and decisions.

## S1.9 Extensions and Future Methods

### S1.9.1 Advanced Semantic Analysis

Future extensions include:

**Transformer-based Embeddings**: Using contextual language models for more sophisticated semantic analysis.

**Multilingual Extensions**: Cross-language terminology mapping and comparison.

**Temporal Analysis**: Tracking terminological evolution over time using diachronic methods.

### S1.9.2 Integration with External Resources

**Ontology Integration**: Mapping to existing biological ontologies and terminologies.

**Citation Network Analysis**: Integrating citation patterns with terminology usage.

**Author Network Analysis**: Examining how terminology use correlates with research communities.

This detailed methodological framework ensures rigorous, reproducible Ento-Linguistic analysis while maintaining flexibility for methodological refinement and extension.




