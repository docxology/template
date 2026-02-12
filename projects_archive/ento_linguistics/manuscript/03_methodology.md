# Methodology {#sec:methodology}

## Mixed-Methodology Framework for Ento-Linguistic Analysis

Our research integrates computational text analysis with theoretical discourse examination to investigate how language shapes scientific understanding in entomology. This mixed-methodology approach combines quantitative pattern detection with qualitative conceptual analysis, following the tradition of critical discourse analysis \cite{fairclough1992} while extending it with computational methods suited to large-scale corpus analysis.

## Computational Text Analysis Pipeline

The computational component implements a multi-stage pipeline: raw scientific text is normalized, tokenized with domain-aware rules that preserve multi-word entomological terms (e.g., "division of labor," "kin selection") as atomic units, and lemmatized. Domain-specific terminology is then extracted using a scoring function that combines TF-IDF weighting, domain relevance (measured by co-occurrence with seed terms), and linguistic features. Terms are classified into the six Ento-Linguistic domains, and those exceeding a calibrated relevance threshold are retained. Full mathematical formulations and parameter calibration details are provided in Section \ref{sec:supplemental_methods}.

Terminology relationships are modeled as weighted co-occurrence networks, where nodes represent terms and edges encode co-occurrence frequency, Jaccard similarity, and semantic relatedness within configurable sliding windows. Network analysis—including community detection, centrality measurement, and modularity scoring—reveals structural patterns in how scientific language is organized. These patterns expose domain clustering and identify bridging terms that connect different conceptual areas.

## Theoretical Discourse Analysis Framework

The theoretical component employs systematic conceptual mapping informed by Foucault's archaeological method \cite{foucault1972archaeology} and Lakoff and Johnson's conceptual metaphor theory \cite{lakoff1980metaphors}. For each identified term, we map its conceptual implications, analyze its usage across different research contexts, and examine how it imposes implicit frameworks on ant biology—particularly where human social concepts are applied to insect societies \cite{keller1995language}.

Each of the six Ento-Linguistic domains receives specialized analysis. The Unit of Individuality domain, for instance, detects scale conflation in how "individual," "colony," and "superorganism" are used. The Power \& Labor domain maps network centrality of terms derived from human hierarchies against biological function terms. The Behavior and Identity domain quantifies the stability of behavioral descriptors to distinguish transient activities from fixed identity labels. Detailed per-domain models are documented in Section \ref{sec:supplemental_methods}.

## Integration of Computational and Theoretical Methods

Rather than treating computational and theoretical analysis as independent tracks, we implement an iterative convergence process. Initial computational analysis identifies candidate terminology patterns across the corpus. Theoretical examination assesses their conceptual significance. Refined computational analysis then targets specific domains and relationships guided by theoretical insights. The integrated synthesis yields findings that neither approach alone could produce. Cross-method validation ensures that computationally detected patterns are theoretically meaningful, and that theoretical claims are empirically grounded in corpus evidence.

## The CACE Meta-Standards Framework

The integration of computational and theoretical methods allows us to evaluate terminology against four meta-standards, which we designate as the **CACE** framework:

1. **Clarity**: Does the term have a stable, non-ambiguous definition across scales?
2. **Appropriateness**: Is the metaphor apt for the biological phenomenon, or does it import unjustified assumptions?
3. **Consistency**: Is the term used consistently within the work and the broader field?
4. **Evolvability**: Is the terminology robust to new empirical discoveries (e.g., genomic drivers of caste)?

We apply this framework to quantify the state of current entomological discourse.

**Worked Example: Evaluating "Queen" Under the CACE Framework.** Consider the term "queen" as used in ant biology. *Clarity*: the term conflates reproductive function (egg-laying) with political authority (ruling), creating ambiguity about whether the individual exercises control over colony decisions—she typically does not \cite{herbers2007}. *Appropriateness*: the monarchical metaphor imports assumptions of hierarchical command absent from the biology; pheromone-mediated reproductive signalling is not governance. *Consistency*: usage varies across taxa—in *Apis* (honeybees), the queen's regulatory role is more pronounced than in many ant species where multiple reproductives coexist, yet the same term is used without qualification. *Evolvability*: recent genomic work on caste determination \cite{chandra2021epigenetics} reframes "queen" status as an epigenetically labile phenotype rather than a fixed role, straining the term's implication of permanence. A CACE-informed alternative such as "primary reproductive" scores higher on Clarity (describes function, not rank), Appropriateness (no hierarchical implication), Consistency (applicable across taxa), and Evolvability (compatible with plasticity findings).

## Implementation and Validation

The analysis framework is implemented as a modular Python package organized by analytical function (text processing, terminology extraction, domain analysis, discourse analysis, conceptual mapping, and visualization). The pipeline scales as $O(n \log n + m \cdot d)$ where $n$ is corpus size, $m$ is the number of extracted terms, and $d = 6$ is the fixed number of domains. Results are validated through multi-method triangulation: internal consistency checks, cross-method agreement protocols, and external comparison with existing literature on scientific discourse \cite{latour1987, longino1990}. Full implementation architecture, data structures, quality gates, and reproducibility infrastructure are documented in Section \ref{sec:supplemental_methods}.
