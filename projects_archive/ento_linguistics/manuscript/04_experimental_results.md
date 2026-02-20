# Experimental Results {#sec:experimental_results}

## Terminology Extraction Across Domains

Our experimental evaluation applies the mixed-methodology framework described in Section \ref{sec:methodology} to a curated corpus of seminal entomological literature. The dataset includes fundamental abstracts defining the field, such as works by Hölldobler, Wilson, and Gordon, incorporating terminology patterns characteristic of journals including *Behavioral Ecology*, *Journal of Insect Behavior*, and *Insectes Sociaux*.

Domain-specific extraction identified **1,841 terms** spanning all six domains, with substantial variation in usage patterns:

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
\caption{Primary domain assignments for extracted terminology. Total unique terms = 1,841; terms shown under primary domain classification ($N=1{,}578$). Remaining 263 terms have cross-domain assignments. Context Variability measures the average number of distinct usage contexts per term. Ambiguity Score (0--1) reflects the proportion of usages where term meaning is context-dependent.}
\label{tab:terminology_extraction}
\end{table}

The 1,841 unique terms identified across the corpus are shown here under their primary domain classification ($N = 1{,}578$). An additional 263 terms receive secondary assignments across multiple domains and are counted once under their highest-confidence primary domain. Table~\ref{tab:extended_terminology} details sub-domain specializations within each domain; its ``Additional Terms'' column reflects sub-domain refinement, not separate terms.

Unit of Individuality and Kin \& Relatedness both exhibit high context variability (4.2 and 4.5), indicating ongoing conceptual debates.

### Sub-Domain Analysis and Extended Terminology

Beyond the aggregate metrics, we identified distinctive terminology patterns within specific sub-domains:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|c|}
\hline
\textbf{Domain} & \textbf{Additional Terms} & \textbf{Sub-domains} & \textbf{Cross-domain Links} & \textbf{Ambiguity Patterns} \\
\hline
Unit of Individuality & 89 & 4 & 156 & Scale transitions \\
Behavior and Identity & 134 & 6 & 203 & Context-dependent roles \\
Power \& Labor & 98 & 3 & 187 & Authority structures \\
Sex \& Reproduction & 67 & 2 & 98 & Binary assumptions \\
Kin \& Relatedness & 76 & 5 & 145 & Relationship complexity \\
Economics & 45 & 2 & 67 & Resource metaphors \\
\hline
\end{tabular}
\caption{Extended terminology extraction showing sub-domain specializations within each primary domain and cross-domain relationship counts. ``Additional Terms'' represent sub-domain refinements of the primary terms in Table~\ref{tab:terminology_extraction}, not separate terms.}
\label{tab:extended_terminology}
\end{table}

Key sub-domains driving these patterns include:

- **Unit of Individuality**: Splits into colony-level concepts (e.g., *superorganism*), individual-level concepts (e.g., *nestmate recognition*), and scale-transition terms.
- **Behavior and Identity**: Distinct vocabularies for task specialization (e.g., *foraging*), age-related roles (*temporal polyethism*), and context-dependent flexibility.

## Terminology Network Structure

Terminology networks were constructed using co-occurrence analysis within configurable sliding windows (default 10 words). Edge weights are normalized by term frequencies to emphasize meaningful relationships:

\begin{equation}\label{eq:network_edge_weight}
w(u,v) = \frac{\text{co-occurrence}(u,v)}{\max(\text{freq}(u), \text{freq}(v))}
\end{equation}

Figure \ref{fig:terminology_network} illustrates the resulting network.

\begin{figure}[h]
\centering
\includegraphics[width=0.95\textwidth]{../output/figures/terminology_network.png}
\caption{Terminology network showing co-occurrence relationships across all six Ento-Linguistic domains. Node size reflects term frequency; edge thickness represents co-occurrence strength. Visible clustering indicates domain-specific terminology communities, with bridging terms connecting conceptual areas.}
\label{fig:terminology_network}
\end{figure}

The network exhibits strong modularity: 1,578 nodes connected by 12,847 edges, with a clustering coefficient of 0.67 and average degree of 16.3. These metrics indicate a highly interconnected terminology structure with coherent domain clustering—scientific language in entomology forms conceptual communities rather than isolated terms.

Domain-level network analysis reveals distinct architectures:

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

Extended structural analysis further characterizes these networks (Table \ref{tab:extended_network_properties}). The conceptual bridges between domains are visualized in Figure \ref{fig:domain_overlap}.

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|c|}
\hline
\textbf{Network Property} & \textbf{Unit} & \textbf{Behavior} & \textbf{Power} & \textbf{Sex} & \textbf{Economics} \\
\hline
Betweenness Centrality & 0.23 & 0.31 & 0.18 & 0.12 & 0.09 \\
Clustering Coefficient & 0.67 & 0.71 & 0.58 & 0.62 & 0.55 \\
Average Path Length & 3.2 & 2.8 & 3.7 & 4.1 & 3.9 \\
Network Diameter & 8 & 7 & 9 & 10 & 8 \\
Small World Coefficient & 2.1 & 2.3 & 1.8 & 1.9 & 1.7 \\
\hline
\end{tabular}
\caption{Extended network structural properties across all Ento-Linguistic domains}
\label{tab:extended_network_properties}
\end{table}

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/domain_overlap_heatmap.png}
\caption{Domain overlap heatmap showing the proportion of shared terminology between each pair of Ento-Linguistic domains. Darker cells indicate higher overlap; the Power \& Labor / Economics pair shows the strongest cross-domain sharing (0.34), while Unit of Individuality / Sex \& Reproduction shows the weakest (0.08). Off-diagonal asymmetry reflects directional borrowing patterns.}
\label{fig:domain_overlap}
\end{figure}

Distinctive cross-domain bridges include:

- **Power & Labor $\leftrightarrow$ Behavior and Identity**: Mechanisms of role assignment.
- **Unit of Individuality $\leftrightarrow$ Kin & Relatedness**: Foundations of social structure.
- **Economics $\leftrightarrow$ Power & Labor**: Resource distribution hierarchies.

Figure \ref{fig:domain_comparison} shows the comparative analysis across domains.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/domain_comparison.png}
\caption{Cross-domain comparison of terminology characteristics across all six Ento-Linguistic domains. The four panels show (top-left) the number of distinct terms extracted per domain, (top-right) the average confidence score assigned during extraction, (bottom-left) cumulative term frequency across the corpus, and (bottom-right) the mean ambiguity score quantifying context-dependent meaning variation. Domains with higher ambiguity scores contain terms whose meanings shift more substantially across research contexts, indicating areas where terminological reform may be most impactful.}
\label{fig:domain_comparison}
\end{figure}

Approximately three-quarters (73.4%) of analyzed terminology exhibits context-dependent meanings. Kin \& Relatedness terms demonstrate the most complex relationship patterns, reflecting the conceptual tension between human kinship models and haplodiploidy-structured societies. Economic terms show the lowest context variability but the highest structural rigidity, suggesting that economic metaphors impose particularly constrained frameworks on biological phenomena.

## Domain-Specific Findings

### Unit of Individuality

Analysis of individuality terminology reveals complex multi-scale patterns (Figure \ref{fig:unit_individuality_patterns}). "Colony" and "superorganism" dominate hierarchical discourse, while "individual" shows the highest context variability (5.2 contexts per usage). Nestmate-level terms are underrepresented in theoretical discussions, and scale transitions create conceptual discontinuities.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/unit_of_individuality_patterns.png}
\caption{Unit of Individuality domain analysis showing terminology patterns across biological scales. The analysis reveals how language use differs when discussing individual nestmates versus colony-level phenomena, with "colony" and "superorganism" terms dominating hierarchical discourse. Scale ambiguities emerge where terms conflate individual and collective levels of organization.}
\label{fig:unit_individuality_patterns}
\end{figure}

### Power \& Labor

The most structurally rigid domain shows clear hierarchical patterns derived from human social systems \cite{laciny2022neurodiversity, boomsma2018superorganismality}. Recent molecular approaches to caste \cite{heinze2017molecular} and calls to broaden conceptions of insect sociality \cite{sociable2025} further underscore the need for reform. Nearly nine in ten (89.2%) Power \& Labor terms derive from human hierarchical systems. "Caste" and "queen" form central hub terms with the highest betweenness centrality; "worker" and "slave" show parasitic terminology influence \cite{herbers2006}. The chain-like network structure reflects the linear hierarchies assumed by this vocabulary rather than the distributed organization documented in behavioral studies (Figure \ref{fig:concept_hierarchy}).

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/concept_hierarchy.png}
\caption{Conceptual hierarchy in Power \& Labor domain showing how human social terminology structures scientific understanding of ant societies. The term "caste" creates direct parallels to human hierarchical systems \cite{crespi1992caste}, while terms like "queen" and "worker" impose role-based identities that may not reflect biological flexibility. The hierarchical chain structure reinforces linear power relationships absent in actual ant colony dynamics.}
\label{fig:concept_hierarchy}
\end{figure}

### Behavior and Identity

Behavioral descriptions create categorical identities that may obscure the biological fluidity documented in ant task-switching research \cite{ravary2007, gordon2010}. Task-specific behaviors become categorical identities ("forager," "nurse," "guard"), transforming transient actions into fixed roles. Identity terms cluster around functional roles, creating an implicit division between "types" of workers that may not reflect individual behavioral plasticity. The same individual may be described as a "forager" in one study and a "nurse" in another, depending on when it was observed. \citeauthor{gordon2023ecology}'s \citeyearpar{gordon2023ecology} recent synthesis demonstrates that task allocation in harvester ant colonies operates entirely through local interaction networks—brief antennal contacts modulated by cuticular hydrocarbon profiles—without any centralized assignment. Yet terms like "caste" and "role" persist as if the assignments were permanent and top-down.

### Sex \& Reproduction

Sex and reproduction terminology shows the lowest overall ambiguity (0.59) but reveals a distinctive pattern of **binary opposition**—the dominant network structure in this domain (Table \ref{tab:domain_network_stats}). Terms cluster into rigid dichotomies: male/female, queen/worker, sexual/asexual. These oppositions import mammalian sex-determination frameworks into a fundamentally different system: under haplodiploidy, males develop from unfertilized (haploid) eggs and females from fertilized (diploid) eggs, decoupling sex determination from the chromosomal mechanisms assumed by standard terminology \cite{chandra2021epigenetics}. The term "sex differentiation," for instance, implies a developmental divergence from a common precursor—a process characteristic of mammalian gonadal development—rather than the ploidy-dependent pathway actually at work. Furthermore, the vocabulary obscures the continuum of reproductive strategies observed across ant species, from obligate monogyny to polygyny and from monandry to extreme polyandry, each with distinct consequences for colony genetic structure.

### Kin \& Relatedness

Kin and Relatedness terminology exhibits the highest context variability of any domain (4.5) and a web-like network architecture reflecting the complex, non-intuitive relatedness structures of haplodiploid societies (Figure \ref{fig:kin_relatedness_patterns}). The central tension is between human bilateral kinship models—where siblings share $r = 0.5$—and the haplodiploidy-specific asymmetry where full sisters share $r = 0.75$ but sisters relate to brothers at only $r = 0.25$. When researchers describe colony members as "sisters," the term imports an assumption of symmetry that masks the very asymmetry on which inclusive fitness theory depends.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/kin_and_relatedness_patterns.png}
\caption{Kin and Relatedness terminology patterns. The network shows a web-like architecture with high interconnectivity, reflecting the complex relationship structures in haplodiploid societies. High centrality nodes include "kin," "relatedness," and "inclusive fitness."}
\label{fig:kin_relatedness_patterns}
\end{figure}

Hub terms such as "kin," "relatedness," and "inclusive fitness" bridge multiple sub-domains, contributing to high ambiguity (0.75). Network analysis reveals that Hamilton's-rule-adjacent vocabulary dominates the discourse, often at the expense of alternative frameworks such as multilevel selection. Analysis of kinship terminology (Figure \ref{fig:kin_relatedness_frequencies}) shows that "kin selection" co-occurs with "altruism" and "cooperation" far more frequently than with "conflict" or "policing," suggesting a framing bias toward cooperative explanations that may underrepresent intra-colony conflict dynamics.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/kin_and_relatedness_term_frequencies.png}
\caption{Frequency analysis of Kin and Relatedness terminology. "Kin selection" and cooperative terms dominate the discourse, potentially obscuring conflict-based dynamics.}
\label{fig:kin_relatedness_frequencies}
\end{figure}

### Economics

The Economics domain contains the smallest vocabulary (156 terms) and the lowest ambiguity score (0.55) but the highest **structural rigidity**: economic metaphors impose particularly constrained interpretive frameworks. Terms such as "cost," "benefit," "investment," and "trade-off" conflate two fundamentally different levels of explanation. "Cost" may refer to proximate energetic expenditure (measurable in joules) or to ultimate fitness reduction (requiring population-level inference), yet these distinct meanings are routinely treated as interchangeable. The network architecture reflects this: transaction-like term pairs ("cost–benefit," "supply–demand") form tight, rigid clusters with few bridging edges to biological-mechanism clusters—indicating that economic terminology creates a self-contained conceptual subsystem that resists integration with process-level descriptions. Extended frequency and ambiguity analyses for this domain (Figures \ref{fig:economics_frequencies}, \ref{fig:economics_ambiguities}) confirm this insularity.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/economics_term_frequencies.png}
\caption{Frequency analysis of Economics domain terminology. Transaction-pair terms ("cost–benefit," "supply–demand") dominate the vocabulary, forming tight clusters with few bridging edges to biological-mechanism terminology.}
\label{fig:economics_frequencies}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/economics_ambiguities.png}
\caption{Ambiguity patterns in Economics domain terminology. Despite the lowest overall ambiguity score (0.55), economic terms exhibit high structural rigidity—metaphors like "cost" and "investment" conflate proximate energetic expenditure with ultimate fitness reduction.}
\label{fig:economics_ambiguities}
\end{figure}

## Framing Analysis

Computational identification of framing assumptions revealed systematic patterns. Anthropomorphic framing affects all domains at a prevalence of 67.3% and with high impact; hierarchical framing (45.8%) concentrates in Power/Labor and Individuality domains. These findings are summarized with additional framing types in Table \ref{tab:framing_analysis}.

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

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/anthropomorphic_framing.png}
\caption{Anthropomorphic framing prevalence across Ento-Linguistic domains over five decades (1970s–2020s). Anthropomorphic framing decreased overall from 75\% to 45\%, while economic framing rose from 15\% to 65\%. Hierarchical framing remained stable at approximately 50\%. Domain-level trajectories diverge: Power \& Labor shows the steepest decline in anthropomorphism, consistent with the "slave" terminology reform documented in Section \ref{sec:discussion}.}
\label{fig:anthropomorphic}
\end{figure}

Table \ref{tab:domain_framing_prevalence} breaks down framing prevalence by domain.

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|c|}
\hline
\textbf{Framing Type} & \textbf{Unit (\%)} & \textbf{Behavior (\%)} & \textbf{Power (\%)} & \textbf{Sex (\%)} & \textbf{Economics (\%)} \\
\hline
Anthropomorphic & 68.3 & 71.2 & 45.8 & 23.1 & 34.7 \\
Hierarchical & 45.8 & 32.4 & 89.2 & 12.3 & 67.8 \\
Economic & 23.1 & 18.9 & 34.5 & 8.7 & 91.3 \\
Kinship-based & 34.7 & 41.2 & 23.4 & 76.5 & 28.9 \\
Technological & 12.4 & 28.7 & 15.6 & 9.8 & 45.2 \\
Biological & 87.6 & 93.1 & 78.9 & 95.4 & 72.3 \\
\hline
\end{tabular}
\caption{Framing prevalence across individual Ento-Linguistic domains}
\label{tab:domain_framing_prevalence}
\end{table}

Our ambiguity detection algorithm classifying distinct ambiguity types confirms that *semantic* and *context-dependent* ambiguity are most prevalent.

## Longitudinal Case Studies

To understand how these patterns evolve, we conducted longitudinal analysis on two critical terminology clusters: Caste and Superorganism.

### Caste Terminology Evolution: 1970-2024

We observe a clear transition from rigid categories to plasticity-aware concepts:

- **1970s-1980s**: Rigid caste categories dominant (92\% usage).
- **1990s-2000s**: Transition to task-based understanding (67\% traditional caste).
- **2010s-2024**: Recognition of plasticity and individual variation (34\% traditional caste).

### Superorganism Debate: Conceptual Evolution

The superorganism concept has undergone a parallel transformation (Table \ref{tab:superorganism_evolution}).

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|}
\hline
\textbf{Period} & \textbf{Superorganism (\%)} & \textbf{Colony (\%)} & \textbf{Eusocial (\%)} & \textbf{Major Shift} \\
\hline
1970-1980 & 78.3 & 12.4 & 9.3 & Emergence of superorganism concept \\
1980-1990 & 65.7 & 23.1 & 11.2 & Introduction of colony-level analysis \\
1990-2000 & 43.2 & 38.9 & 17.9 & Recognition of individual variation \\
2000-2010 & 28.7 & 52.1 & 19.2 & Integration of genomic perspectives \\
2010-2024 & 18.3 & 61.5 & 20.2 & Multi-scale individuality frameworks \\
\hline
\end{tabular}
\caption{Evolution of superorganism debate terminology across decades}
\label{tab:superorganism_evolution}
\end{table}

This evolution reflects a shift from metaphorical usage to a rigorous multi-scale framework for individuality.
