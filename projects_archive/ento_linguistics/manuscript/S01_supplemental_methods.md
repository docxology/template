# Supplemental Methods {#sec:supplemental_methods}

This section provides detailed methodological information supplementing Section \ref{sec:methodology}, focusing on the computational implementation of Ento-Linguistic analysis.

## Text Processing Pipeline Implementation

### Multi-Stage Text Normalization

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

### Linguistic Preprocessing Pipeline

The preprocessing pipeline includes:

1. **Unicode Normalization**: Standardizing character encodings
2. **Case Folding**: Converting to lowercase for consistency
3. **Punctuation Handling**: Removing or preserving scientific notation
4. **Number Normalization**: Standardizing numerical expressions
5. **Stop Word Filtering**: Domain-aware removal of non-informative terms
6. **Lemmatization**: Reducing words to base forms using scientific dictionaries

## Terminology Extraction Algorithms

### Domain-Specific Term Identification

Terminology extraction uses a multi-criteria approach combining statistical and linguistic features:

\begin{equation}\label{eq:term_extraction_score}
S(t) = \alpha \cdot \text{TF-IDF}(t) + \beta \cdot \text{domain_relevance}(t) + \gamma \cdot \text{linguistic_features}(t)
\end{equation}

where weights $\alpha, \beta, \gamma$ are calibrated for each Ento-Linguistic domain.

**Domain Relevance Scoring**: Terms are scored for relevance to specific domains using:

- **Co-occurrence Patterns**: Terms frequently appearing with domain indicators
- **Semantic Similarity**: Vector similarity to domain seed terms
- **Contextual Features**: Syntactic patterns characteristic of domain usage

### Ambiguity Detection Framework

Ambiguity detection identifies terms with context-dependent meanings:

\begin{equation}\label{eq:ambiguity_score}
A(t) = \frac{H(\text{contexts}(t))}{\log |\text{contexts}(t)|} \cdot \frac{|\text{meanings}(t)|}{\text{frequency}(t)}
\end{equation}

where $H(\text{contexts}(t))$ is the entropy of contextual usage patterns, measuring dispersion across different research contexts.

## Network Construction and Analysis

### Edge Weight Calculation

Network edges are weighted using multiple co-occurrence measures:

\begin{equation}\label{eq:edge_weight_computation}
w(u,v) = \frac{1}{3} \left[ \frac{\text{co-occurrence}(u,v)}{\max(\text{freq}(u), \text{freq}(v))} + \text{Jaccard}(u,v) + \text{cosine}(\vec{u}, \vec{v}) \right]
\end{equation}

where co-occurrence is measured within sliding windows, Jaccard similarity captures set overlap, and cosine similarity measures semantic relatedness.

### Community Detection Algorithms

We implement multiple community detection approaches:

**Modularity Optimization**:
\begin{equation}\label{eq:modularity}
Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)
\end{equation}

**Domain-Aware Clustering**: Communities are constrained to respect Ento-Linguistic domain boundaries while allowing cross-domain bridging terms.

### Network Validation Metrics

Network quality is assessed using:

\begin{equation}\label{eq:network_validation}
V(G) = \alpha \cdot \text{modularity}(G) + \beta \cdot \text{conductance}(G) + \gamma \cdot \text{domain_purity}(G)
\end{equation}

where domain purity measures the extent to which communities correspond to Ento-Linguistic domains.

## Framing Analysis Implementation

### Anthropomorphic Framing Detection

Anthropomorphic language is detected through:

**Lexical Indicators**: Terms suggesting human-like agency or intentionality
**Syntactic Patterns**: Sentence structures implying human-like behavior
**Semantic Fields**: Clusters of terms drawing from human social domains

**Detection Algorithm**:
\begin{equation}\label{eq:anthropomorphic_score}
A_{\text{anthro}}(t) = \sum_{f \in F_{\text{human}}} \text{similarity}(t, f) \cdot w_f
\end{equation}

where $F_{\text{human}}$ contains human social concept features and $w_f$ are calibrated weights.

### Hierarchical Framing Analysis

Hierarchical structures are identified by:

**Term Relationship Patterns**: Chains of subordination (superior → subordinate)
**Power Dynamic Indicators**: Terms implying authority, control, or submission
**Organizational Metaphors**: Language drawing from human institutional structures

## Validation Framework Implementation

### Computational Validation Procedures

**Terminology Extraction Validation**:

- **Precision**: Manual verification of extracted terms against expert-curated lists
- **Recall**: Coverage assessment against domain glossaries
- **Domain Accuracy**: Correct classification into Ento-Linguistic domains

**Network Validation**:

- **Structural Validity**: Comparison against null models
- **Domain Correspondence**: Alignment with theoretical domain boundaries
- **Stability Analysis**: Consistency across subsampling procedures

### Theoretical Validation Methods

**Inter-coder Agreement**: Multiple researchers code ambiguous passages to assess consistency.

**Theoretical Saturation**: Iterative analysis until theoretical categories are developed.

**Member Checking**: Expert review of interpretations and categorizations.

## Implementation Architecture

### Modular Software Design

The implementation follows a modular architecture organized under the `src/` package:

```text
src/
├── analysis/           # Core analytical modules
│   ├── text_analysis.py        # TextProcessor, LinguisticFeatureExtractor
│   ├── term_extraction.py      # TerminologyExtractor, Term dataclass
│   ├── domain_analysis.py      # DomainAnalyzer, DomainAnalysis dataclass
│   ├── conceptual_mapping.py   # ConceptualMapper, concept graph construction
│   ├── discourse_analysis.py   # DiscourseAnalyzer, framing detection
│   ├── statistics.py           # Statistical validation utilities
│   └── performance.py          # Performance benchmarking
├── core/               # Shared infrastructure and utilities
├── data/               # Domain seed data and corpus resources
├── pipeline/           # End-to-end orchestration
└── visualization/      # ConceptVisualizer, VisualizationEngine
```

### Data Structures and Formats

**Term Representation** (from `src/analysis/term_extraction.py`):

```python
@dataclass
class Term:
    text: str               # The term text
    lemma: str              # Lemmatized form
    domains: List[str]      # Ento-Linguistic domains
    frequency: int          # Total frequency across corpus
    contexts: List[str]     # Contextual usage examples
    pos_tags: List[str]     # Part-of-speech tags
    confidence: float       # Extraction confidence score
```

**Domain Analysis Results** (from `src/analysis/domain_analysis.py`):

```python
@dataclass
class DomainAnalysis:
    domain_name: str
    key_terms: List[str]                        # Most important terms
    term_patterns: Dict[str, int]               # Linguistic pattern counts
    framing_assumptions: List[str]              # Identified framings
    conceptual_structure: Dict[str, Any]        # Concept organization
    ambiguities: List[Dict[str, Any]]           # Ambiguity contexts
    recommendations: List[str]                  # Communication suggestions
    frequency_stats: Dict[str, Any]             # Term frequency analysis
    cooccurrence_analysis: Dict[str, Any]       # Co-occurrence patterns
    ambiguity_metrics: Dict[str, Any]           # Quantified ambiguity
    confidence_scores: Dict[str, float]         # Framing confidence
    conceptual_metrics: Dict[str, Any]          # Conceptual structure metrics
    statistical_significance: Dict[str, Any]    # Significance results
```

### Performance Optimization

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

## Parameter Calibration and Sensitivity

### Algorithm Parameters

Critical parameters and their calibration:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|}
\hline
\textbf{Parameter} & \textbf{Default} & \textbf{Range} & \textbf{Impact} & \textbf{Calibration Method} \\
\hline
Co-occurrence Window & 10 & [5, 50] & High & Cross-validation \\
Similarity Threshold & 0.3 & [0.1, 0.8] & High & Domain expert review \\
Minimum Frequency & 3 & [1, 50] & Medium & Statistical significance \\
Ambiguity Threshold & 0.7 & [0.5, 0.9] & Medium & Manual validation \\
\hline
\end{tabular}
\caption{Algorithm parameter calibration and sensitivity analysis}
\label{tab:parameter_calibration}
\end{table}

### Sensitivity Analysis Results

Parameter sensitivity testing revealed:

**Co-occurrence Window**: Default of 10 words for co-occurrence analysis balances sensitivity with specificity; context extraction uses a narrower 3-word window for precise usage examples.

**Similarity Threshold**: 0.3 provides balance between precision and recall; lower values increase false positives, higher values miss subtle relationships.

**Frequency Threshold**: Default of 3 occurrences ensures statistical reliability while maintaining coverage for smaller corpora.

## Quality Assurance and Reproducibility

### Automated Quality Checks

**Data Quality Validation**:

- Text encoding verification
- Corpus completeness checks
- Metadata consistency validation

**Algorithmic Validation**:

- Deterministic output verification
- Cross-platform compatibility testing
- Performance regression monitoring

### Reproducibility Framework

**Version Control**: All code, data, and parameters are version controlled via Git for reproducibility and traceability.

**Environment Management**: Analysis environments are managed using `uv` with pinned dependencies in `pyproject.toml` for reproducible installations.

**Documentation**: Comprehensive documentation of all processing steps, parameters, and decisions.

**Software Dependencies**: Analysis conducted using Python 3.10+, NLTK 3.8+ (tokenization/text processing), NetworkX 3.2+ (network construction), scikit-learn 1.3+ (statistical validation), pandas 2.0+ (data manipulation), matplotlib 3.7+ and seaborn 0.13+ (visualization), NumPy 1.24+ and SciPy 1.10+ (numerical computation).

## Extended Mathematical Formulations

### Conceptual Mapping Framework

The conceptual mapping algorithm formalizes term relationships across contexts:

\begin{equation}\label{eq:concept_mapping}
M(t_i, t_j) = \frac{1}{k} \sum_{c=1}^k \text{similarity}(\vec{t_i}^{(c)}, \vec{t_j}^{(c)})
\end{equation}

where $k$ represents the number of contextual embeddings and $\vec{t}^{(c)}$ is the embedding of a term in context $c$.

### Discourse Pattern Recognition

Discourse pattern detection uses sequence modeling:

\begin{equation}\label{eq:discourse_patterns}
P(d|t_1, \dots, t_n) = \prod_{i=1}^n P(t_i|t_{i-1}, d) \cdot P(d)
\end{equation}

where $d$ represents discourse patterns and $t_i$ are sequential terms.

## Performance and Scalability

### Computational Complexity

The pipeline's overall time complexity is:

\begin{equation}\label{eq:computational_complexity}
C(n,m) = O(n \log n + m \cdot d)
\end{equation}

where $n$ is the corpus size (total words or documents), $m$ is the number of extracted terms, and $d = 6$ is the fixed number of Ento-Linguistic domains. The $n \log n$ term covers text preprocessing and tokenization; $m \cdot d$ represents domain classification and per-domain analysis.

### Memory and Resource Management

**Streaming Processing**: Documents are processed incrementally so that the full corpus need not reside in memory simultaneously.

**Incremental Network Construction**: Edge weights and community structure update incrementally as new documents are added, ensuring that network analysis scales linearly with additional data.

**Parallel Processing**: Because domain analyses are independent, they can be distributed across multiple cores or machines without inter-process synchronization.

### Automated Quality Gates

The following gates run automatically at each pipeline stage:

1. **Text Processing Validation**: Round-trip verification and comparison against manually processed subsets ensure preprocessing preserves semantic integrity.
2. **Terminology Validation**: Extracted terms are cross-referenced against expert-curated seed lists and published entomological glossaries.
3. **Network Validation**: Constructed networks are compared against null models (random networks with preserved degree distributions) to confirm that observed structure is statistically meaningful.
4. **Theoretical Validation**: Decision criteria and interpretation chains are documented at each analytical stage to maintain conceptual coherence.

This detailed methodological framework ensures rigorous, reproducible Ento-Linguistic analysis while maintaining flexibility for methodological refinement and extension.
