# Symbols and Notation Glossary {#sec:glossary}

This glossary defines the mathematical notation and domain-specific terminology used throughout the manuscript.

## Mathematical Notation

| Symbol | Description | First Use |
|--------|-------------|-----------|
| $T$ | Raw text corpus (collection of scientific documents) | Eq. \ref{eq:text_normalization} |
| $T_{\text{normalized}}$ | Text after normalization preprocessing | Eq. \ref{eq:text_normalization} |
| $T_{\text{tokenized}}$ | Text after domain-aware tokenization | Eq. \ref{eq:domain_tokenization} |
| $T_{\text{lemmatized}}$ | Text after lemmatization | Eq. \ref{eq:text_normalization} |
| $\mathcal{T}_d$ | Set of terms classified in domain $d$ | Eq. \ref{eq:term_extraction_score} |
| $\theta$ | Relevance threshold for term inclusion | Eq. \ref{eq:term_extraction_score} |
| $G = (V, E)$ | Terminology network (graph with vertices and edges) | Eq. \ref{eq:edge_weight_computation} |
| $\phi$ | Relationship threshold for edge inclusion | Eq. \ref{eq:edge_weight_computation} |
| $w(u,v)$ | Edge weight between terms $u$ and $v$ | Eq. \ref{eq:edge_weight_computation} |
| $n$ | Corpus size (total words or documents) | Eq. \ref{eq:method_complexity} |
| $m$ | Number of identified terms after extraction | Eq. \ref{eq:method_complexity} |
| $d$ | Number of Ento-Linguistic domains (fixed at 6) | Eq. \ref{eq:method_complexity} |
| $S(t)$ | Term extraction score combining TF-IDF, domain relevance, and linguistic features | Eq. \ref{eq:term_extraction_score} |
| $A(t)$ | Ambiguity score based on contextual entropy and meaning dispersion | Eq. \ref{eq:ambiguity_score} |
| $F(D, T)$ | Discursive framing network function for domain $D$ and term set $T$ | Eq. \ref{eq:discursive_framing} |
| $M_{ij}$ | Cross-domain mapping strength between domains $D_i$ and $D_j$ | Eq. \ref{eq:concept_mapping} |
| $\Delta G(t)$ | Temporal network evolution (graph change over time) | Eq. \ref{eq:temporal_network_evolution} |

## Theoretical Terms

| Term | Definition | Context |
|------|------------|---------|
| **Active Inference** | A corollary of the Free Energy Principle stating that agents act to fulfill the predictions of their generative models. | Sec. \ref{sec:introduction} |
| **Generative Model** | A probabilistic model of how sensory data is generated from latent causes. | Sec. \ref{sec:discussion} |
| **Markov Blanket** | The statistical boundary that separates independent internal states from external states, formally defining the individual. | Sec. \ref{sec:supplemental_analysis} |
| **Stigmergy** | A mechanism of indirect coordination where agents modify the environment to stimulate the actions of others. | Sec. \ref{sec:introduction} |
| **Variational Free Energy** | An information-theoretic quantity that bounds the surprise of a model; biological systems minimize this to maintain integrity. | Sec. \ref{sec:discussion} |

## Pipeline Modules

| Module | File | Function |
|--------|------|----------|
| Text Processing | `src/analysis/text_analysis.py` | Tokenization, normalization, feature extraction |
| Term Extraction | `src/analysis/term_extraction.py` | Domain-aware terminology identification |
| Domain Analysis | `src/analysis/domain_analysis.py` | Per-domain framing and ambiguity analysis |
| Conceptual Mapping | `src/analysis/conceptual_mapping.py` | Cross-domain concept graph construction |
| Discourse Analysis | `src/analysis/discourse_analysis.py` | Framing detection and classification |
| Statistics | `src/analysis/statistics.py` | Statistical validation utilities |
| Visualization | `src/visualization/concept_visualization.py` | Network and domain-specific figure generation |
