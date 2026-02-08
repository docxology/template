# Symbols and Notation Glossary {#sec:glossary}

This glossary defines the mathematical notation and domain-specific terminology used throughout the manuscript.

## Mathematical Notation

| Symbol | Description | First Use |
|--------|------------|-----------|
| $T$ | Raw text corpus (collection of scientific documents) | Eq. \ref{eq:text_processing} |
| $T_{\text{normalized}}$ | Text after normalization preprocessing | Eq. \ref{eq:text_processing} |
| $T_{\text{tokenized}}$ | Text after domain-aware tokenization | Eq. \ref{eq:text_processing} |
| $T_{\text{lemmatized}}$ | Text after lemmatization | Eq. \ref{eq:text_processing} |
| $\mathcal{T}_d$ | Set of terms classified in domain $d$ | Eq. \ref{eq:term_extraction} |
| $\theta$ | Relevance threshold for term inclusion | Eq. \ref{eq:term_extraction} |
| $G = (V, E)$ | Terminology network (graph with vertices and edges) | Eq. \ref{eq:network_construction} |
| $\phi$ | Relationship threshold for edge inclusion | Eq. \ref{eq:network_construction} |
| $w(u,v)$ | Edge weight between terms $u$ and $v$ | Eq. \ref{eq:network_edge_weight} |
| $n$ | Corpus size (total words or documents) | Eq. \ref{eq:computational_complexity} |
| $m$ | Number of identified terms after extraction | Eq. \ref{eq:computational_complexity} |
| $d$ | Number of Ento-Linguistic domains (fixed at 6) | Eq. \ref{eq:computational_complexity} |

## Ento-Linguistic Domain Abbreviations

| Domain | Abbreviation | Description |
|--------|-------------|-------------|
| Unit of Individuality | UI | Terminology related to biological individuality and scale |
| Behavior and Identity | BI | Language linking behaviors to categorical identities |
| Power \& Labor | PL | Terms derived from human hierarchical systems |
| Sex \& Reproduction | SR | Sex/gender concepts applied to insect biology |
| Kin \& Relatedness | KR | Kinship terminology and relatedness concepts |
| Economics | EC | Economic metaphors for resource allocation |

## Key Metrics

| Metric | Definition | Range |
|--------|-----------|-------|
| Context Variability | Average number of distinct usage contexts per term | $[1, \infty)$ |
| Ambiguity Score | Proportion of usages where term meaning is context-dependent | $[0, 1]$ |
| Clustering Coefficient | Fraction of possible triangles through a node that exist | $[0, 1]$ |
| Betweenness Centrality | Fraction of shortest paths passing through a node | $[0, 1]$ |
| Modularity | Strength of network division into domain communities | $[-0.5, 1]$ |

## Framing Categories

| Framing Type | Definition |
|-------------|------------|
| Anthropomorphic | Application of human attributes or social concepts to insect phenomena |
| Hierarchical | Imposition of power-based ordering on biological organization |
| Economic | Use of market, trade, or resource-investment language for biological processes |
| Kinship-based | Application of human family/relatedness concepts |
| Technological | Use of mechanistic or engineering metaphors |
