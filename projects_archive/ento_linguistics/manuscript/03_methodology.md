# Methodology {#sec:methodology}

## Mixed-Methodology Framework for Ento-Linguistic Analysis

Our research integrates computational text analysis with theoretical discourse examination to investigate how language shapes scientific understanding in entomology. This mixed-methodology approach combines quantitative pattern detection with qualitative conceptual analysis, following the tradition of critical discourse analysis \cite{fairclough1992} while extending it with computational methods suited to large-scale corpus analysis.

## Computational Text Analysis Pipeline

The computational component implements a multi-stage pipeline processing a **comprehensive corpus of 3,253 publications** (473,322 tokens) mined from **PubMed** and **arXiv** (quantitative biology/entomology categories). Raw scientific text is normalized, tokenized with domain-aware rules that preserve multi-word entomological terms (e.g., "division of labor," "kin selection") as atomic units, and lemmatized. Domain-specific terminology is then extracted using a scoring function that combines TF-IDF weighting, domain relevance, and linguistic features. Terms are classified into the six Ento-Linguistic domains. Full mathematical formulations and parameter calibration details are provided in Section \ref{sec:supplemental_methods}.

Terminology relationships are modeled as weighted co-occurrence networks, where nodes represent terms and edges encode co-occurrence frequency, Jaccard similarity, and semantic relatedness within configurable sliding windows. Network analysis—including community detection, centrality measurement, and modularity scoring—reveals structural patterns in how scientific language is organized. These patterns expose domain clustering and identify bridging terms that connect different conceptual areas.

## Theoretical Discourse Analysis Framework

The theoretical component employs systematic conceptual mapping informed by \citeauthor{foucault1972archaeology}'s archaeological method \citeyearpar{foucault1972archaeology} and **bio-semiotic formalism** \cite{deacon2011incomplete, kirchhoff2018markov}. We evaluate terms not just for social bias, but for **generative model specification errors**:

1. **Teleological Fallacies**: Does the term attribute global planning (deep temporal policies) to an entity that operates on local cues (reflexive policies)?
2. **Agency Attribution Errors**: Does the term locate agency in the individual ant when the relevant Markov Blanket is the colony?
3. **Boundary Confusions**: Does the term blur the distinction between internal states and external states?

For each identified term, we map its conceptual implications against the **physics of life** principles \cite{friston2013life}, examining how it imposes implicit frameworks on ant biology—particularly where human social concepts are applied to insect societies \cite{keller1995language}.

### Quantifying Ambiguity: Semantic Entropy

To rigorously measure the "noise" a term introduces into the scientific generative model, we calculate its **Semantic Entropy** ($H$). Rather than a simple count of meanings, we employ an information-theoretic approach:

1. **Context Vectorization**: All usage contexts of a term are embedded using TF-IDF vectorization.
2. **Semantic Clustering**: Contexts are clustered to identify distinct *senses* (e.g., "Queen as mother" vs. "Queen as ruler").
3. **Entropy Calculation**: We compute the Shannon entropy of the cluster distribution to derive the **Semantic Entropy** ($H$) of the term:
    $$ H(t) = - \sum_{i=1}^{k} p(c_i) \log_2 p(c_i) $$
    Where $p(c_i)$ is the probability of term $t$ appearing in semantic cluster $c_i$.

    A term with $H \approx 0$ (low entropy) maps 1:1 to a specific biological phenomenon regardless of context. We set the **high-entropy threshold at $H > 2.0$ bits**, corresponding to $> 4$ equiprobable semantic senses ($\log_2 4 = 2.0$). This threshold was calibrated against known polysemous terms: "colony" and "queen" consistently exceed this boundary, while domain-specific technical terms (e.g., "haplodiploidy," "trophallaxis") fall below it. A term exceeding this threshold acts as a high-temperature stochastic variable in the scientific model, introducing irreducible uncertainty into the communication channel and increasing the variational free energy of any explanation determined by it. Statistical comparisons between domains employ two-tailed $t$-tests (or one-way ANOVA for $> 2$ groups) with significance reported at $\alpha = 0.05$; 95\% confidence intervals are provided for all point estimates.

## The CACE Meta-Standards Framework

The integration of computational and theoretical methods allows us to evaluate terminology against four meta-standards, which we designate as the **CACE** framework:

1. **Clarity**: Does the term have a stable, non-ambiguous definition across scales? (Low Semantic Entropy).
2. **Appropriateness**: Is the metaphor apt for the biological phenomenon, or does it import unjustified assumptions?
3. **Consistency**: Is the term used consistently within the work and the broader field?
4. **Evolvability**: Is the terminology **scale-invariant**? An evolvable term (e.g., "reproductive") functions correctly at genetic, organismal, and superorganismal scales. A rigid term (e.g., "queen") fractures when the scale of analysis shifts, requiring different definitions at different levels of organization.

We apply this framework to quantify the state of current entomological discourse.

**Worked Example: Evaluating "Queen" Under the CACE Framework.** Consider the term "queen" as used in ant biology. *Clarity*: the term conflates reproductive function (egg-laying) with political authority (ruling), creating ambiguity about whether the individual exercises control over colony decisions—she typically does not \cite{herbers2007}. *Appropriateness*: the monarchical metaphor imports assumptions of hierarchical command absent from the biology; pheromone-mediated reproductive signalling is not governance. *Consistency*: usage varies across taxa—in *Apis* (honeybees), the queen's regulatory role is more pronounced than in many ant species where multiple reproductives coexist, yet the same term is used without qualification. *Evolvability*: recent genomic work on caste determination \cite{chandra2021epigenetics} reframes "queen" status as an epigenetically labile phenotype rather than a fixed role, straining the term's implication of permanence. A CACE-informed alternative such as "primary reproductive" scores higher on Clarity (describes function, not rank), Appropriateness (no hierarchical implication), Consistency (applicable across taxa), and Evolvability (compatible with plasticity findings).

## Implementation and Validation

The analysis framework is implemented as a modular Python package organized by analytical function (text processing, terminology extraction, domain analysis, discourse analysis, conceptual mapping, and visualization). The pipeline scales as $O(n \log n + m \cdot d)$ where $n$ is corpus size, $m$ is the number of extracted terms, and $d = 6$ is the fixed number of domains. Results are validated through multi-method triangulation: internal consistency checks, cross-method agreement protocols, and external comparison with existing literature on scientific discourse \cite{latour1987, longino1990}. Full implementation architecture, data structures, quality gates, and reproducibility infrastructure are documented in Section \ref{sec:supplemental_methods}.
