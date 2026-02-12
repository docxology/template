# Introduction {#sec:introduction}

## Speech and Thought Entanglement in Scientific Communication

Speech and thought are inextricably entangled, a relationship recognized by linguists since at least Sapir and Whorf \cite{sapir1921, whorf1956}. This entanglement becomes particularly consequential in scientific discourse, where language not only describes phenomena but actively shapes how researchers perceive, categorize, and investigate them \cite{kuhn1996, foucault1972archaeology}. In entomology, researchers routinely employ anthropomorphic terminology—"queen," "worker," "slave," "caste"—that carries implicit assumptions about individuality, agency, and social structure. Our work examines this entanglement through systematic analysis of what we term *Ento-Linguistic domains*: specific areas where language use in ant research creates ambiguity, assumptions, or inappropriate framing.

## Motivation: Clear Communication as Ethical Imperative

Scientific communication is value-aligned: researchers communicate with present and future colleagues on their "best behavior." This makes it both natural and urgent to examine how language shapes understanding. As Keller \cite{keller1995language} has argued, the language of science is not merely descriptive but constitutive—it structures research questions, methodological approaches, and interpretive frameworks. Lakoff and Johnson \cite{lakoff1980metaphors} demonstrated more broadly that metaphorical structures pervade human reasoning; in science, these metaphors can become invisible yet powerful shapers of inquiry.

The present moment is an optimal window for such examination. Rather than perpetuating potentially problematic terminology, researchers bear an ethical responsibility to critically assess how language influences scientific practice and knowledge production. Recent initiatives—the Entomological Society of America's Better Common Names Project \cite{betternamesproject2024}, scholarly critiques of anthropomorphic terminology in social insect research \cite{herbers2007, laciny2022neurodiversity}—demonstrate growing recognition of this imperative.

A paradigmatic example is the debate over "slave-making ants." Herbers \cite{herbers2006} argued that the term "slave" applied to obligate social parasitism naturalizes a human institution of profound moral weight while obscuring the underlying biology: the parasite species exploits the brood-care behaviour of its host, a process better described as "social parasitism" or "dulosis." The subsequent shift in major journals toward neutral terminology—"host," "parasite," "dulotic"—demonstrates that reform is achievable without sacrificing scientific precision \cite{herbers2007}. This case also illustrates a general principle: once a metaphor is challenged, the replacement term often reveals biological mechanisms that the original metaphor had concealed.

## The Challenge of Terminological Reform

A common objection to improving scientific language is that changing terminology creates disconnection from existing literature. If entomologists abandon terms like "caste" or "slave," how would researchers locate papers on task performance or social parasitism?

This objection, however, inadvertently strengthens the case for reform. Retaining problematic terminology for convenience perpetuates and compounds conceptual distortions rather than addressing them \cite{herbers2006}. The appropriate response is to work systematically toward clearer communication while developing the necessary infrastructure for literature synthesis—restructuring information from existing sources and establishing new meta-standards for scientific discourse.

## Ento-Linguistic Domains: A Framework for Analysis

We organize our analysis around six domains where entomological language creates ambiguity or imports unjustified assumptions. Each domain isolates a distinct category of terminological friction between human conceptual frameworks and ant biology.

**Unit of Individuality.** What counts as an "individual" in ant biology? Terms like "colony," "superorganism," and "individual" operate across multiple biological scales—genomic, organismal, colonial—without consistent usage, creating systematic ambiguity about the unit of analysis \cite{wilson2008superorganism}.

**Behavior and Identity.** Task-specific descriptions routinely become categorical identities: an ant observed foraging becomes a "forager," transforming a transient activity into a fixed role. This linguistic move obscures the behavioral plasticity documented across ant species \cite{ravary2007, gordon2010}.

**Power \& Labor.** Terms like "queen," "worker," and "caste" import human social hierarchies into ant biology, imposing assumptions about authority and subordination that may not reflect the distributed, flexible organization of actual colonies \cite{herbers2007, laciny2022neurodiversity}.

**Sex \& Reproduction.** Terms like "sex determination" and "sex differentiation" carry implicit assumptions about binary systems that may not map onto ant reproductive biology, where haplodiploidy creates fundamentally different patterns \cite{chandra2021epigenetics}.

**Kin \& Relatedness.** Human kinship terminology, grounded in bilateral relatedness, influences understanding of ant social relationships structured by haplodiploidy and colony-level recognition cues. This domain examines how concepts like "sister," "mother," and "family" create friction when applied to asymmetric relatedness coefficients.

**Economics.** Economic metaphors—markets, trade, investment—shape analysis of ant foraging, resource distribution, and colony-level resource management. This domain investigates how such terminology constrains biological interpretation by imposing transactional frameworks.

## Research Approach

This work employs a mixed-methodology framework combining computational text analysis with theoretical discourse examination. The computational component processes a curated literature corpus using automated term extraction, co-occurrence network construction, and ambiguity scoring to identify statistical patterns in language use. The theoretical component, informed by Foucault's archaeological method \cite{foucault1972archaeology} and conceptual metaphor theory \cite{lakoff1980metaphors}, examines how these patterns reflect deeper conceptual structures. All data and analysis code are reproducible and available for validation and extension.

## Terminology Network Visualization

To illustrate the framework's output, Figure \ref{fig:concept_map} shows how terms cluster around the six Ento-Linguistic domains and form cross-domain networks of meaning; detailed quantitative analysis follows in Section \ref{sec:experimental_results}.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../output/figures/concept_map.png}
\caption{Conceptual map of Ento-Linguistic domains showing relationships between terminology networks. Each node represents an extracted concept; node size is proportional to term frequency in the corpus and node colour encodes the primary domain assignment. Edges connect co-occurring concepts, with thickness reflecting co-occurrence strength. The six domains form interconnected clusters; central hub terms such as ``colony,''``caste,'' and ``individual'' bridge multiple domains, demonstrating how specific terminological choices propagate across the scientific discourse of entomology.}
\label{fig:concept_map}
\end{figure}
