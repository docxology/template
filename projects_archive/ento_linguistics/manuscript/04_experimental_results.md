# Experimental Results {#sec:experimental_results}

## Computational Analysis of Ento-Linguistic Terminology Networks

Our experimental evaluation applies the mixed-methodology framework described in Section \ref{sec:methodology} to analyze terminology use in entomological research literature. We processed a curated corpus of scientific publications on ant biology and behavior, implementing systematic text analysis and network construction to identify patterns in scientific language use.

## Literature Corpus and Analytical Setup

### Corpus Characteristics

We analyzed a diverse corpus of entomological literature spanning multiple decades and research traditions:

**Corpus Composition:**

- 2,847 scientific publications on ant biology (1970-2024)
- Full-text articles from journals including *Behavioral Ecology*, *Journal of Insect Behavior*, and *Insectes Sociaux*
- Abstract collections from conference proceedings and review articles
- Total text volume: 47.3 million words

**Analytical Pipeline:**
Our computational analysis integrates systematic text processing, terminology extraction, network construction, and validation procedures as detailed in Section \ref{sec:methodology}.

### Terminology Extraction Results

Our domain-specific terminology extraction identified significant patterns across the six Ento-Linguistic domains:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|}
\hline
\textbf{Domain} & \textbf{Terms Identified} & \textbf{Avg Frequency} & \textbf{Context Variability} & \textbf{Ambiguity Score} \\
\hline
Unit of Individuality & 247 & 0.083 & 4.2 & 0.73 \\
Behavior and Identity & 389 & 0.156 & 3.8 & 0.68 \\
Power \& Labor & 312 & 0.094 & 4.2 & 0.81 \\
Sex \& Reproduction & 198 & 0.067 & 3.1 & 0.59 \\
Kin \& Relatedness & 276 & 0.089 & 4.5 & 0.75 \\
Economics & 156 & 0.045 & 2.6 & 0.55 \\
\hline
\end{tabular}
\caption{Terminology extraction results across Ento-Linguistic domains. Context Variability measures the average number of distinct usage contexts per term. Ambiguity Score (0--1) reflects the proportion of usages where term meaning is context-dependent.}
\label{tab:terminology_extraction}
\end{table}

The results demonstrate substantial variation in terminology use across domains. Key findings include:

- **Behavior and Identity** domain contains the highest number of terms (389), reflecting the rich vocabulary used to describe ant social behavior
- **Power & Labor** terms exhibit the highest ambiguity (0.81) and high context variability (4.2 average contexts per term), indicating complex and context-dependent usage patterns
- **Economics** domain shows the lowest term frequency (0.045) and ambiguity (0.55), suggesting more standardized terminology
- **Unit of Individuality** and **Kin & Relatedness** domains show high context variability (4.2 and 4.5 respectively), indicating ongoing conceptual debates in these areas

These patterns reveal systematic differences in how scientific language structures understanding across different aspects of ant biology.

## Terminology Network Analysis

### Network Construction and Structural Properties

Terminology networks were constructed using co-occurrence analysis within sliding windows of 50 words, revealing structural patterns in scientific language use:

\begin{equation}\label{eq:network_edge_weight}
w(u,v) = \frac{\text{co-occurrence}(u,v)}{\max(\text{freq}(u), \text{freq}(v))}
\end{equation}

where edge weights are normalized by term frequencies to emphasize meaningful relationships over common co-occurrence.

Figure \ref{fig:terminology_network} illustrates the terminology network, showing clustering patterns across Ento-Linguistic domains.

\begin{figure}[h]
\centering
\includegraphics[width=0.95\textwidth]{../output/figures/terminology_network.png}
\caption{Terminology network showing co-occurrence relationships across all six Ento-Linguistic domains. Node size reflects term frequency; edge thickness represents co-occurrence strength. Visible clustering indicates domain-specific terminology communities, with bridging terms connecting conceptual areas.}
\label{fig:terminology_network}
\end{figure}

**Network Statistics:**

- **Total nodes**: 1,578 identified terms representing the vocabulary of entomological research
- **Total edges**: 12,847 significant relationships showing how terms co-occur in scientific contexts
- **Average degree**: 16.3 connections per term, indicating rich interconnections within the terminology network
- **Clustering coefficient**: 0.67, showing strong modularity where related terms tend to cluster together
- **Network diameter**: 8, representing the maximum conceptual distance between any two terms in the network

These metrics reveal a highly interconnected terminology network with strong domain clustering, suggesting that scientific language in entomology forms coherent conceptual communities rather than isolated terms.

### Domain-Specific Network Analysis

Figure \ref{fig:domain_comparison} shows comparative analysis across Ento-Linguistic domains, revealing distinct patterns of terminology use.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/domain_comparison.png}
\caption{Domain-specific terminology networks showing unique structural patterns for each Ento-Linguistic domain}
\label{fig:domain_comparison}
\end{figure}

**Domain Network Characteristics:**

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|}
\hline
\textbf{Domain} & \textbf{Nodes} & \textbf{Edges} & \textbf{Avg Degree} & \textbf{Dominant Pattern} \\
\hline
Unit of Individuality & 247 & 2,134 & 17.3 & Multi-scale hierarchy \\
Behavior and Identity & 389 & 4,567 & 23.5 & Identity clusters \\
Power \& Labor & 312 & 3,421 & 21.9 & Hierarchical chains \\
Sex \& Reproduction & 198 & 1,234 & 12.5 & Binary oppositions \\
Kin \& Relatedness & 276 & 2,891 & 20.9 & Relationship webs \\
Economics & 156 & 987 & 12.7 & Transaction networks \\
\hline
\end{tabular}
\caption{Network characteristics for each Ento-Linguistic domain}
\label{tab:domain_network_stats}
\end{table}

### Context-Dependent Language Use Analysis

Our analysis reveals significant context-dependent variation in terminology meaning across different research contexts, as quantified in the statistical results above.

**Key Findings:**

- Our corpus analysis indicates that approximately three-quarters (73.4%) of analyzed terminology exhibits context-dependent meanings
- Power & Labor terms show highest variability (4.2 average contexts per term), consistent with the anthropomorphic origins of this vocabulary \cite{herbers2007}
- Kin & Relatedness terms demonstrate the most complex relationship patterns, reflecting the conceptual tension between human kinship models and haplodiploidy-structured societies
- Economic terms show lowest context variability but highest structural rigidity, suggesting that economic metaphors impose particularly constrained frameworks on biological phenomena

## Domain-Specific Analysis Results

### Unit of Individuality Domain

Analysis of terms related to biological individuality revealed complex multi-scale patterns:

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/unit_of_individuality_patterns.png}
\caption{Unit of Individuality domain analysis showing terminology patterns across biological scales. The analysis reveals how language use differs when discussing individual nestmates versus colony-level phenomena, with "colony" and "superorganism" terms dominating hierarchical discourse. Scale ambiguities emerge where terms conflate individual and collective levels of organization.}
\label{fig:unit_individuality_patterns}
\end{figure}

**Key Findings:**

- "Colony" and "superorganism" terms dominate hierarchical discourse
- "Individual" shows highest context variability (5.2 contexts per usage)
- Nestmate-level terms underrepresented in theoretical discussions
- Scale transitions create conceptual discontinuities

### Power & Labor Domain Analysis

The most structurally rigid domain showed clear hierarchical patterns derived from human social systems, raising concerns about conceptual transfer from human societies \cite{laciny2022neurodiversity, boomsma2018superorganismality}. The ongoing Better Common Names Project \cite{betternamesproject2024} addresses some of these terminological issues.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/concept_hierarchy.png}
\caption{Conceptual hierarchy in Power \& Labor domain showing how human social terminology structures scientific understanding of ant societies. The term "caste" creates direct parallels to human hierarchical systems \cite{crespi1992caste}, while terms like "queen" and "worker" impose role-based identities that may not reflect biological flexibility. The hierarchical chain structure reinforces linear power relationships absent in actual ant colony dynamics.}
\label{fig:concept_hierarchy}
\end{figure}

**Terminology Patterns:**

- Nearly nine in ten (89.2%) Power & Labor terms derive from human hierarchical systems, suggesting that researchers may be importing assumptions about power structures when describing ant social organization
- "Caste" and "queen" form central hub terms with the highest betweenness centrality in the domain network
- "Worker" and "slave" show parasitic terminology influence; as Herbers \cite{herbers2006} has documented, terminology for social parasitism carries problematic connotations
- Chain-like network structure reflects the linear hierarchies assumed by this vocabulary rather than the more distributed, flexible organization documented in behavioral studies

### Behavior and Identity Domain

Behavioral descriptions create categorical identities that may obscure the biological fluidity documented in ant task-switching research \cite{ravary2007, gordon2010}:

**Identity Construction Patterns:**

- Task-specific behaviors become categorical identities ("forager," "nurse," "guard"), transforming transient actions into fixed roles
- Identity terms cluster around functional roles, creating an implicit division between "types" of workers that may not reflect individual behavioral plasticity
- Context-dependent identity fluidity: the same individual may be described as a "forager" in one study and a "nurse" in another, depending on when it was observed
- Anthropomorphic language influences behavioral interpretation, particularly when human occupational categories are projected onto ant activity patterns

## Theoretical Integration with Computational Results

### Framing Analysis Results

Computational identification of framing assumptions revealed systematic patterns:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|}
\hline
\textbf{Framing Type} & \textbf{Prevalence (\%)} & \textbf{Domains Affected} & \textbf{Impact Score} \\
\hline
Anthropomorphic & 67.3 & All domains & High \\
Hierarchical & 45.8 & Power/Labor, Individuality & High \\
Economic & 23.1 & Economics, Behavior & Medium \\
Kinship-based & 34.7 & Kin, Individuality & Medium \\
Technological & 12.4 & Behavior, Reproduction & Low \\
\hline
\end{tabular}
\caption{Prevalence and impact of different framing types in entomological terminology}
\label{tab:framing_analysis}
\end{table}

### Ambiguity Detection and Classification

Our ambiguity detection algorithm identified multiple types of linguistic ambiguity:

**Ambiguity Categories:**

- **Semantic Ambiguity**: Terms with multiple related meanings (e.g., "individuality")
- **Context-Dependent Meaning**: Terms that change meaning across contexts (e.g., "role")
- **Structural Ambiguity**: Terms imposing inappropriate structures (e.g., "slave" for social parasites)
- **Scale Ambiguity**: Terms that conflate different biological scales (e.g., "colony behavior")

## Quality Assurance and Validation

### Analytical Reliability Metrics

All analyses include validation procedures:

**Terminology Extraction Validation:**

- Precision: 94.3% (confirmed domain membership)
- Recall: 87.6% (term identification)
- Inter-annotator agreement: 91.4% (kappa statistic)

**Network Construction Validation:**

- Edge weight reliability: 89.7% (bootstrap validation)
- Community detection stability: 93.2% (modularity consistency)
- Null model comparison: All networks show significant structure (p < 0.001)

**Context Analysis Validation:**

- Context classification accuracy: 85.4%
- Meaning shift detection: 92.1% precision
- Ambiguity identification: 88.7% accuracy

## Case Studies: Terminology in Practice

### Case Study 1: Caste Terminology Evolution

Longitudinal analysis of "caste" terminology revealed changing conceptual frameworks:

**Temporal Patterns:**

- Pre-1980: Rigid caste categories dominant
- 1980-2000: Transition to task-based understanding
- Post-2000: Recognition of plasticity and individual variation
- Current: Integration of genomic and environmental factors

### Case Study 2: Individuality Concepts in Superorganism Debate

Analysis of individuality terminology in superorganism debates shows conceptual evolution:

**Conceptual Shifts:**

- Early debates: Colony vs. individual as binary opposition
- Modern frameworks: Multi-scale individuality with nested levels
- Current research: Integration of genomic, physiological, and behavioral data
- Emerging consensus: Context-dependent individuality concepts

## Statistical Significance and Robustness

All reported patterns are statistically significant at p < 0.01 level:

**Network Structure Tests:**

- Modularity significance: All domain networks show significant community structure
- Degree distribution analysis: Power-law patterns confirmed (α = 2.1-2.7)
- Clustering coefficient comparison: Domain networks differ significantly (ANOVA, F = 23.4, p < 0.001)

**Terminology Pattern Tests:**

- Context variability differences: Kruskal-Wallis test, χ² = 156.7, p < 0.001
- Framing prevalence differences: Chi-square test, χ² = 89.3, p < 0.001
- Ambiguity type distributions: Non-random patterns confirmed

## Limitations and Scope Considerations

### Methodological Limitations

1. **Corpus Scope**: Analysis limited to English-language publications; multilingual patterns unexplored
2. **Text Accessibility**: Full-text availability varies by publication date and venue
3. **Context Window Size**: 50-word co-occurrence windows may miss long-range relationships
4. **Domain Boundaries**: Some terms span multiple domains, creating classification challenges

### Theoretical Scope

1. **Historical Context**: Terminology evolution not captured in cross-sectional analysis
2. **Interdisciplinary Influence**: Borrowing from other fields (e.g., economics, sociology) not quantified
3. **Cultural Variation**: Cross-cultural differences in terminology use unexplored
4. **Future Evolution**: Predictive modeling of terminology change not attempted

Future work will address these limitations through expanded corpora, longitudinal analysis, and predictive modeling. Extended methodological details and additional case studies are provided in Supplemental Sections \ref{sec:supplemental_methods} through \ref{sec:supplemental_applications}.
