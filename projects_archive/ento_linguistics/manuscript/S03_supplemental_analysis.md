# Supplemental Analysis {#sec:supplemental_analysis}

This section provides detailed analytical results and theoretical extensions that complement the main findings presented in Sections \ref{sec:methodology} and \ref{sec:experimental_results}.

## Theoretical Extensions

### Extended Discourse Analysis Frameworks

Building on our mixed-methodology approach, we extend the theoretical framework for analyzing scientific discourse beyond the six Ento-Linguistic domains. Our analysis reveals that terminology networks serve as both descriptive tools and constitutive elements of scientific knowledge production.

**Extended Constitutive Framework**:

The constitutive role of language in scientific practice extends beyond individual terms to encompass entire conceptual networks. We formalize this through the concept of **discursive framing networks**:

\begin{equation}\label{eq:discursive_framing}
F(D, T) = \sum_{t \in T} w_t \cdot f_t(D) \cdot c_t
\end{equation}

where $D$ represents a domain, $T$ is the terminology set, $w_t$ are term weights, $f_t(D)$ is the framing function for domain $D$, and $c_t$ represents contextual factors.

### Advanced Ambiguity Classification Systems

Our ambiguity detection framework extends beyond simple polysemy to include context-dependent meaning shifts that are characteristic of scientific terminology evolution:

**Multi-Level Ambiguity Classification**:

\begin{enumerate}
\item **Lexical Ambiguity**: Multiple dictionary meanings (e.g., "individual" in biological vs. psychological contexts)
\item **Contextual Ambiguity**: Meaning shifts based on research tradition (e.g., "caste" in classical vs. modern entomology)
\item **Scale Ambiguity**: Meaning variations across biological scales (e.g., "behavior" at individual vs. colony levels)
\item **Temporal Ambiguity**: Historical meaning evolution (e.g., "superorganism" from 1970s to present)
\end{enumerate}

### Cross-Domain Conceptual Mapping

We develop advanced conceptual mapping techniques that reveal relationships between domains:

\begin{equation}\label{eq:cross_domain_mapping}
M_{ij} = \frac{1}{|T_i \cap T_j|} \sum_{t \in T_i \cap T_j} s(t, D_i, D_j)
\end{equation}

where $M_{ij}$ is the mapping strength between domains $D_i$ and $D_j$, and $s(t, D_i, D_j)$ measures semantic similarity of term $t$ across domains.

## Extended Framing Analysis Methods

### Anthropomorphic Framing Detection

Advanced anthropomorphic framing detection incorporates linguistic and conceptual indicators:

**Linguistic Indicators**:

- Pronominalization (use of "it" vs. "she/he" for colonies)
- Agency attribution (active vs. passive voice patterns)
- Intentionality markers (words implying purpose or planning)

**Conceptual Indicators**:

- Social structure projections (human hierarchies onto insect societies)
- Emotional attribution (anthropomorphic emotional terms)
- Cultural bias patterns (Western social norms in biological descriptions)

### Hierarchical Framing Analysis

Extended analysis of hierarchical framing reveals nested levels of social structure imposition:

**Macro-Level Hierarchies**: Colony-level social organization (queen → workers → males)

**Micro-Level Hierarchies**: Individual-level interactions (dominant → subordinate nestmates)

**Inter-Colony Hierarchies**: Population-level relationships (territorial dominance, resource competition)

## Advanced Network Analysis Techniques

### Temporal Network Evolution

Analysis of how terminology networks evolve over time reveals conceptual shifts:

\begin{equation}\label{eq:temporal_network_evolution}
\Delta G(t) = G(t+1) - G(t) = \sum_{e \in E} \delta_e(t) + \sum_{v \in V} \delta_v(t)
\end{equation}

where $\delta_e(t)$ and $\delta_v(t)$ represent edge and vertex changes over time periods.

**Key Evolutionary Patterns**:

- **Network Growth**: Addition of new terms and relationships
- **Structural Rearrangements**: Changes in network topology
- **Conceptual Consolidation**: Strengthening of established relationships
- **Paradigm Shifts**: Major restructuring events

### Multi-Scale Network Analysis

Extending network analysis to multiple scales reveals hierarchical organization:

**Local Scale**: Individual term relationships within domains
**Domain Scale**: Inter-term relationships within domains
**Cross-Domain Scale**: Relationships between domains
**Field Scale**: Relationships across the entire entomological terminology network

## Extended Validation Frameworks

### Inter-Subjectivity Validation

Advanced validation incorporates multiple perspectives:

**Expert Validation**: Entomological domain experts review classifications
**Peer Validation**: Interdisciplinary researchers assess cross-domain mappings
**Historical Validation**: Analysis of terminology evolution against known conceptual shifts
**Cross-Cultural Validation**: Comparison with non-English entomological literature

### Robustness Testing

Robustness analysis ensures result stability:

**Subsampling Stability**: Performance across different corpus subsets
**Parameter Sensitivity**: Robustness to algorithmic parameter variations
**Annotation Consistency**: Agreement across multiple human annotators
**Temporal Stability**: Consistency across publication periods

## Advanced Case Study Analysis

### Caste Terminology Evolution: 1850-2024

Ultra-longitudinal analysis reveals century-scale conceptual evolution:

**Pre-Darwinian Period (1850-1859)**: Essentialist caste categories based on morphological differences

**Darwinian Synthesis (1860-1899)**: Evolutionary explanations for caste differences

**Genetic Revolution (1900-1949)**: Chromosomal mechanisms underlying caste determination

**Molecular Biology Era (1950-1999)**: Gene expression and hormonal control of caste differentiation

**Genomic Era (2000-2024)**: Epigenetic and transcriptomic regulation of caste phenotypes \cite{chandra2021epigenetics}, accompanied by calls to broaden conceptions of sociality beyond traditional eusocial models \cite{sociable2025}.

### Superorganism Concept Evolution

Detailed analysis of the superorganism concept across seven decades:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|}
\hline
\textbf{Era} & \textbf{Dominant Metaphor} & \textbf{Key Evidence} & \textbf{Critiques} & \textbf{Legacy} \\
\hline
1960s & Organismic & Division of labor analogies & Ignores individual variation & Established field \\
1970s & Cybernetic & Communication networks & Mechanistic reductionism & Systems thinking \\
1980s & Genetic & Kin selection theory & Haplodiploidy focus & Evolutionary framework \\
1990s & Neuroendocrine & Pheromonal control & Colony complexity & Regulatory mechanisms \\
2000s & Epigenetic & DNA methylation & Environmental effects & Developmental plasticity \\
2010s & Microbiome & Symbiont communities & Host-symbiont dynamics & Extended organism concept \\
\hline
\end{tabular}
\caption{Evolution of superorganism concept across research eras}
\label{tab:superorganism_concept_evolution}
\end{table}

## Methodological Reflections

### Mixed-Methodology Integration

Our approach successfully integrates qualitative and quantitative methods:

**Qualitative Contributions**:

- Theoretical framework development
- Conceptual category identification
- Historical context analysis
- Cross-domain relationship mapping

**Quantitative Contributions**:

- Statistical pattern identification
- Network structure analysis
- Temporal trend quantification
- Validation metric development

For a discussion of methodological limitations and scope considerations, see Section \ref{sec:discussion}. Future research directions, including advanced semantic analysis (transformer-based embeddings, multilingual extensions) and practical applications (terminology standards, peer review tools), are discussed in Section \ref{sec:conclusion}.
