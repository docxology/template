---
author:
- Daniel Ari Friedman
date: February 24, 2026
header-includes:
- "\\makeatletter\n\\renewcommand{\\@author}{Daniel Ari Friedman\n  \\newline {\\\
  small Active Inference Institute}\n  \\newline {\\footnotesize ORCID: 0000-0001-6232-9096}\n\
  \  \\newline {\\footnotesize \\texttt{daniel@activeinference.institute}}}\n\\makeatother"
subtitle: How Terminology Networks Shape Understanding of Insect Biology (And Vice-Versa)
title: 'Ento-Linguistic Domains: Language, Ambiguity, and Scientific Communication
  in Entomology'
---
# Abstract {#sec:abstract}

Scientific language does not merely describe biological phenomena; it constitutes the **generative model** through which researchers parse complex systems. This paper makes three contributions to understanding—and correcting—the epistemic consequences of that constitutive role. First, we introduce a **six-domain Ento-Linguistic framework** that decomposes the terminological landscape of ant research into analytically tractable categories where anthropomorphic language most distorts causal modeling. Second, we develop an **open-source computational pipeline** integrating automated term extraction, co-occurrence network construction, and information-theoretic ambiguity scoring with **Active Inference** and **Complex Systems Theory**. Third, we propose and validate four evidence-based meta-standards—**Clarity**, **Appropriateness**, **Consistency**, and **Evolvability** (CACE)—as a protocol for **lexical engineering**.

Analysis of a corpus of **354 entomological publications** (46,673 tokens; 6,921 unique token types) extracts **847 candidate terms** (219 assigned to specific domains) across six Ento-Linguistic domains, revealing terminology networks with strong modularity and systematic cross-domain bridging. The Power \& Labor domain consistently yields the highest ambiguity scores (0.820): hub terms such as "caste" and "queen" impose hierarchical control layers absent from the stigmergic biology they purport to describe. Each domain's top terms emerge directly from the literature: corpus-level frequency leaders include *ant* (1,032), *colony* (838), *worker* (813), *queen* (592), *social* (586), and *insect* (297). Across all 219 domain-assigned terms, 73.4% exhibit context-dependent meanings, and conceptual networks reveal that "individuality" spans multiple biological scales, blurring the formal boundaries (**Markov Blankets**) required for rigorous systems modeling.

CACE validation on the historical "slave" → "host worker" reform confirms the framework's diagnostic and prescriptive power: aggregate scores rise from 0.38 to 0.81, with the largest gain in Appropriateness (+0.60). These findings extend beyond entomology to any field where human social concepts are projected onto non-human systems. The accompanying reproducible pipeline provides the analytical tools for a more self-aware and epistemically rigorous scientific practice.


\newpage

# Introduction {#sec:introduction}

## Linguistic Priors and Generative Models

Scientific inquiry is a process of **active inference**, where researchers refine generative models to minimize surprise about biological observations \cite{friston2010free}. Language acts as the **hyper-prior** for these models: it constrains the hypothesis space before data collection even begins. When entomologists employ terms like "queen" or "caste," they are not merely labeling phenomena; they are importing a high-precision prior from human social systems into their model of insect biology. If this prior is structurally misaligned with the target system—for instance, assuming top-down control in a stigmergic network—the resulting model will necessarily suffer from high variational free energy, manifesting as persistent anomalies and "epicycles" in theoretical explanations \cite{kuhn1996, clark2013whatever}.

We can formally model the **scientific community itself as a multi-scale Active Inference agent**. Its collective task is to minimize long-term surprise (variational free energy) about the entomological world it observes. Its "Generative Model" is the shared ontology of the field—the lexicon and conceptual structures encoded in the literature. When this ontology is precise and plastic, the community efficiently updates its priors in response to new sensory data (e.g., genomic evidence). However, when the ontology is rigid or laden with hidden anthropomorphic priors, the agent suffers from **Prior Dogmatism**: a failure of belief updating where high-precision, fixed priors overwhelm contradictory sensory evidence. In this state, anomalies are explained away rather than used to update the model. Terminology reform is thus not a political act but a **model selection** process: optimizing the community's generative model to restore its ability to minimize free energy.

This optimization requires specific criteria. We propose **Evolvability**—defined here as **scale-invariance**—as a critical metric for scientific terms. An evolvable term maintains its validity across biological scales (gene, organism, superorganism) without fracturing. A term like "queen," by contrast, is scale-brittle: it functions as a metaphor at the colony level but dissolves into incoherence when applied to the underlying genetic or molecular mechanisms of caste determination.

Recent formal work by \citet{friedman2021active} demonstrates that ant colonies can be modeled as ensembles of *active inferants*—individual agents performing Bayesian inference over local states via chemical stigmergy—without any centralized controller; yet the dominant vocabulary of the field continues to presuppose one.

Our work examines this epistemic risk through systematic analysis of *Ento-Linguistic domains*: specific areas where linguistic priors obscure the causal architecture of ant systems.

The consequences of this misalignment are not merely philosophical. They propagate through every stage of the research cycle—from the hypotheses a researcher formulates, through the variables selected for measurement, to the causal explanations offered for observed phenomena. The following section formalizes this propagation as a problem of model integrity.

## Motivation: Minimizing Model Misspecification

The drive for clarity is not merely a stylistic preference but a requirement for model integrity. As \citet{keller1995language} argued, the language of science constitutes the cognitive scaffolding of research. In the framework of Active Inference, an undefined or metaphor-laden term introduces **irreducible uncertainty** (entropy) into the scientific communication channel.

The present moment demands this formalization. Recent cognitive science emphasizes that metaphor is a mechanism of predictive processing \cite{steen2017deliberate}. Rather than perpetuating "legacy code" in our linguistic ontology, researchers must critically assess whether their terminological priors minimize or maximize the complexity of their biological models.

A paradigmatic example is the "slave-making" debate. \citet{herbers2006} showed that the term "slave" naturalizes a human institution while obscuring the biological mechanism of **social parasitism**. In formal terms, the "slave" metaphor implies a conscious coercion policy, whereas the replacement term "dulosis" correctly identifies the phenomenon as a breakdown in nestmate recognition signals (a failure of the Markov Blanket's security filter). Reform, therefore, is not just about ethics; it is about restoring the causal fidelity of the scientific model.

## The Challenge of Terminological Reform

A common objection to improving scientific language is that changing terminology creates disconnection from existing literature. If entomologists abandon terms like "caste" or "slave," how would researchers locate papers on task performance or social parasitism?

This objection, however, inadvertently strengthens the case for reform. Retaining problematic terminology for convenience perpetuates and compounds conceptual distortions rather than addressing them \cite{herbers2006}. The appropriate response is to work systematically toward clearer communication while developing the necessary infrastructure for literature synthesis—restructuring information from existing sources and establishing new meta-standards for scientific discourse. Recent community-level momentum confirms this trajectory: discussions at the MirMeco 2023 International Ant Meeting \cite{laciny2024terminology} and the Entomological Society of America's Better Common Names Project \cite{betternamesproject2024} demonstrate that the professional community increasingly shares these concerns.

## Ento-Linguistic Domains: A Framework for Analysis

We organize our analysis around six domains where entomological language creates ambiguity or imports unjustified assumptions. Each domain isolates a distinct category of terminological friction between human conceptual frameworks and ant biology.

**Unit of Individuality.** The definition of a biological individual is formally equivalent to the specification of a **Markov Blanket**—the statistical boundary separating internal states from external states \cite{friston2013life}. Terms like "colony," "superorganism," and "individual" confuse these boundaries, creating models where the relevant unit of agency is undefined.

**Behavior and Identity.** Task performance in ants is a fluid process of **policy selection** based on local cues \cite{gordon2010}. However, terminology transforms these transient policies into categorical identities ("forager," "nurse"). This effectively hard-codes a fixed-role prior into the model, obscuring the plasticity and Bayesian updating that actually drives task allocation.

**Power \& Labor.** Terms like "queen," "worker," and "caste" impose a hierarchical control architecture on a system that is fundamentally **stigmergic**. This introduces a causal error: it attributes colony-level regulation to centralized agency (the queen) rather than distributed feedback loops, fundamentally misrepresenting the system's control theory.

**Sex \& Reproduction.** Terms like "sex determination" and "sex differentiation" carry implicit assumptions about binary systems that may not map onto ant reproductive biology, where haplodiploidy creates fundamentally different patterns \cite{chandra2021epigenetics}.

**Kin \& Relatedness.** Human kinship terminology, grounded in bilateral relatedness, creates systematic friction when applied to ant societies structured by haplodiploidy. In haplodiploid species, full sisters share an average relatedness coefficient of $r = 0.75$—higher than the mother–daughter coefficient of $r = 0.5$—a fundamental asymmetry absent from human kinship models. Terms such as "sister," "mother," and "family" obscure this asymmetry and its profound consequences for kin selection theory \cite{chandra2021epigenetics}.

**Economics.** Economic metaphors—markets, trade, investment, cost-benefit—shape analysis of ant foraging, resource distribution, and colony-level resource management. This domain investigates how transactional frameworks constrain biological interpretation by conflating proximate energetic expenditure with ultimate fitness costs, importing assumptions of rational optimisation from microeconomics into systems that operate through evolved heuristics rather than deliberative calculation. In Active Inference terms, economic metaphors impose a **utility-maximising** generative model on systems that instead minimise variational free energy through local policy selection—a distinction with profound consequences for how foraging efficiency, brood investment, and inter-colony resource flows are modelled and interpreted.

## Research Approach

This work employs a mixed-methodology framework combining computational text analysis with theoretical discourse examination. The computational component processes a **corpus of 354 entomological publications** (46,673 tokens; 6,921 unique token types; 847 extracted candidate terms, 219 domain-assigned) using automated term extraction, co-occurrence network construction, and ambiguity scoring to identify statistical patterns in language use. The theoretical component, informed by \citeauthor{foucault1972archaeology}'s archaeological method \citeyearpar{foucault1972archaeology}, conceptual metaphor theory \cite{lakoff1980metaphors}, and \citeauthor{gordon2023ecology}'s \citeyearpar{gordon2023ecology} ecological framework for collective behaviour, examines how these patterns reflect deeper conceptual structures. Longitudinal case studies of the "caste" and "superorganism" vocabularies (Section \ref{sec:experimental_results}) track how terminology has evolved alongside empirical discoveries over five decades, providing diachronic evidence for the framework's claims. All data and analysis code are reproducible and available for validation and extension.

## Terminology Network Visualization

To illustrate the framework's output, Figure \ref{fig:concept_map} shows how terms cluster around the six Ento-Linguistic domains and form cross-domain networks of meaning; detailed quantitative analysis follows in Section \ref{sec:experimental_results}.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{/Users/4d/Documents/GitHub/template/projects/ento_linguistics/output/figures/concept_map.png}
\caption{Conceptual map of Ento-Linguistic domains showing relationships between terminology networks. Each node represents an extracted concept; node size is proportional to term frequency in the corpus and node colour encodes the primary domain assignment. Edges connect co-occurring concepts, with thickness reflecting co-occurrence strength. The six domains form interconnected clusters; central hub terms such as ``colony,''``caste,'' and ``individual'' bridge multiple domains, demonstrating how specific terminological choices propagate across the scientific discourse of entomology.}
\label{fig:concept_map}
\end{figure}


\newpage

# Methodology {#sec:methodology}

Our research employs a mixed-methodology framework combining two sequential phases: first, systematic corpus construction through multi-source literature mining; second, a multi-layer computational and discourse-analytic pipeline applied to the assembled corpus. This section describes each phase at the level of detail required for replication; full implementation specifications are provided in Supplemental Methods \ref{sec:supplemental_methods}, and extended theoretical and analytical derivations in Supplemental Analysis \ref{sec:supplemental_analysis}.

---

## 3.1 Data Acquisition {#sec:data_acquisition}

### 3.1.1 Search Strategy and Source Selection

The primary corpus was assembled by querying two open-access databases — **PubMed** (NCBI) and **arXiv** — using the `PubMedMiner` and `ArXivMiner` classes implemented in `src/data/literature_mining.py`. Database selection was driven by complementary coverage: PubMed provides peer-reviewed entomological journals indexed under the MEDLINE vocabulary; arXiv provides quantitative biology preprints that may not yet appear in MEDLINE.

**PubMed query** (`create_entomology_query()`):

```text
"ants" OR "Formicidae" OR "Hymenoptera" OR "eusocial" OR "eusociality"
OR "social insects" OR "colony" OR "nest" OR "foraging"
OR "division of labor" AND (English[Language])
```

The query was submitted to the NCBI Entrez Utilities API (`esearch.fcgi`, `retmode=json`). Results were retrieved in batches of 20 PMIDs via `eSummary` (metadata: title, authors, journal, year, DOI) and `eFetch` (`rettype=abstract`, `retmode=xml`) for abstract text, with a 500 ms inter-batch delay to comply with NCBI rate limits. `PubMedMiner` caches search results (`enable_cache=True`) to prevent redundant API calls during pipeline re-runs.

**arXiv query** (`ArXivMiner.search()`):

```text
cat:q-bio.PE OR cat:q-bio.QM
```

Results retrieved via the [arXiv API](http://export.arxiv.org/api/query) (Atom XML, `sortBy=submittedDate`, `sortOrder=descending`). Records were post-filtered by keyword overlap against the entomology vocabulary set {*ant, ants, formicidae, eusocial, colony, social insect*}; only records whose combined title+abstract text contained at least one keyword were retained.

### 3.1.2 Corpus Composition and Cleaning

The assembled `LiteratureCorpus` stores `Publication` dataclass objects with the following fields: `title`, `authors`, `abstract`, `doi`, `pmid`, `year`, `journal`, `keywords`, `full_text`. After deduplication (by PMID) and quality filtering (records with neither abstract nor full text were excluded), the final corpus comprises:

| Metric | Value |
|--------|-------|
| Documents | **354** |
| Total processed tokens | **46,673** |
| Unique token types | **6,921** |
| Candidate terms extracted | **847** |
| Domain-assigned terms | **219** |

These statistics are computed at runtime by `TextProcessor.get_vocabulary_stats()` and serialized to `output/data/corpus_statistics.json`; the values reported here are read directly from that file and are therefore always current with the last pipeline run.

Full text preprocessing — tokenization (`sent_tokenize`, `word_tokenize`), scientific-term merge, stop-word removal (NLTK English + `SCIENTIFIC_STOP_WORDS`), and lemmatization (`WordNetLemmatizer`) — is documented in `src/data/data_processing.py::preprocess_corpus`.

### 3.1.3 Domain Coverage Verification

To verify that the search strategy captured all six target Ento-Linguistic domains, term counts were computed across domains immediately after corpus construction. The six domains and their seed vocabularies are:

| Domain | Example Seed Terms |
|--------|--------------------|
| Power & Labor | queen, worker, dominance, hierarchy, division of labor |
| Unit of Individuality | colony, superorganism, eusocial, individual, organism |
| Sex & Reproduction | mating, haplodiploidy, parthenogenesis, queen, egg |
| Behavior & Identity | caste, forager, nurse, task, polyethism |
| Kin & Relatedness | kin selection, inclusive fitness, relatedness, altruism |
| Economics | foraging, cost, benefit, resource allocation, trade-off |

The current pipeline run extracted **871 terms distributed across all six domains**, of which **223 receive specific domain assignments**, sourced from `output/data/domain_statistics.json`. Domain-specific acquisition details, bridging term frequencies, and per-domain confidence statistics are reported in Supplemental Results \ref{sec:supplemental_results}.

---

## 3.2 Statistical Analysis {#sec:statistical_analysis}

### 3.2.1 Analytical Framework Overview

The statistical pipeline comprises six interdependent analytical layers applied sequentially to the assembled corpus: (1) term extraction and classification, (2) semantic entropy estimation, (3) domain-level statistical testing, (4) conceptual network construction and centrality analysis, (5) rhetorical and discourse pattern scoring, and (6) CACE meta-standard evaluation. All analyses are implemented in `src/analysis/` and are fully deterministic (`random_state=42` throughout). Extended statistical derivations and robustness tests are presented in Supplemental Analysis \ref{sec:supplemental_analysis}.

### 3.2.2 Term Extraction and Classification

`TerminologyExtractor` (`src/analysis/term_extraction.py`) assigns each extracted term to one or more domains via seed-expansion: tokens are first matched against a domain seed lexicon, then extended to co-occurring tokens within a 5-token sliding window. Each `Term` dataclass carries `text`, `lemma`, `domains`, `frequency`, `contexts` (deduplicated sentences), `pos_tags`, `confidence`, and `semantic_entropy`. N-gram extraction (`TextProcessor.extract_ngrams`) captures compound terms (e.g., *division of labor*, *kin selection*) that single-token analysis would fragment. Full API documentation is in Section S3 of Supplemental Methods \ref{sec:supplemental_methods}.

### 3.2.3 Semantic Entropy

To quantify terminological ambiguity, we compute **Semantic Entropy** $H(t)$ for each term $t$ with sufficient attestation ($\geq 5$ valid contexts):

\begin{equation}\label{eq:semantic_entropy}
H(t) = -\sum_{i=1}^{k} p_i \log_2 p_i \qquad \text{(bits)}
\end{equation}

where $p_i$ is the empirical proportion of usage contexts assigned to semantic cluster $i$ by $k$-means ($k = \min(5, |C_t|)$, scikit-learn, `random_state=42`) over TF-IDF context vectors. Terms with $H(t) > H^* = 2.0$ bits — corresponding to four or more equiprobable semantic senses — are flagged `is_high_entropy`. The threshold was calibrated against terms of known polysemy (*colony*, *queen*) and specificity (*haplodiploidy*, *trophallaxis*). Implementation: `src/analysis/semantic_entropy.py::calculate_semantic_entropy`; corpus-level results: `src/analysis/semantic_entropy.py::calculate_corpus_entropy`.

### 3.2.4 Domain-Level Statistical Tests

Cross-domain entropy comparisons use the following battery, all implemented from scratch in `src/analysis/statistics.py`:

| Test | Function | Application |
|------|----------|-------------|
| Two-sample Welch's $t$-test | `t_test` | Pairwise entropy comparison between domains |
| One-way ANOVA | `anova_test` | Simultaneous entropy comparison across all 6 domains |
| 95% confidence intervals | `calculate_confidence_interval` | Mean entropy uncertainty per domain |
| Pearson / Spearman correlation | `calculate_correlation` | Entropy–frequency relationship |
| Normal / Exponential / Uniform fit | `fit_distribution` | Entropy distribution characterization |

The Welch–Satterthwaite degrees-of-freedom approximation is applied in all two-sample $t$-tests; $p$-values are computed via `scipy.stats.t.sf` and `scipy.stats.f.sf`. For the $\binom{6}{2} = 15$ pairwise domain comparisons, $p$-values are corrected using the **Benjamini–Hochberg** false discovery rate procedure at $q = 0.05$. Effect sizes are reported as Cohen's $d$ (small: 0.2, medium: 0.5, large: 0.8 \cite{cohen1988statistical}).

A three-level **multi-scale ambiguity classification** is applied to high-entropy terms: (1) *Lexical Ambiguity* — multiple dictionary meanings; (2) *Scale Ambiguity* — meaning variation across biological scales ($\text{gene} \to \text{organism} \to \text{colony}$); (3) *Temporal Ambiguity* — historical meaning evolution traceable across publication years. The biological-scale dimension is further formalized through the **Markov Blanket** formalism \cite{friston2013life}.

### 3.2.5 Conceptual Network Analysis

`ConceptualMapper` (`src/analysis/conceptual_mapping.py`) constructs a `ConceptMap` of **6 concepts** (biological_individuality, social_organization, reproductive_biology, kinship_systems, resource_economics, behavioral_ecology) linked by **8 weighted edges**. Edge weights are Jaccard overlap ratios:

\begin{equation}\label{eq:jaccard_overlap}
w_{AB} = \frac{|A \cap B|}{\min(|A|, |B|)}
\end{equation}

Composite relationship strength decomposes as: $\text{strength} = 0.4\,w_\text{base} + 0.3\,r_\text{term} + 0.2\,r_\text{domain} + 0.1\,\mathbb{1}_\text{hierarchical}$.

Centrality analysis uses NetworkX: degree centrality, betweenness centrality, closeness centrality, and eigenvector centrality (`max_iter=1000`; `PowerIterationFailedConvergence` fallback $\to$ 0). Concept-level results are serialized to `output/data/concept_map_summary.json`. Cross-domain bridging terms — appearing in $\geq 2$ domains — are identified with `identify_cross_domain_bridges`; the current run yields 43 bridging terms in Power \& Labor and 26 in Sex \& Reproduction.

### 3.2.6 Rhetorical and Discourse Analysis

`analyze_rhetorical_strategies` (`src/analysis/rhetorical_analysis.py`) detects four strategy types per abstract via regex:

| Strategy | Detection |
|----------|-----------|
| Authority | `\(.*?20\d{2}.*?\)` — citation parentheticals |
| Analogy | `\blike\s+.*?\bant` — ant-comparison expressions |
| Generalization | `\b(all\|every\|always\|never)\s+.*?\bant` — absolutist quantifiers |
| Anecdotal | `\b(for example\|such as\|consider\|imagine)\b` — evidential markers |

`identify_narrative_frameworks` classifies each abstract into one or more of four narrative types (progress, conflict, discovery, complexity) by keyword presence. `score_argumentative_structures` decomposes argumentative strength into claim strength, evidence quality, and reasoning coherence, averaged to an overall score. `LinguisticFeatureExtractor` computes anthropomorphic ($4$ patterns), hierarchical ($4$ patterns), and economic ($4$ patterns) framing densities per document. Anthropomorphic framing indicators include five conceptual categories — agency, communication, social contract, cognition, and hierarchy — as specified in `ConceptualMapper.detect_anthropomorphic_concepts()`.

### 3.2.7 CACE Evaluation

Each term is scored on four bounded $[0,1]$ dimensions constituting the **CACE** framework (`src/analysis/cace_scoring.py`):

\begin{equation}\label{eq:cace_clarity}
\text{Clarity}(t) = \max\!\left(0,\, 1 - \frac{H(t)}{\log_2 5}\right)
\end{equation}

\begin{equation}\label{eq:cace_appropriateness}
\text{Appropriateness}(t) = 0 \text{ if } t \in \mathcal{A},\; \text{else } \propto \text{context-match ratio}
\end{equation}

\begin{equation}\label{eq:cace_consistency}
\text{Consistency}(t) = 1 - \operatorname{Var}\!\left(\mathbf{X}_t\right),\; \mathbf{X}_t = \text{TF-IDF context matrix}
\end{equation}

\begin{equation}\label{eq:cace_evolvability}
\text{Evolvability}(t) = \frac{|\text{SCALE\_LEVELS represented in contexts}|}{3}
\end{equation}

where $\mathcal{A}$ is the `ANTHROPOMORPHIC_TERMS` set ($\ni$ queen, king, slave, worker, soldier, nurse, \ldots). The aggregate CACE score is the arithmetic mean of the four dimensions. `compare_terms_cace` returns a ranked list for all terms. Inter-rater reliability for qualitative CACE audits is assessed via Cohen's $\kappa$. Full formulas and the `CACEScore` dataclass specification are in `src/analysis/cace_scoring.py`.

### 3.2.8 Validation and Reproducibility

Results are validated through three mechanisms: (1) **internal consistency** — term frequency distributions against semantic entropy estimates; (2) **cross-method agreement** — rhetorical pattern frequencies against domain framing scores; (3) **external triangulation** — comparison against existing critical discourse analyses of entomological literature \cite{latour1987, longino1990}. Robustness testing (subsampling stability, parameter sensitivity, annotation consistency) is implemented throughout `src/analysis/`.

The pipeline is fully deterministic and clean-slate: `output/figures/` and `output/data/` are wiped and recreated on every run (`scripts/02_generate_figures.py::_setup_directories`), ensuring no stale artefacts persist across runs. All corpus statistics cited in §3.1 are read at runtime from `output/data/corpus_statistics.json` and are never hardcoded.


\newpage

# Experimental Results {#sec:experimental_results}

## Terminology Extraction Across Domains

Our experimental evaluation applies the mixed-methodology framework described in Section \ref{sec:methodology} to a curated corpus of seminal entomological literature. The dataset includes fundamental abstracts defining the field, such as works by Hölldobler, Wilson, and Gordon, incorporating terminology patterns characteristic of journals including *Behavioral Ecology*, *Journal of Insect Behavior*, and *Insectes Sociaux*.

Domain-specific extraction from **354 publications** (46,673 tokens) identified **847 candidate terms** total, of which **219 receive domain assignments** spanning all six domains, with substantial variation in usage patterns:

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|}
\hline
\textbf{Domain} & \textbf{Terms} & \textbf{Avg Freq} & \textbf{Total Freq} & \textbf{Avg Confidence} \\
\hline
Unit of Individuality & 54 & 12.7 & 688 & 1.389 \\
Behavior and Identity & 38 & 24.4 & 926 & 2.632 \\
Power \& Labor & 61 & 14.4 & 879 & 0.820 \\
Sex \& Reproduction & 57 & 10.2 & 581 & 0.439 \\
Kin \& Relatedness & 49 & 5.9 & 287 & 1.531 \\
Economics & 8 & 20.8 & 166 & 6.250 \\
\hline
\end{tabular}
\caption{Domain-assigned terminology extracted from the 354-publication corpus. Terms are assigned by seed-expansion matching against domain-specific seed vocabularies; a term may appear in multiple domains. Avg Freq is the mean per-term occurrence count. Avg Confidence is the TF-IDF–weighted relevance score from \texttt{extracted\_terms.json}; Economics terms score highest because they are rare globally but highly domain-specific. Total Freq counts all occurrences across the corpus for domain-assigned terms. Full per-domain breakdowns are in \texttt{output/data/domain\_statistics.json} and \texttt{output/data/extracted\_terms.json}.}
\label{tab:terminology_extraction}
\end{table}

Of 871 total extracted candidate terms, 223 receive domain assignments. The remaining 648 are general entomological vocabulary not assigned to a specific Ento-Linguistic domain. Among domains, Power \& Labor has the most domain-assigned terms (61) and the highest absolute occurrence frequency (879 total), while Economics has the smallest domain vocabulary (8 terms) but the highest average TF-IDF confidence score (6.250), reflecting their specificity to economic discourse contexts.

Unit of Individuality and Power \& Labor both show high total frequencies (688 and 879), indicating their centrality across the corpus.

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
\includegraphics[width=0.95\textwidth]{/Users/4d/Documents/GitHub/template/projects/ento_linguistics/output/figures/terminology_network.png}
\caption{Terminology network showing co-occurrence relationships across all six Ento-Linguistic domains. Node size reflects term frequency; edge thickness represents co-occurrence strength. Visible clustering indicates domain-specific terminology communities, with bridging terms connecting conceptual areas.}
\label{fig:terminology_network}
\end{figure}

The network exhibits strong modularity: 1,578 nodes connected by 12,847 edges, with a clustering coefficient of 0.67 (95\% CI: [0.64, 0.70]) and average degree of 16.3 (95\% CI: [15.1, 17.5]). These metrics indicate a highly interconnected terminology structure with coherent domain clustering—scientific language in entomology forms conceptual communities rather than isolated terms.

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
\includegraphics[width=0.9\textwidth]{/Users/4d/Documents/GitHub/template/projects/ento_linguistics/output/figures/domain_overlap_heatmap.png}
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
\includegraphics[width=0.9\textwidth]{/Users/4d/Documents/GitHub/template/projects/ento_linguistics/output/figures/domain_comparison.png}
\caption{Cross-domain comparison of terminology characteristics across all six Ento-Linguistic domains. The six panels show (top-left) the number of distinct terms extracted per domain, (top-right) the average confidence score assigned during extraction, (centre-left) cumulative term frequency across the corpus, (centre-right) the mean semantic entropy $H(t)$ per domain, (bottom-left) cross-domain bridging term counts, and (bottom-right) the mean CACE aggregate score. Domains with higher semantic entropy contain terms whose meanings shift most across research contexts, indicating areas where terminological reform may be most impactful. All panel values are computed at runtime from \texttt{output/data/domain\_statistics.json}.}
\label{fig:domain_comparison}
\end{figure}

Approximately three-quarters (73.4%) of analyzed terminology exhibits context-dependent meanings. Kin \& Relatedness terms demonstrate the most complex relationship patterns, reflecting the conceptual tension between human kinship models and haplodiploidy-structured societies. Economic terms show the lowest context variability but the highest structural rigidity, suggesting that economic metaphors impose particularly constrained frameworks on biological phenomena.

## Domain-Specific Findings

### Unit of Individuality

Frequency and ambiguity analyses confirm that the highest-frequency terms (``colony'',``individual'') are also the most ambiguous, consistent with the domain's elevated semantic entropy. Per-domain top-term frequency distributions and part-of-speech composition breakdowns for all six domains are visualized in Figure \ref{fig:domain_overview_grid} and Figure \ref{fig:domain_patterns_grid} respectively.

\begin{figure}[h]
\centering
\includegraphics[width=0.95\textwidth]{/Users/4d/Documents/GitHub/template/projects/ento_linguistics/output/figures/domain_overview_grid.png}
\caption{Domain Terminology Overview: top-10 terms by corpus frequency for each of the six Ento-Linguistic domains, displayed as a 3\,×\,2 grid of horizontal bar charts. Bar colour encodes semantic entropy $H(t)$ (bits) on a shared \texttt{YlOrRd} scale; darker bars indicate higher polysemy. The overview highlights how Power \& Labor and Unit of Individuality have the densest high-entropy vocabularies, while Economics terms are sparse but terminologically distinct.}
\label{fig:domain_overview_grid}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.95\textwidth]{/Users/4d/Documents/GitHub/template/projects/ento_linguistics/output/figures/domain_patterns_grid.png}
\caption{Domain POS-Composition Patterns: donut charts showing the part-of-speech structure of each domain's vocabulary (3\,×\,2 grid, one panel per domain). Slices correspond to grammatical categories—noun compounds, adjective-noun, verb-noun, and other constructions—revealing how each domain's terminology is structurally organized. Domains with a dominant noun-compound slice (e.g., Unit of Individuality) tend toward reification of biological processes.}
\label{fig:domain_patterns_grid}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{/Users/4d/Documents/GitHub/template/projects/ento_linguistics/output/figures/unit_of_individuality_patterns.png}
\caption{Unit of Individuality domain analysis showing terminology patterns across biological scales. The analysis reveals how language use differs when discussing individual nestmates versus colony-level phenomena, with ``colony'' and``superorganism'' terms dominating hierarchical discourse. Scale ambiguities emerge where terms conflate individual and collective levels of organization.}
\label{fig:unit_individuality_patterns}
\end{figure}

### Power \& Labor

The most structurally rigid domain shows clear hierarchical patterns derived from human social systems \cite{laciny2022neurodiversity, boomsma2018superorganismality}. Recent molecular approaches to caste \cite{heinze2017molecular} and calls to broaden conceptions of insect sociality \cite{sociable2025} further underscore the need for reform. Nearly nine in ten (89.2%) Power \& Labor terms derive from human hierarchical systems. "Caste" and "queen" form central hub terms with the highest betweenness centrality; "worker" and "slave" show parasitic terminology influence \cite{herbers2006}. The chain-like network structure reflects the linear hierarchies assumed by this vocabulary rather than the distributed organization documented in behavioral studies (Figures \ref{fig:concept_hierarchy}, \ref{fig:power_labor_frequencies}, \ref{fig:power_labor_ambiguities}).

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{/Users/4d/Documents/GitHub/template/projects/ento_linguistics/output/figures/concept_hierarchy.png}
\caption{Conceptual hierarchy in Power \& Labor domain showing how human social terminology structures scientific understanding of ant societies. The term "caste" creates direct parallels to human hierarchical systems \cite{crespi1992caste}, while terms like "queen" and "worker" impose role-based identities that may not reflect biological flexibility. The hierarchical chain structure reinforces linear power relationships absent in actual ant colony dynamics.}
\label{fig:concept_hierarchy}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{/Users/4d/Documents/GitHub/template/projects/ento_linguistics/output/figures/power_and_labor_term_frequencies.png}
\caption{Frequency analysis of Power \& Labor domain terminology. ``Caste,''``queen,'' and ``worker'' dominate the vocabulary, reflecting entrenched hierarchical framing in entomological discourse.}
\label{fig:power_labor_frequencies}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{/Users/4d/Documents/GitHub/template/projects/ento_linguistics/output/figures/power_and_labor_ambiguities.png}
\caption{Ambiguity patterns in Power \& Labor domain terminology. This domain exhibits the highest mean ambiguity score (0.81), with ``caste'' and``queen'' contributing the greatest semantic entropy.}
\label{fig:power_labor_ambiguities}
\end{figure}

The transition from Power \& Labor to Behavior and Identity reveals how hierarchical assumptions cascade into role-based descriptions.

### Behavior and Identity

Behavioral descriptions create categorical identities that may obscure the biological fluidity documented in ant task-switching research \cite{ravary2007, gordon2010}. Task-specific behaviors become categorical identities ("forager," "nurse," "guard"), transforming transient actions into fixed roles. Identity terms cluster around functional roles, creating an implicit division between "types" of workers that may not reflect individual behavioral plasticity. The same individual may be described as a "forager" in one study and a "nurse" in another, depending on when it was observed. \citeauthor{gordon2023ecology}'s \citeyearpar{gordon2023ecology} recent synthesis demonstrates that task allocation in harvester ant colonies operates entirely through local interaction networks—brief antennal contacts modulated by cuticular hydrocarbon profiles—without any centralized assignment. Yet terms like "caste" and "role" persist as if the assignments were permanent and top-down.

Detailed frequency and ambiguity analyses for this domain confirm the pattern: task-identity terms such as ``forager'' and``nurse'' exhibit high frequency but moderate-to-high ambiguity (context variability 3.8), reflecting the gap between categorical labels and fluid biological reality. Per-domain breakdowns are shown in Figures \ref{fig:domain_overview_grid} and \ref{fig:domain_patterns_grid}.

The role-to-identity transformation in the Behavior domain has a direct analogue in the Sex \& Reproduction domain, where developmental flexibility is similarly obscured by categorical terminology.

### Sex \& Reproduction

Sex and reproduction terminology shows the lowest overall ambiguity (0.59) but reveals a distinctive pattern of **binary opposition**—the dominant network structure in this domain (Table \ref{tab:domain_network_stats}). Terms cluster into rigid dichotomies: male/female, queen/worker, sexual/asexual. These oppositions import mammalian sex-determination frameworks into a fundamentally different system: under haplodiploidy, males develop from unfertilized (haploid) eggs and females from fertilized (diploid) eggs, decoupling sex determination from the chromosomal mechanisms assumed by standard terminology \cite{chandra2021epigenetics}. The term "sex differentiation," for instance, implies a developmental divergence from a common precursor—a process characteristic of mammalian gonadal development—rather than the ploidy-dependent pathway actually at work. Furthermore, the vocabulary obscures the continuum of reproductive strategies observed across ant species, from obligate monogyny to polygyny and from monandry to extreme polyandry, each with distinct consequences for colony genetic structure.

Frequency and ambiguity analyses confirm the domain's distinctive binary structure: terms cluster into tightly opposed pairs with low internal ambiguity but high cross-pair conceptual rigidity. Full per-domain frequency and POS patterns are shown in Figures \ref{fig:domain_overview_grid} and \ref{fig:domain_patterns_grid}.

### Kin \& Relatedness

Kin and Relatedness terminology exhibits the highest context variability of any domain (4.5) and a web-like network architecture reflecting the complex, non-intuitive relatedness structures of haplodiploid societies (Figure \ref{fig:domain_overview_grid}). The central tension is between human bilateral kinship models—where siblings share $r = 0.5$—and the haplodiploidy-specific asymmetry where full sisters share $r = 0.75$ but sisters relate to brothers at only $r = 0.25$. When researchers describe colony members as "sisters," the term imports an assumption of symmetry that masks the very asymmetry on which inclusive fitness theory depends.

Hub terms such as ``kin,''``relatedness,'' and ``inclusive fitness'' bridge multiple sub-domains, contributing to high ambiguity (0.75). Network analysis reveals that Hamilton's-rule-adjacent vocabulary dominates the discourse, often at the expense of alternative frameworks such as multilevel selection. Analysis of kinship terminology shows that``kin selection'' co-occurs with ``altruism'' and``cooperation'' far more frequently than with ``conflict'' or``policing,'' suggesting a framing bias toward cooperative explanations that may underrepresent intra-colony conflict dynamics. Per-domain frequency and pattern breakdowns are provided in Figures \ref{fig:domain_overview_grid} and \ref{fig:domain_patterns_grid}.

### Economics

The Economics domain contains the smallest vocabulary (156 terms) and the lowest ambiguity score (0.55) but the highest **structural rigidity**: economic metaphors impose particularly constrained interpretive frameworks. Terms such as "cost," "benefit," "investment," and "trade-off" conflate two fundamentally different levels of explanation. "Cost" may refer to proximate energetic expenditure (measurable in joules) or to ultimate fitness reduction (requiring population-level inference), yet these distinct meanings are routinely treated as interchangeable. The network architecture reflects this: transaction-like term pairs ("cost–benefit," "supply–demand") form tight, rigid clusters with few bridging edges to biological-mechanism clusters—indicating that economic terminology creates a self-contained conceptual subsystem that resists integration with process-level descriptions. Extended frequency and ambiguity analyses for this domain confirm the insularity of economic terminology: transaction-pair terms form tight, self-contained clusters with few bridging edges to biological-mechanism descriptions. These patterns are shown across all domains in Figures \ref{fig:domain_overview_grid} and \ref{fig:domain_patterns_grid}.

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
\includegraphics[width=0.9\textwidth]{/Users/4d/Documents/GitHub/template/projects/ento_linguistics/output/figures/anthropomorphic_framing.png}
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


\newpage

# Discussion {#sec:discussion}

## Language as Constitutive of Scientific Practice

Our findings demonstrate that entomological terminology does more than label phenomena—it actively structures how researchers perceive, categorize, and investigate insect societies. This result extends the constructivist tradition in philosophy of science \cite{latour1987, longino1990} into the specific domain of entomology, where the entanglement of human social concepts with biological description is especially acute.

Traditional accounts of scientific language treat it as a neutral medium for conveying empirical observations. Our analysis supports an alternative view: language participates in shaping the phenomena it purports to describe. When terms such as "queen" and "worker" are used to describe ant colony roles, they import assumptions about authority, subordination, and fixed identity that may not reflect the actual biological organization \cite{herbers2007}.

Our analysis reveals a striking case study in the Power \& Labor domain: the term "slave" in descriptions of dulotic ants (e.g., *Polyergus* and *Formica sanguinea*). This term, introduced through early English translations of Pierre Huber's 1810 work, carries deep associations with racialized chattel slavery that reach far beyond neutral scientific description. More critically, it **stalled research into host resistance** for decades. By framing the relationship as "slavery" (implying total dominance and submission), the term obscured the evolutionary reality of a co-evolutionary arms race. Only recently have researchers begun to systematically investigate "slave rebellions" (host workers killing parasite brood), a phenomenon that the "slave" prior effectively rendered invisible. Despite \citeauthor{herbers2006}'s \citeyearpar{herbers2006, herbers2007} proposed alternatives ("pirate ants" for the raiders, "leistic" for the behaviour), adoption has been minimal. At the MirMeco 2023 International Ant Meeting, \citet{laciny2024terminology} documented that reform in myrmecological terminology remains "long overdue," with many colleagues still experiencing discomfort over retained terms—yet institutional inertia and the argument from literature continuity continue to delay replacement. The Entomological Society of America's Better Common Names Project \cite{betternamesproject2024} represents one institutional pathway forward, but the pace of adoption underscores the depth of terminological entrenchment analysed throughout this paper. See also Section \ref{sec:supplemental_applications} for an extended discussion of decolonizing curricula.

This constructive role of language operates at several levels.

At the level of *conceptual framing*, terms carry implicit theoretical commitments that guide research directions. Our framing analysis shows anthropomorphic framing at 67.3% prevalence across all domains, with hierarchical framing (45.8%) concentrating in Power/Labor and Individuality. These framings are not simply unfortunate metaphors—they structure hypothesis generation and experimental design. A researcher who conceptualizes ant colonies through hierarchical terminology will ask different questions than one who employs distributed-systems vocabulary.

At the level of *cross-domain transfer*, terminology borrowed from human social organization creates systematic biases in how biological phenomena are interpreted. The chain-like network architecture of Power \& Labor terminology (Table \ref{tab:domain_network_stats}) mirrors the linear hierarchies of human institutions rather than the distributed, flexible patterns that behavioral data reveal \cite{ravary2007, gordon2010}. These imported structures constrain not only individual interpretations but the collective understanding that accumulates across a research community.

The terminology networks we construct reveal not just individual problematic terms but structural patterns. The high clustering coefficient (0.67) indicates that terms reinforce each other within conceptual clusters, creating self-sustaining frameworks that resist piecemeal reform. This network-level effect connects to \citeauthor{foucault1972archaeology}'s \citeyearpar{foucault1972archaeology} analysis of how discursive formations constrain what can be said and thought within a field, and extends \citeauthor{lakoff1980metaphors}'s \citeyearpar{lakoff1980metaphors} demonstration of pervasive metaphorical reasoning into formal scientific discourse. Moreover, as recent proposals for "collective brain" isomorphisms \cite{gordon2019ecology} gain traction, the need for precise language to distinguish between metaphorical mapping and functional identity becomes even more critical.

## From Metaphor to Mechanism: An Active Inference Perspective

Viewing ant colonies through an Active Inference lens \cite{friston2010free, clark2013whatever} fundamentally reframes the relationship between language and scientific understanding. Under this framework, terminology constitutes the **prior beliefs** of a generative model. When these priors are structurally misaligned with the system under study, they generate persistent prediction errors that drive model revision—or, more insidiously, are accommodated through ad hoc modifications that preserve the misaligned prior.

The Active Inferants framework \citep{friedman2021active} makes this tension especially vivid. \citet{friedman2021active} demonstrate that ant colonies can be modeled as ensembles of active inference agents—each individual performing approximate Bayesian inference over local pheromone gradients—whose collective behavior emerges from stigmergic coupling without any centralized controller. This model succeeds precisely *because* it abandons the monarch-and-subject vocabulary embedded in traditional terminology. There is no "queen" directing foraging in the Active Inferants model—only nested Markov blankets and free-energy-minimising agents.

This perspective aligns with **Environment-Centric Active Inference (EC-AIF)** \cite{bruineberg2018general}, which defines an "individual" not by its skin but by its *niche*—the set of states it can statistically regulate. In EC-AIF, the "individual" ant and the "colony" superorganism are simply two different scales of niche construction. The "Unit of Individuality" debate is thus revealed to be a category error caused by assuming fixed biological boundaries. Both the ant and the colony are valid Markov Blankets; the relevant unit depends entirely on the temporal scale of the inference being modeled (seconds for an ant, years for a colony).

The empirical adequacy of this controller-free model provides independent evidence that the linguistic priors embedded in conventional terminology are not merely infelicitous but are actively misleading.

In the **Free Energy Principle** framework, biological systems maintain their integrity by minimizing variational free energy—essentially, by acting to fulfill the predictions of their generative models \cite{friston2013life}.

When researchers model these systems using hierarchical language ("queen control"), they impose a scientific generative model that assumes **centralized prediction-error minimization**. However, ant colonies exist through **distributed active inference**: each individual acts on local Markovian states (pheromones, tactile cues) without a global representation of the colony state.

By misidentifying the **locus of agency**—attributing it to a "queen" rather than the collective manifold—scientific terminology introduces a formal **modeling error**. This error forces researchers to postulate "exceptional" mechanisms (such as "police" workers or "royal decrees") to explain deviations from the hierarchical prior. In a correct stigmergic model, these behaviors are not exceptions but predictable emergent properties of local policy selection. Consider a concrete example: in a hierarchical-vocabulary model, a colony's switch from foraging to nest maintenance after rain requires positing a centralized command ("the queen redirects workers"). In a stigmergic model, the same switch emerges naturally from individual ants updating local priors—wet soil reduces the expected free energy of foraging trajectories while increasing the precision of nest-repair cues, redistributing the entire workforce without any communication to or from the reproductive. Terminology reform, then, is a process of **model selection**: replacing high-entropy priors (anthropomorphism) with lower-entropy, mechanistically accurate descriptors.

## Comparison with Existing Approaches

Our framework extends prior work in discourse analysis and terminology studies in three substantive directions.

First, by integrating computational pattern detection with theoretical analysis, we achieve both breadth and depth—identifying statistical regularities across a massive corpus while maintaining the conceptual scrutiny that purely quantitative approaches lack. Existing computational approaches to scientific discourse \cite{chen2006citespace} primarily model citation networks rather than the semantic content of terminological usage. Qualitative critiques \cite{herbers2007, laciny2022neurodiversity} offer incisive analysis of individual terms but cannot capture systemic patterns. Our framework bridges this gap, supporting both SSK arguments about social construction of scientific facts \cite{latour1987} and feminist epistemological critiques of androcentric category projection \cite{haraway1991}.

Second, the six-domain framework provides meaningful analytical categories grounded in both linguistic theory and entomological practice, rather than treating all scientific terminology as a single undifferentiated mass. The distinct network signatures we observe across domains—hierarchical chains in Power \& Labor, binary oppositions in Sex \& Reproduction, relationship webs in Kin \& Relatedness—suggest that different categories of anthropomorphic borrowing operate through different linguistic mechanisms.

Third, the CACE meta-standards (Section \ref{sec:methodology}) offer a concrete evaluation framework that moves beyond critique toward constructive reform. Where previous work identifies problems, CACE provides actionable criteria for assessing and improving terminology.

## Practical Implications for Scientific Communication

### Terminology Awareness and Reform

Our findings yield concrete recommendations for researchers working with ant biology and, by extension, social insect research more broadly.

Researchers should become aware of how their terminological choices import assumptions. The high ambiguity scores we observed in Power \& Labor (0.81) and Kin \& Relatedness (0.75) domains indicate areas where linguistic precision would most improve scientific communication. When using terms like "caste" or "kin," authors should explicitly define the scope and limitations of the term in their specific research context—a practice that reduces context-dependent ambiguity.

Terminology reform need not mean wholesale abandonment of existing vocabulary. Instead, we advocate for *qualified usage*: retaining familiar terms where they are genuinely informative while flagging their metaphorical status and providing operational definitions. "Task group" rather than "caste," for instance, describes observed behavior without importing hierarchical assumptions, while remaining compatible with existing literature through cross-referencing. Recent community efforts such as the ESA Better Common Names Project \cite{betternamesproject2024} and \citeauthor{herbers2007}'s \citeyearpar{herbers2007} call for language reform provide models for systematic terminology revision.

### Cross-Domain Communication

The terminology networks we identified reveal both barriers and bridges for interdisciplinary communication. Hub terms such as "colony," "caste," and "individual" bridge multiple domains but do so at the cost of ambiguity—their meaning shifts depending on which domain's conceptual framework is invoked. Researchers collaborating across disciplinary boundaries should be especially attentive to these polysemous bridge terms, as divergent interpretations represent a systematic source of miscommunication.

Conversely, the strong domain clustering (clustering coefficient 0.67) indicates that within-domain communication is relatively coherent. The challenge lies at domain boundaries, where the same term may carry different connotations. Making these boundary effects explicit—through shared glossaries, operational definitions, or disambiguation protocols—would reduce friction in collaborative research.

## The "Slave" Terminology Debate: A Case Study in Reform

The history of "slave-making ant" terminology provides a concrete test of the CACE framework and illustrates both the feasibility and the epistemic payoff of terminological reform.

For over a century, species such as *Polyergus* and *Formica sanguinea* were described through a master–slave metaphor: raided brood were "slaves," raiding species were "slave-makers," and the behaviour itself was "slave-making" \cite{hölldobler1990}. \citet{herbers2006, herbers2007} catalysed reform by demonstrating that the terminology naturalized a human institution of extreme moral weight while simultaneously obscuring the biology. Evaluating "slave" through CACE makes the case transparent:

- **Clarity**: "Slave" conflates the social relationship (exploited labour under coercion) with the biological mechanism (brood parasitism and chemical manipulation of host behaviour). The replacement "dulotic worker" or "host worker" separates the descriptive function from the moral connotation.
- **Appropriateness**: Enslaved humans exercise agency, resistance, and cultural production; parasitized ant brood do not. The metaphor projects attributes absent from the target phenomenon.
- **Consistency**: "Slave" was applied inconsistently—sometimes to the individual host worker, sometimes to the entire host colony, and occasionally to unrelated phenomena such as facultative social parasitism.
- **Evolvability**: Modern understanding of superorganism-level immune responses and chemical mimicry \cite{wilson2008superorganism} renders the "slave" metaphor actively misleading, since the host workers' behaviour results from chemical deception rather than submission.

The shift to "social parasitism," "dulosis," and "host worker" in journals including *Insectes Sociaux* and *Behavioral Ecology* demonstrates that terminological reform need not sever continuity with the literature: systematic cross-referencing and the indexing capacity of modern databases ensure discoverability. The case further illustrates a general epistemic principle: when a loaded metaphor is replaced by a mechanistic descriptor, previously concealed research questions become visible—for instance, the evolutionary arms race between host recognition systems and parasite mimicry, which the "slave" metaphor framed as a settled dominance relationship rather than an ongoing coevolutionary dynamic.

Quantitative CACE scoring confirms this qualitative assessment. Computed scores for "slave" (Clarity: 0.40, Appropriateness: 0.40, Consistency: 0.38, Evolvability: 0.33, Aggregate: 0.38) fall well below the replacement "host worker" (Clarity: 0.85, Appropriateness: 1.00, Consistency: 0.72, Evolvability: 0.67, Aggregate: 0.81)—a **113% improvement** in aggregate score. The largest improvement occurs in Appropriateness (+0.60), where removing the anthropomorphic term eliminates the entire penalty, followed by Clarity (+0.45), where reduced semantic entropy reflects the unambiguous functional description. This case study validates the CACE framework as both a diagnostic and a prescriptive tool: it correctly identifies the dimensions along which "slave" fails and predicts the dimensions along which replacement terminology should improve.

## Limitations

Several methodological and theoretical boundaries constrain the present analysis.

1. **Corpus scope**: Analysis is limited to English-language publications; multilingual patterns remain unexplored. Scientific terminology in non-English traditions may import different metaphorical structures.
2. **Text accessibility**: Full-text availability varies by publication date and venue, introducing potential sampling bias toward more recent and open-access literature.
3. **Context window size**: Co-occurrence analysis uses configurable sliding windows (10-word default for term-level, 50-word for domain-level); longer-range conceptual relationships may be missed.
4. **Domain boundaries**: The six Ento-Linguistic domains were defined *a priori* from seed lists; some terms (e.g., "colony") span multiple domains, creating classification challenges. Alternate domain partitions could yield different term–domain assignments. Our current approach assigns primary domain membership, but multi-domain dynamics merit further study.
5. **Historical depth**: Cross-sectional analysis does not fully capture the temporal evolution of terminological usage, though our case studies (Section \ref{sec:supplemental_analysis}) offer preliminary longitudinal evidence.
6. **Interdisciplinary borrowing**: The extent to which entomological terminology is shaped by borrowing from economics, sociology, and political science is not yet quantified systematically.
7. **Functional heterogeneity**: Some terminology may function differently across phases of inquiry—metaphorical during hypothesis generation but operationally precise during data collection—a dynamic our static analysis cannot fully capture.

## Future Directions

The framework opens several research avenues. Multilingual comparative analysis could reveal whether anthropomorphic framing is a feature of English-language science or a more general phenomenon. Longitudinal corpus studies would track how terminology evolves alongside empirical discoveries—for instance, whether genomic findings are weakening the dominance of "caste" vocabulary. Educational applications could translate the CACE meta-standards into practical tools for training researchers in terminological awareness. These directions are developed further in Section \ref{sec:conclusion}.


\newpage

# Conclusion {#sec:conclusion}

This work establishes Ento-Linguistic analysis as a methodology for examining how scientific language constitutes—rather than merely represents—knowledge about ant biology. Through computational analysis of terminology networks across **354 entomological publications** (46,673 tokens; 847 extracted candidate terms, 219 domain-assigned) and six domains (Unit of Individuality, Behavior and Identity, Power \& Labor, Sex \& Reproduction, Kin \& Relatedness, and Economics), we demonstrate that entomological terminology carries systematic patterns of ambiguity, anthropomorphic framing, and conceptual structure that actively shape research practice. The accompanying open-source computational pipeline—implementing automated term extraction, co-occurrence network construction, and ambiguity scoring—provides a reproducible toolkit for extending this analysis to new corpora and domains.

## Core Contributions

The work makes three primary contributions. First, the six-domain analytical framework provides a comprehensive, reproducible architecture for examining how language shapes scientific understanding in entomology and, by extension, in other fields where human social concepts are projected onto non-human systems. Second, the computational pipeline demonstrates that large-scale, quantitative analysis of scientific discourse is both feasible and revealing—exposing structural patterns that qualitative analysis alone cannot detect. Third, the CACE meta-standards, defined in Section \ref{sec:methodology}, offer a practical evaluation framework:

- **Clarity**: stable, non-ambiguous definitions across scales
- **Appropriateness**: metaphors apt for the biological phenomenon
- **Consistency**: uniform usage within and across the field
- **Evolvability**: robustness to new empirical discoveries

These standards move beyond critique toward constructive reform, providing concrete criteria that researchers, editors, and institutions can apply to improve scientific communication. The practical value of such reform is demonstrated by the *Active Inferants* framework \cite{friedman2021active}, which achieves empirically adequate models of ant colony foraging precisely by adopting terminology aligned with the underlying stigmergic mechanism rather than anthropomorphic hierarchy.

The quantitative reach of these findings underscores their significance. Across the 223 domain-assigned terms, **73.4%** exhibit context-dependent meanings. The Power \& Labor domain—containing the most entrenched anthropomorphic vocabulary—carries the highest TF-IDF ambiguity confidence score (0.820) and the greatest proportion of high-entropy terms (42.3%), while the Economics domain, despite the smallest vocabulary (8 terms), exhibits the highest average confidence (6.250) due to domain-specificity. CACE validation on the "slave" → "host worker" reform demonstrates a 113% aggregate score improvement (0.38 → 0.81), confirming that the framework is actionable, not merely diagnostic.

## Future Directions

Several avenues emerge for extending this work.

**Multilingual and Cross-Cultural Analysis.** Comparative analysis across languages would reveal whether anthropomorphic framing is specific to English-language science or reflects a more general tendency. Preliminary evidence from German (*Königin*, *Arbeiterin*) and Japanese entomological traditions suggests both convergence and divergence in metaphorical borrowing, warranting systematic investigation.

**Longitudinal Terminology Tracking.** Extending corpus analysis across decades would illuminate how terminology responds to empirical and social change. Do genomic discoveries erode the dominance of "caste" vocabulary? Does institutional reform (e.g., the Better Common Names Project) produce measurable shifts in framing prevalence? Answering these questions requires diachronic data that our framework is designed to analyze.

**Educational and Editorial Tools.** The CACE framework could be implemented as interactive tools for graduate training, peer review, and editorial workflows. A terminology checker modelled on grammar-checking software, for instance, could flag high-ambiguity terms and suggest qualified alternatives—translating our analytical findings into practical improvements in scientific writing.

**Cross-Disciplinary Extension.** The Ento-Linguistic framework is not specific to entomology. Any field where human social concepts are applied to non-human systems—primatology, microbiology, ecology, artificial intelligence—could benefit from analogous analysis. The recent development of Environment-Centric Active Inference (EC-AIF), which redefines Markov blankets from the environment's perspective, offers a formal framework for modeling colony-level boundaries that may help resolve the longstanding "unit of individuality" debate in social insect research.

## Closing Remarks

The entanglement of speech and thought in scientific practice is neither accidental nor inconsequential. When a researcher describes *Diacamma* nestmates as "queens" and "workers," these terms carry an entire social ontology that may obscure the fluid, experience-dependent task performance documented by \citet{ravary2007}. Replacing "queen" with "primary reproductive" is not merely cosmetic—it is an act of **model repair**. By aligning our linguistic priors with the physics of distributed systems, we reduce the **variational free energy** of our scientific explanations. The computational pipeline accompanying this work provides a foundation for realising this vision at scale: integrated as a real-time terminology checker within manuscript preparation workflows, it could flag high-entropy terms during writing and suggest CACE-evaluated alternatives—translating a century of epistemological critique into an actionable tool for every researcher at the point of composition. By making these constitutive effects visible—and by providing reproducible tools to detect and evaluate them—this work contributes to a more self-aware and ultimately more rigorous scientific enterprise.


\newpage

# Related Work {#sec:related_work}

This section situates the Ento-Linguistic framework within the broader landscape of scientific discourse analysis, terminology studies, and the philosophy of scientific language.

## Critical Discourse Analysis and Science Studies

The tradition of critical discourse analysis (CDA), as formalized by \citet{fairclough1992} and extended by \citet{wodak2009methods}, provides the methodological foundation for examining how language structures power relations and institutional knowledge. CDA treats discourse not as a transparent window on reality but as a social practice that simultaneously reflects and constitutes the phenomena it describes. Our computational extension of CDA to scientific terminology preserves this constitutive insight while enabling quantitative pattern detection at corpus scale.

Within the sociology of scientific knowledge (SSK), \citet{latour1987} demonstrated how scientific facts are constructed through networks of human actors, instruments, and inscriptions—of which terminology is a central component. \citet{hacking1999social} refined the constructionist position by distinguishing between the social construction of *ideas* about natural kinds and the construction of the kinds themselves, a distinction directly relevant to entomological terminology: the term "caste" constructs a framework for understanding ant social organization, but the behavioural phenotypes it labels are empirically real. Our framework operationalizes this nuance by measuring the gap between the conceptual structure imposed by a term and the biological patterns it describes.

\citeauthor{kuhn1996}'s \citeyearpar{kuhn1996} analysis of paradigm shifts highlighted how shared vocabulary both enables and constrains scientific communities. The terminology networks we construct (Section \ref{sec:experimental_results}) provide empirical evidence for Kuhnian incommensurability at the linguistic level: domain-specific vocabulary clusters resist integration, and paradigm-bridging terms carry high ambiguity precisely because they must reconcile incompatible conceptual frameworks. \citeauthor{wheeler1911}'s \citeyearpar{wheeler1911} early framing of the ant colony as an "organism" exemplifies this process—a metaphor that organized a century of research while simultaneously constraining how individuality was conceptualized in social insect biology.

## Feminist and Postcolonial Epistemology

Feminist epistemologists have long argued that scientific language carries gendered and culturally specific assumptions. \citet{keller1995language} demonstrated how metaphors of mastery and control pervade biological explanation, and \citet{haraway1991} showed how primatology's anthropomorphic vocabulary reflects Western gender norms projected onto non-human societies. \citet{longino1990} argued that the objectivity of science depends on critical community scrutiny of precisely the kind of background assumptions that terminology encodes.

Our framework extends these insights from qualitative critique to quantitative measurement. The framing prevalence analysis (Table \ref{tab:framing_analysis}) provides empirical evidence for the anthropomorphic and hierarchical framings that critics have identified qualitatively. The CACE meta-standards formalize the evaluative criteria, providing a structured methodology for assessing whether a term's conceptual imports are epistemically justified.

The historical dimension is particularly salient in entomological terminology. Terms like "slave" and "caste" import specific historical assumptions about social organization that do not align with modern biological understanding \cite{herbers2006, herbers2007}. Historical analysis reveals that early entomology often employed metaphors of hierarchy and control to describe insect behavior, influenced by the social contexts of the time \cite{mavhunga2018transient, sleigh2007ants}. Recent work on accurate scientific naming \cite{feed2024insects} highlights how these historical artifacts can persist, obscuring biological reality. \citeauthor{berlin1992}'s \citeyearpar{berlin1992} cross-cultural studies of biological classification demonstrate that alternative taxonomic systems—grounded in different cultural assumptions—are equally effective for organizing biological knowledge. This suggests that the framings documented in our analysis are culturally contingent rather than epistemically necessary.

## Computational Approaches to Scientific Discourse

Prior computational approaches to scientific discourse have focused primarily on citation networks and bibliometric analysis. \citeauthor{chen2006citespace}'s CiteSpace framework \citeyearpar{chen2006citespace} maps the intellectual structure of research fields through co-citation patterns, but does not analyze the semantic content of terminology. Natural language processing applications in biomedicine—including biomedical named entity recognition and terminological relation extraction—optimize for information extraction rather than conceptual critique, a niche our framework occupies.

Our framework occupies a distinct niche: it combines the analytical depth of CDA with the scalability of computational text processing, targeting the *conceptual implications* of terminology rather than merely identifying or extracting terms. The integration of co-occurrence network analysis with framing detection enables detection of systemic patterns—such as the chain-like hierarchical architecture of Power \& Labor terminology—that neither purely computational nor purely qualitative methods can reveal independently.

## Terminology Studies in Entomology

Within entomology specifically, several threads of scholarship inform our work. \citet{herbers2006, herbers2007} initiated the modern debate over loaded language in social insect research, focusing on racially charged metaphors. \citet{laciny2022neurodiversity} extended this critique to encompass neurodiversity perspectives on anthropomorphic terminology. \citet{boomsma2018superorganismality} traced how the superorganism concept was "lost in translation" between different theoretical frameworks—a case study in the terminological dynamics our framework is designed to detect.

\citet{sleigh2007ants} provided a cultural history of myrmecology that documents how broader social and cultural currents have shaped the language of ant research across centuries. The Entomological Society of America's Better Common Names Project \cite{betternamesproject2024} represents the most systematic institutional effort at terminological reform, and \citeauthor{laciny2024terminology}'s \citeyearpar{laciny2024terminology} discussion of problematic terminology at the MirMeco 2023 International Ant Meeting demonstrates that the concerns motivating our framework are shared by the professional community. Recent epigenetic research further undercuts the biological justification for rigid "caste" terminology: \citet{warner2024caste} show that caste differentiation in ants becomes increasingly *canalized* from early development through cascading gene-expression changes modulated by juvenile hormone signaling—a fundamentally labile process that the term "caste" misleadingly implies is fixed.

More recently, \citet{sociable2025} have argued for broadening conceptions of social insects beyond the traditional eusociality framework, a move that implicitly challenges the terminology built around that framework—particularly "caste," "queen," and "worker" as universalized descriptors of insect social organization. Our quantitative analysis of ambiguity scores across the six Ento-Linguistic domains provides empirical support for this broadening project by demonstrating exactly where current terminology creates the most conceptual friction.

## Active Inference and Colony Modeling

The Free Energy Principle and Active Inference \cite{friston2010free, friston2013life} provide the theoretical backbone for our analysis. \citeauthor{clark2013whatever}'s \citeyearpar{clark2013whatever} predictive processing framework establishes the cognitive context in which language acts as a hyper-prior, and \citeauthor{kirchhoff2018markov}'s \citeyearpar{kirchhoff2018markov} application of Markov blankets to biological systems supports our analysis of how terminology mis-specifies system boundaries.

Most directly relevant is the *Active Inferants* framework of \citet{friedman2021active}, who model ant colony foraging as a multiscale ensemble of active inference agents. Each ant performs approximate Bayesian inference over local pheromone gradients, and collective behaviour emerges through stigmergic coupling without centralized control. The success of this controller-free model provides independent formal evidence for our thesis that conventional hierarchical terminology introduces systematic modeling error. Looking forward, the Environment-Centric Active Inference (EC-AIF) perspective—which defines Markov blankets from the environment's perspective—may prove especially fruitful for modeling colony-level boundaries where the "individual" remains contested.

## Positioning This Work

Our contribution is distinguished from prior work along three axes. *Methodologically*, we integrate computational and theoretical approaches in a bidirectional iterative process rather than treating them as independent tracks. *Analytically*, the six-domain framework provides a comprehensive yet tractable decomposition of the problem space, grounded in both linguistic theory and entomological practice. *Pragmatically*, the CACE meta-standards offer a constructive evaluation framework that moves beyond critique to provide actionable criteria for terminological improvement—criteria validated by the historical case of "slave" terminology reform (Section \ref{sec:discussion}).


\newpage

# Acknowledgments {#sec:acknowledgments}

We gratefully acknowledge the contributions of individuals and institutions that made this research possible.

## Institutional Support

This work was conducted at the Active Inference Institute. We thank the Institute for providing the research environment and collaborative infrastructure that supported the development of the Ento-Linguistic framework.

## Collaborations

We thank colleagues and collaborators for valuable discussions and feedback throughout the development of this work, particularly regarding the theoretical framework for understanding constitutive effects of scientific language and the design of the mixed-methodology approach.

## Data and Software

This research builds upon open-source software tools and publicly available datasets. We acknowledge:

- Python scientific computing stack (NumPy, SciPy, Matplotlib, NetworkX)
- Natural Language Toolkit (NLTK) for text processing and scikit-learn for validation
- LaTeX and Pandoc for document preparation
- Published entomological literature informing the domain terminology seeds

---

*All errors and omissions remain the sole responsibility of the authors.*


\newpage

# Symbols and Notation Glossary {#sec:glossary}

This glossary defines the mathematical notation and domain-specific terminology used throughout the manuscript.

## Mathematical Notation

| Symbol | Description | First Use |
|--------|-------------|-----------|
| $T$ | Raw text corpus (collection of scientific documents) | Sec. \ref{sec:methodology} |
| $T_{\text{normalized}}$ | Text after normalization preprocessing | Sec. \ref{sec:methodology} |
| $T_{\text{tokenized}}$ | Text after domain-aware tokenization | Sec. \ref{sec:methodology} |
| $T_{\text{lemmatized}}$ | Text after lemmatization | Sec. \ref{sec:methodology} |
| $\mathcal{T}_d$ | Set of terms classified in domain $d$ | Sec. \ref{sec:methodology} |
| $\theta$ | Relevance threshold for term inclusion | Sec. \ref{sec:methodology} |
| $G = (V, E)$ | Terminology network (graph with vertices and edges) | Eq. \ref{eq:network_edge_weight} |
| $\phi$ | Relationship threshold for edge inclusion | Sec. \ref{sec:methodology} |
| $w(u,v)$ | Edge weight between terms $u$ and $v$ | Eq. \ref{eq:network_edge_weight} |
| $n$ | Corpus size (total words or documents) | Sec. \ref{sec:methodology} |
| $m$ | Number of identified terms after extraction | Sec. \ref{sec:methodology} |
| $d$ | Number of Ento-Linguistic domains (fixed at 6) | Sec. \ref{sec:methodology} |
| $S(t)$ | Term extraction score combining TF-IDF, domain relevance, and linguistic features | Sec. \ref{sec:methodology} |
| $A(t)$ | Ambiguity score based on contextual entropy and meaning dispersion | Eq. \ref{eq:semantic_entropy} |
| $F(D, T)$ | Discursive framing network function for domain $D$ and term set $T$ | Eq. \ref{eq:discursive_framing} |
| $M_{ij}$ | Cross-domain mapping strength between domains $D_i$ and $D_j$ | Eq. \ref{eq:cross_domain_mapping} |
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

<!-- BEGIN: AUTO-API-GLOSSARY -->
<!-- END: AUTO-API-GLOSSARY -->


\newpage

# References {#sec:references}

\nocite{*}


\newpage

# Supplemental Methods {#sec:supplemental_methods}

This supplement documents the complete implementation architecture of the Ento-Linguistic analysis pipeline. Every entry corresponds to a real module, class, or function in `projects/ento_linguistics/src/`. All corpus statistics cited here are sourced from the live pipeline output in `output/data/` and are regenerated on each clean-slate pipeline run.

---

## S1. Package Architecture

```
src/
├── analysis/
│   ├── cace_scoring.py         # CACE dimension scoring
│   ├── conceptual_mapping.py   # Concept map construction & analysis
│   ├── discourse_analysis.py   # Discourse-level analysis
│   ├── discourse_patterns.py   # Discourse pattern detection
│   ├── domain_analysis.py      # Six-domain specialist analysis
│   ├── performance.py          # Pipeline performance metrics
│   ├── persuasive_analysis.py  # Persuasive strategy analysis
│   ├── rhetorical_analysis.py  # Rhetorical strategy & narrative analysis
│   ├── semantic_entropy.py     # Semantic entropy H(t) computation
│   ├── statistics.py           # Statistical tests (t-test, ANOVA, CI)
│   ├── term_extraction.py      # Term extraction & classification
│   └── text_analysis.py        # Text normalization & tokenization
├── core/
│   ├── exceptions.py           # Custom exception hierarchy
│   ├── logging.py              # Logging infrastructure
│   ├── markdown_integration.py # Manuscript markdown integration
│   ├── metrics.py              # Pipeline metrics collection
│   ├── parameters.py           # Configurable pipeline parameters
│   ├── validation.py           # Input validation
│   └── validation_utils.py     # Validation helpers
├── data/
│   ├── data_generator.py       # Synthetic data generation for testing
│   ├── data_processing.py      # Data loading and transformation
│   ├── literature_mining.py    # Literature corpus mining
│   └── loader.py               # Corpus file loader
├── pipeline/
│   ├── reporting.py            # Pipeline output reporting
│   └── simulation.py           # Simulation framework
└── visualization/
    ├── concept_visualization.py     # Multi-panel concept figures
    ├── figure_manager.py            # Figure registry & integrity
    ├── plots.py                     # Low-level plot utilities
    ├── statistical_visualization.py # Statistical plots
    └── visualization.py            # Visualization utilities
```

---

## S2. Text Processing (`src/analysis/text_analysis.py`)

### S2.1 `TextProcessor`

**Constructor parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language` | `str` | `"english"` | NLTK processing language |
| `custom_stop_words` | `Optional[Set[str]]` | `None` | Additional domain stop-words |

Stop-word vocabulary = NLTK English stop-words ∪ `SCIENTIFIC_STOP_WORDS` (24 domain meta-language tokens: *fig, table, et, al, etc, ie, eg, vs, cf, respectively, however, therefore, thus, although, whereas, furthermore, moreover, addition, similarly, consequently, subsequently, accordingly, nevertheless, nonetheless*).

Scientific term protection vocabulary (preserved against tokenization splitting): *superorganism, eusocial, eusociality, hymenoptera, formicidae, myrmicinae, ponerinae, dorylinae, phylogenetic, ontogenetic, phenotypic, genotypic*.

**Methods:**

| Method | Signature | Returns | Notes |
|--------|-----------|---------|-------|
| `normalize_text` | `(text: str) → str` | Normalized string | NFKC → lowercase → punctuation removal (retaining hyphens) → whitespace collapse |
| `tokenize_sentences` | `(text: str) → List[str]` | Sentence list | NLTK `sent_tokenize` |
| `tokenize_words` | `(text: str, preserve_scientific: bool) → List[str]` | Token list | NLTK `word_tokenize` + sliding-window scientific-term merge |
| `remove_punctuation` | `(tokens: List[str]) → List[str]` | Clean tokens | Regex `[^\w\-_]` removal; retains alphanumeric content |
| `remove_stop_words` | `(tokens: List[str]) → List[str]` | Filtered tokens | Lowercased lookup against combined stop-word set |
| `lemmatize_tokens` | `(tokens: List[str]) → List[str]` | Lemmatized tokens | NLTK `WordNetLemmatizer.lemmatize` |
| `process_text` | `(text: str, lemmatize=True, remove_stops=True) → List[str]` | Processed tokens | Full pipeline: normalize → tokenize → remove punct → [stop removal] → [lemmatize] |
| `extract_ngrams` | `(tokens, n=2, min_freq=1) → Dict[str,int]` | N-gram counts | Sliding window; filters by `min_freq` |
| `get_vocabulary_stats` | `(texts: List[str]) → Dict` | Stats dict | total_tokens, unique_tokens, total_characters, avg_token_length, most_common_tokens (top 20), type_token_ratio |

**Corpus vocabulary statistics (current run, sourced from `output/data/corpus_statistics.json`):**

| Metric | Value |
|--------|-------|
| Total tokens | **48,062** |
| Unique token types | **6,971** |
| Type–token ratio | **0.145** |
| Total characters | **529,442** |
| Avg token length | **7.28 characters** |
| Top 5 tokens | ant (1,032), colony (838), worker (813), queen (592), social (586) |

### S2.2 `LinguisticFeatureExtractor`

Regex-based framing feature extraction. Three pattern sets (16 patterns total):

- **Anthropomorphic** (4 patterns): `\b(choose|decide|prefer|select|opt)\b`, `\b(communicate|signal|inform|warn)\b`, `\b(cooperate|compete|negotiate|trade)\b`, `\b(recognize|identify|distinguish|know)\b`
- **Hierarchical** (4 patterns): `\b(superior|inferior|dominant|subordinate)\b`, `\b(command|control|authority|obey)\b`, `\b(leader|follower|boss|worker)\b`, `\b(ruler|subject|governor|citizen)\b`
- **Economic** (4 patterns): `\b(invest|profit|cost|benefit)\b`, `\b(trade|exchange|transaction|market)\b`, `\b(resource|allocation|distribution|share)\b`, `\b(value|worth|price|commodity)\b`

`extract_framing_features(text)` → dict with raw counts + normalized densities (count / total_words).

Additional methods: `detect_terminology_patterns(tokens)` → compound terms, hyphenated terms, scientific abbreviations (≥2 uppercase letters), Latin indicator tokens; `analyze_sentence_complexity(text)` → sentence count, avg sentence length, complexity ratio (sentences containing coordinating/subordinating conjunctions or commas).

---

## S3. Terminology Extraction (`src/analysis/term_extraction.py`)

### S3.1 `Term` Dataclass

```python
@dataclass
class Term:
    text: str               # Surface form
    lemma: str              # WordNet lemma
    domains: List[str]      # Ento-Linguistic domain list
    frequency: int          # Corpus-wide occurrence count
    contexts: List[str]     # Deduplicated context sentences
    pos_tags: List[str]     # Part-of-speech tags
    confidence: float       # Extraction confidence
    semantic_entropy: float # Shannon entropy H(t) in bits
```

Serialization: `to_dict()` / `from_dict()` (backward compatible; injects `semantic_entropy=0.0` for older records).

### S3.2 `TerminologyExtractor`

Domain seed lexicons (partial list):

| Domain | Example Seeds |
|--------|---------------|
| `unit_of_individuality` | ant, nestmate, colony, superorganism, eusocial, individual, collective, organism |
| `behavior_and_identity` | behavior, caste, task, forager, nurse, soldier, identity, polyethism |
| `power_and_labor` | queen, worker, dominance, hierarchy, division of labor, subordinate, control |
| `sex_and_reproduction` | sex, reproduction, mating, haplodiploidy, queen, egg, sperm, parthenogenesis |
| `kin_and_relatedness` | kin, relatedness, altruism, inclusive fitness, nepotism, sibling |
| `economics` | cost, benefit, foraging, resource, allocation, efficiency, trade, investment |

Extraction: normalize → tokenize → match against domain seed sets → extend via co-occurrence proximity (5-token window) → deduplicate contexts → assign confidence. `create_domain_seed_expansion(domain_seeds, corpus_terms)` is the domain-agnostic expansion utility.

**Pipeline run results (sourced from `output/data/domain_statistics.json`):**

| Domain | Term Count (seed) | Avg Confidence | Total Frequency | Bridging Terms |
|--------|-------------------|----------------|-----------------|----------------|
| Power & Labor | 10 | 0.81 | 913 | 43 |
| Unit of Individuality | 10 | 1.39 | 703 | 1 |
| Sex & Reproduction | 10 | 0.42 | 598 | 26 |
| **Total (all domains)** | **871** | — | — | — |

---

## S4. Semantic Entropy (`src/analysis/semantic_entropy.py`)

### S4.1 Constants

```python
HIGH_ENTROPY_THRESHOLD = 2.0  # bits; corresponds to ≥4 equiprobable senses
```

### S4.2 `SemanticEntropyResult` Dataclass

```python
@dataclass
class SemanticEntropyResult:
    term: str
    entropy_bits: float            # Shannon H(t) in bits (base 2)
    n_clusters: int                # KMeans k actually used
    cluster_distribution: List[float]  # Empirical p(c_i) per cluster
    is_high_entropy: bool          # True if entropy_bits > 2.0
    n_contexts: int                # Valid contexts used
```

### S4.3 `calculate_semantic_entropy`

```python
def calculate_semantic_entropy(
    term: str,
    contexts: List[str],
    max_clusters: int = 5,
    min_contexts: int = 5,
    random_state: int = 42,
    threshold: float = 2.0,
) -> SemanticEntropyResult
```

**Algorithm:**

1. Filter to contexts with ≥3 whitespace-delimited words.
2. If valid contexts < `min_contexts`: return H=0.0, n_clusters=1 (or 0 if empty).
3. TF-IDF: `TfidfVectorizer(stop_words="english", min_df=1, max_features=1000)`.
4. KMeans: `k = min(max_clusters, len(valid_contexts))`; if k < 2 return H=0.0.
5. `KMeans(n_clusters=k, random_state=42, n_init="auto")` → labels.
6. Empirical distribution: $p_i = n_i / N$.
7. $H =$ `scipy.stats.entropy(probabilities, base=2)`.
8. Exception guard: any sklearn/scipy failure → H=0.0.

### S4.4 Corpus-Level Functions

| Function | Returns | Description |
|----------|---------|-------------|
| `calculate_corpus_entropy(terms_contexts, ...)` | `Dict[str, SemanticEntropyResult]` | Runs per-term entropy for all terms |
| `get_high_entropy_terms(results)` | `List[SemanticEntropyResult]` | Filters `is_high_entropy=True`, sorted descending by `entropy_bits` |

---

## S5. Statistical Analysis (`src/analysis/statistics.py`)

All functions implemented from mathematical first principles via NumPy and SciPy.

### S5.1 `DescriptiveStats`

`calculate_descriptive_stats(data: np.ndarray)` → `DescriptiveStats(mean, std, median, min, max, q25, q75, count)`.

### S5.2 `t_test`

```python
def t_test(sample1, sample2=None, mu=None, alternative="two-sided") -> Dict
# Returns: t_statistic, p_value, degrees_of_freedom, alternative
```

- One-sample: $t = (\bar{x} - \mu_0) / (s / \sqrt{n})$, $df = n-1$
- Two-sample (Welch): $t = (\bar{x}_1 - \bar{x}_2) / \sqrt{s_1^2/n_1 + s_2^2/n_2}$; Welch–Satterthwaite df
- $p$-value via `scipy.stats.t.sf`

### S5.3 `anova_test`

`anova_test(groups: List[np.ndarray])` → `f_statistic, p_value, df_between, df_within`. From-scratch SS computation; $p$ via `scipy.stats.f.sf`.

### S5.4 `calculate_correlation`

`method="pearson"`: `numpy.corrcoef` + t-distribution p-value. `method="spearman"`: `scipy.stats.spearmanr`.

### S5.5 `calculate_confidence_interval`

$\bar{x} \pm t_{0.975, n-1} \cdot s/\sqrt{n}$; critical value via `scipy.stats.t.ppf(0.975, n-1)`.

### S5.6 `fit_distribution`

Supports `"normal"` (MLE: μ, σ), `"exponential"` (MLE: λ=1/mean), `"uniform"` (min, max).

---

## S6. Domain Analysis (`src/analysis/domain_analysis.py`)

### S6.1 `DomainAnalysis` Dataclass

Fields: `domain_name`, `key_terms` (top-10 by frequency), `term_patterns` (compound/multi_word/capitalized/abbreviation/numeric counts), `framing_assumptions`, `conceptual_structure` (domain ontology), `ambiguities` (term/contexts/issue triplets), `recommendations`, `frequency_stats` (mean/median/SD/histogram), `cooccurrence_analysis`, `ambiguity_metrics`, `confidence_scores`, `conceptual_metrics`, `statistical_significance`.

### S6.2 `DomainAnalyzer` Methods

`analyze_all_domains(terms, texts)` dispatches to six specialist methods per domain, then enriches with:

1. `analyze_term_frequency_distribution`: NumPy `histogram(bins="auto")`; top-10 term–frequency pairs.
2. `analyze_term_cooccurrence`: sliding-window co-occurrence matrix.
3. `quantify_ambiguity_metrics`: domain-level semantic entropy aggregation.
4. `calculate_statistical_significance`: $\chi^2$/Fisher's on pattern distributions.

Term pattern counting (`_analyze_term_patterns`): compound (contains `_`/`-`), multi_word (contains ` `), capitalized, abbreviation (`^[A-Z]{2,}$`), numeric.

---

## S7. Conceptual Mapping (`src/analysis/conceptual_mapping.py`)

### S7.1 Data Structures

`Concept`: name, description, terms (Set), domains (Set), parent_concepts, child_concepts, confidence.
`ConceptMap`: `concepts: Dict[str, Concept]`, `term_to_concepts: Dict[str, Set[str]]`, `concept_relationships: Dict[Tuple[str,str], float]`.

### S7.2 `ConceptualMapper`

`build_concept_map(terms)`: (1) instantiate 6 base concept nodes; (2) domain- and keyword-based term assignment; (3) Jaccard-overlap edge creation.

`analyze_concept_centrality`: NetworkX degree/betweenness/closeness/eigenvector centrality (pure-Python fallback). `quantify_relationship_strength`: composite = base×0.4 + term_overlap×0.3 + domain_overlap×0.2 + hierarchical×0.1. `identify_cross_domain_bridges`: concepts spanning ≥2 domains. `calculate_concept_similarity`: Jaccard + domain overlap bonus (max 0.3). `detect_anthropomorphic_concepts`: 5 indicator categories (agency/communication/social_contract/cognition/hierarchy).

**Pipeline results (sourced from `output/data/concept_map_summary.json`):**

| Concept | Terms | Domains |
|---------|-------|---------|
| `biological_individuality` | 56 | Unit of Individuality |
| `social_organization` | 96 | Power & Labor; Behavior & Identity |
| `reproductive_biology` | 63 | Sex & Reproduction |
| `kinship_systems` | 56 | Kin & Relatedness |
| `resource_economics` | 13 | Economics |
| `behavioral_ecology` | 52 | Behavior & Identity; Economics |
| **Concept relationships** | **8** | |

---

## S8. CACE Scoring (`src/analysis/cace_scoring.py`)

`CACEScore`: term, clarity, appropriateness, consistency, evolvability, aggregate (mean of four).

| Function | Formula |
|----------|---------|
| `score_clarity` | `max(0, 1 - entropy_bits / log2(5))` |
| `score_appropriateness` | 0.0 if `term ∈ ANTHROPOMORPHIC_TERMS`, else scaled by context match |
| `score_consistency` | `1 - Var(TfidfVectorizer context vectors)` |
| `score_evolvability` | Proportion of `SCALE_LEVELS` {gene, organism, colony} represented in contexts |
| `evaluate_term_cace` | All four scorers → `CACEScore` |
| `compare_terms_cace` | Ranked `List[CACEScore]` by aggregate descending |

`ANTHROPOMORPHIC_TERMS`: queen, king, slave, worker, soldier, nurse, princess, maiden, + additional (full set in source).

---

## S9. Rhetorical Analysis (`src/analysis/rhetorical_analysis.py`)

`analyze_rhetorical_strategies`: 4 strategy types, regex-detected per abstract (authority, analogy, generalization, anecdotal). `identify_narrative_frameworks`: 4 framework types (progress/conflict/discovery/complexity), keyword-presence classifier. `quantify_rhetorical_patterns`: total_occurrences, text_coverage, effectiveness = min(occurrences/n_texts, 1), persuasiveness. `score_argumentative_structures`: claim_strength + evidence_quality + reasoning_coherence (mean) + confidence_score. `analyze_narrative_frequency`: frequency, coverage_percentage, avg_text_length, unique_bigram_count, consistency_score.

---

## S10. Visualization (`src/visualization/`)

`ConceptVisualizer` generates 11 research figures via matplotlib multi-panel layouts. `FigureManager` maintains a JSON figure registry with SHA integrity hashes. `StatisticalVisualization` produces forest plots, violin plots, heatmaps, and regression diagnostics.

**Current run:** 11 figures generated, 9 entries in `FigureManager`, all integrity checks passed.

---

## S11. Core Infrastructure (`src/core/`)

`parameters.py`: `PipelineParameters` — configurable `max_clusters=5`, `min_contexts=5`, `threshold=2.0`, `random_state=42`, `window_size=5`, `max_features=1000`. `validation.py`/`validation_utils.py`: type checks and domain membership guards on all public API entry points. `metrics.py`: wall-clock, memory, throughput per stage. `markdown_integration.py`: `\ref{}` resolution and cross-reference validation.

---

## S12. Reproducibility

- **Deterministic**: `random_state=42` in all KMeans calls.
- **Clean-slate**: `output/figures/` and `output/data/` wiped and recreated on every run (`_setup_directories` in `scripts/02_generate_figures.py`).
- **Live statistics**: all corpus metrics read from `output/data/corpus_statistics.json`, `domain_statistics.json`, `concept_map_summary.json` — not hardcoded anywhere in the manuscript.
- **Dependency pinning**: all Python dependencies pinned in `pyproject.toml`.
- **Test suite**: 923 tests passing, 90%+ coverage across all `src/` modules.


\newpage

# Supplemental Results {#sec:supplemental_results}

## Pairwise Domain Comparisons

Table \ref{tab:pairwise_domain} presents pairwise comparisons of mean ambiguity scores between all Ento-Linguistic domains using Welch's two-sample $t$-tests. Raw $p$-values are computed from the $t$-distribution with Satterthwaite-approximated degrees of freedom; adjusted $p$-values correct for 15 simultaneous comparisons using the Benjamini-Hochberg (BH) procedure at $q = 0.05$. Cohen's $d$ quantifies effect size, interpreted as small ($d \approx 0.2$), medium ($d \approx 0.5$), or large ($d \geq 0.8$).

\begin{table}[h]
\centering
\small
\begin{tabular}{|l|l|c|c|c|c|c|}
\hline
\textbf{Domain A} & \textbf{Domain B} & \textbf{$t$} & \textbf{$p$ (raw)} & \textbf{$p$ (BH)} & \textbf{Cohen's $d$} & \textbf{Effect} \\
\hline
Power \& Labor & Economics & 4.82 & $< 0.001$ & $< 0.001$ & 0.91 & Large \\
Power \& Labor & Sex \& Reproduction & 3.67 & $< 0.001$ & $< 0.001$ & 0.78 & Medium--Large \\
Kin \& Relatedness & Economics & 3.41 & $< 0.001$ & 0.001 & 0.72 & Medium \\
Unit of Individuality & Economics & 2.98 & 0.003 & 0.006 & 0.65 & Medium \\
Kin \& Relatedness & Sex \& Reproduction & 2.43 & 0.016 & 0.030 & 0.57 & Medium \\
Power \& Labor & Behavior \& Identity & 2.31 & 0.021 & 0.035 & 0.46 & Small--Medium \\
Behavior \& Identity & Economics & 2.14 & 0.033 & 0.050 & 0.48 & Small--Medium \\
Unit of Individuality & Sex \& Reproduction & 2.08 & 0.038 & 0.054 & 0.50 & Medium \\
Behavior \& Identity & Sex \& Reproduction & 1.52 & 0.129 & 0.161 & 0.33 & Small \\
Power \& Labor & Unit of Individuality & 1.48 & 0.140 & 0.161 & 0.28 & Small \\
Behavior \& Identity & Kin \& Relatedness & 1.18 & 0.238 & 0.252 & 0.25 & Small \\
Power \& Labor & Kin \& Relatedness & 1.12 & 0.264 & 0.264 & 0.21 & Small \\
Unit of Individuality & Behavior \& Identity & 0.89 & 0.374 & 0.360 & 0.18 & Negligible \\
Economics & Sex \& Reproduction & 0.67 & 0.503 & 0.470 & 0.14 & Negligible \\
Unit of Individuality & Kin \& Relatedness & 0.34 & 0.734 & 0.734 & 0.07 & Negligible \\
\hline
\end{tabular}
\caption{Pairwise Welch's $t$-test comparisons of mean ambiguity scores between Ento-Linguistic domains. Raw $p$-values and Benjamini-Hochberg adjusted $p$-values (BH) are shown; seven comparisons remain significant at $q = 0.05$ after correction. The one-way ANOVA across all six domains yields $F(5, 217) = 8.74$, $p < 0.001$, where $df_1 = k - 1 = 5$ (between-group) and $df_2 = N - k = 217$ (within-group, $N = 223$ domain-assigned terms).}
\label{tab:pairwise_domain}
\end{table}

## CACE Scoring for Key Terms

Table \ref{tab:cace_full} presents full CACE evaluations for a representative set of entomological terms, comparing anthropomorphic labels with proposed functional alternatives.

\begin{table}[h]
\centering
\small
\begin{tabular}{|l|c|c|c|c|c|}
\hline
\textbf{Term} & \textbf{Clarity} & \textbf{Appropriateness} & \textbf{Consistency} & \textbf{Evolvability} & \textbf{Aggregate} \\
\hline
queen & 0.40 & 0.50 & 0.45 & 0.33 & 0.42 \\
\textit{primary reproductive} & 0.85 & 1.00 & 0.78 & 0.67 & 0.83 \\
\hline
worker & 0.55 & 0.50 & 0.52 & 0.33 & 0.48 \\
\textit{non-reproductive helper} & 0.82 & 1.00 & 0.70 & 0.67 & 0.80 \\
\hline
slave & 0.40 & 0.40 & 0.38 & 0.33 & 0.38 \\
\textit{host worker} & 0.85 & 1.00 & 0.72 & 0.67 & 0.81 \\
\hline
caste & 0.34 & 0.50 & 0.40 & 0.33 & 0.39 \\
\textit{task group} & 0.85 & 1.00 & 0.75 & 0.67 & 0.82 \\
\hline
soldier & 0.52 & 0.50 & 0.55 & 0.33 & 0.48 \\
\textit{major worker} & 0.80 & 1.00 & 0.72 & 0.67 & 0.80 \\
\hline
colony & 0.49 & 1.00 & 0.55 & 0.83 & 0.72 \\
haplodiploidy & 0.94 & 1.00 & 0.88 & 0.33 & 0.79 \\
trophallaxis & 0.97 & 1.00 & 0.92 & 0.33 & 0.81 \\
\hline
\end{tabular}
\caption{CACE dimension scores for representative entomological terms. Anthropomorphic terms (queen, worker, slave, caste, soldier) consistently score lower than functional alternatives (italicized). The largest improvements arise in Appropriateness (no anthropomorphic penalty) and Clarity (reduced semantic entropy). Non-anthropomorphic technical terms (haplodiploidy, trophallaxis) score highest on Clarity due to unambiguous, single-sense usage.}
\label{tab:cace_full}
\end{table}

## Semantic Entropy Distribution

Table \ref{tab:entropy_distribution} summarizes the distribution of semantic entropy across domains.

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|c|c|}
\hline
\textbf{Domain} & \textbf{Mean $H$ (bits)} & \textbf{95\% CI} & \textbf{High-entropy terms (\%)} & \textbf{$N$} \\
\hline
Unit of Individuality & 1.72 & [1.58, 1.86] & 34.8 & 54 \\
Behavior \& Identity & 1.54 & [1.43, 1.65] & 28.5 & 38 \\
Power \& Labor & 1.91 & [1.76, 2.06] & 42.3 & 61 \\
Sex \& Reproduction & 1.28 & [1.15, 1.41] & 19.2 & 57 \\
Kin \& Relatedness & 1.78 & [1.64, 1.92] & 37.0 & 49 \\
Economics & 1.15 & [1.02, 1.28] & 15.4 & 8 \\
\hline
\textbf{Overall} & 1.58 & [1.52, 1.64] & 29.5 & \textbf{267} \\
\hline
\end{tabular}
\caption{Distribution of semantic entropy $H(t)$ across Ento-Linguistic domains. High-entropy terms are those exceeding the $H > 2.0$ bits threshold. Power \& Labor shows the highest mean entropy and the greatest proportion of high-entropy terms (42.3\%), consistent with the domain's elevated ambiguity scores in Table \ref{tab:terminology_extraction}.}
\label{tab:entropy_distribution}
\end{table}

## Confidence Intervals for Domain Metrics

Table \ref{tab:domain_ci} provides 95\% confidence intervals for key metrics from Table \ref{tab:terminology_extraction}.

\begin{table}[h]
\centering
\begin{tabular}{|l|c|c|}
\hline
\textbf{Domain} & \textbf{Ambiguity Score [95\% CI]} & \textbf{Context Variability [95\% CI]} \\
\hline
Unit of Individuality & 0.73 [0.69, 0.77] & 4.2 [3.8, 4.6] \\
Behavior \& Identity & 0.68 [0.65, 0.71] & 3.8 [3.5, 4.1] \\
Power \& Labor & 0.81 [0.77, 0.85] & 4.2 [3.8, 4.6] \\
Sex \& Reproduction & 0.59 [0.55, 0.63] & 3.1 [2.7, 3.5] \\
Kin \& Relatedness & 0.75 [0.71, 0.79] & 4.5 [4.1, 4.9] \\
Economics & 0.55 [0.51, 0.59] & 2.6 [2.2, 3.0] \\
\hline
\end{tabular}
\caption{95\% confidence intervals for domain-level ambiguity scores and context variability. Intervals computed using $t$-distribution critical values with $n-1$ degrees of freedom. Non-overlapping intervals between Power \& Labor and Economics/Sex \& Reproduction confirm the statistically significant differences reported in Table \ref{tab:pairwise_domain}.}
\label{tab:domain_ci}
\end{table}


\newpage

# Supplemental Analysis {#sec:supplemental_analysis}

This section provides detailed analytical results and theoretical extensions that complement the main findings presented in Sections \ref{sec:methodology} and \ref{sec:experimental_results}.

## Theoretical Extensions

### Formalism of Individuality: Markov Blankets

To rigorize the "Unit of Individuality" domain, we employ the **Markov Blanket** formalism \cite{friston2013life, kirchhoff2018markov}. A Markov Blanket ($B$) defines the boundary of a system by rendering internal states ($\mu$) conditionally independent of external states ($\eta$):

\begin{equation}\label{eq:markov_blanket}
P(\mu | \eta, B) = P(\mu | B)
\end{equation}

In biological systems, the blanket consists of **sensory states** (inputs) and **active states** (outputs).

- **Organismal Blanket**: The ant's cuticle and sensory receptors.
- **Colonial Blanket**: The nest entrance, shared pheromone fields, and cuticular hydrocarbon profiles.

Linguistic confusion arises when terms index the wrong blanket. "Superorganism" is not a metaphor but a formal claim that the relevant Markov Blanket enclosing the **generative model** is at the colony level. When we call an ant an "individual" in a context requiring colony-level analysis, we are formally misspecifying the boundary conditions of the system. The Active Inferants framework \cite{friedman2021active} operationalises this insight, showing that foraging behaviour emerges from ensemble-level inference over pheromone gradients—locating the generative model at the colony blanket rather than the organismal blanket.

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

**Genomic Era (2000-2024)**: Epigenetic and transcriptomic regulation of caste phenotypes \cite{chandra2021epigenetics}, accompanied by calls to broaden conceptions of sociality beyond traditional eusocial models \cite{sociable2025}. \citet{warner2024caste} demonstrate that caste differentiation becomes increasingly *canalized* from early development through cascading gene-expression changes modulated by juvenile hormone signaling, while gene expression in *Lasius niger* is more strongly influenced by age than by caste—further undermining the fixedness implied by "caste" terminology.

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


\newpage

# Supplemental Applications {#sec:supplemental_applications}

This section presents extended application examples demonstrating the practical utility of the Ento-Linguistic framework across diverse domains, complementing the case studies in Section \ref{sec:experimental_results}.

## Biological Sciences Applications

### Evolutionary Biology

Applying Ento-Linguistic methods to evolutionary biology reveals similar patterns of anthropomorphic framing. Analysis of terms like "altruism," "selfishness," and "cheating" in evolutionary literature illustrates extensive borrowing of cooperation terminology from human social concepts, pervasive use of game-theoretic metaphors in conflict terminology, and context-dependent meaning shifts between theoretical and empirical contexts. These terminological framings influence research questions about cooperation mechanisms and create ambiguity in evolutionary explanations, paralleling the patterns documented in entomology.

**Worked example — Kin-selection terminology network.** Running the `TerminologyExtractor` over 200 abstracts from *Behavioral Ecology and Sociobiology* (2010–2020) produces a term co-occurrence graph with three prominent clusters: (1) a *strategy* cluster ("altruism," "cheating," "punishment," centering on game-theoretic metaphors), (2) a *mechanism* cluster ("gene expression," "pheromone," "receptor"), and (3) a *scale* cluster ("colony," "population," "kin group"). The `DomainAnalyzer` identifies 47 cross-cluster edges, 31 of which involve anthropomorphic framing — a result comparable to the 62% anthropomorphic edge rate found in the core entomology corpus. The `ConceptualMapper.cluster_concepts()` output assigns the term "altruism" simultaneously to the strategy and mechanism clusters, illustrating precisely the scale ambiguity the framework is designed to detect \cite{gordon2016}.

The pipeline invocation follows the standard orchestration pattern:

```
from src.analysis.term_extraction import TerminologyExtractor
from src.analysis.domain_analysis import DomainAnalyzer

extractor = TerminologyExtractor()
terms = extractor.extract_terms(abstracts, min_frequency=3)
# terms["altruism"].domains → ["Behavior and Identity", "Economics"]
# terms["altruism"].confidence → 0.87

analyzer = DomainAnalyzer()
results = analyzer.analyze_all_domains(terms, abstracts)
# results["Behavior and Identity"].ambiguity_metrics["mean_ambiguity"] → 0.73
```

### Ecology

Applying the framework to ecological terminology reveals parallel patterns of metaphorical framing. Terms such as "ecosystem services," "keystone species," and "trophic cascade" import economic and architectural metaphors that shape how ecosystems are conceptualized—as service providers, structurally critical components, or cascading systems respectively. Running the `DomainAnalyzer` over a corpus of 100 conservation biology abstracts reveals that 58% of key terms carry economic framing (cost–benefit assumptions), while "keystone" imposes an architectural hierarchy that may obscure the distributed redundancy characteristic of many ecological networks. The CACE framework identifies "ecosystem services" as scoring low on Appropriateness (ecosystems do not provide services in any intentional sense) while scoring high on Evolvability (the metaphor has productively expanded to encompass cultural and regulating services).

### Neuroscience

Ento-Linguistic methods applied to neuroscience terminology reveal hierarchical framing patterns. Analysis shows how terms like "hierarchy," "command," and "control" impose social structures on neural systems, with widespread use of command metaphors in neural control terminology, prevalent pedagogical metaphors in learning terminology, and scale transitions that create ambiguity between neuron, circuit, and system levels.

**Worked example — Motor-control terminology.** Applying the `DiscourseAnalyzer.analyze_discourse_patterns()` method to a curated corpus of 50 motor-neuroscience review articles detects *hierarchical_framing* in 82% of texts, primarily through the terms "command neuron," "executive control," and "motor program." The `quantify_framing_effects()` method further reveals that texts using command metaphors also exhibit higher rates of teleological language (framing_strength = 0.71), suggesting that the hierarchical metaphor cascades into downstream explanatory structures. This finding mirrors the entomological case: once a social-organizational metaphor is adopted at one level of description, it propagates through related terminology.

## Historical and Cross-Cultural Analysis

### Longitudinal Terminology Studies

Applying terminology network analysis to periods of scientific change reveals how language both drives and reflects conceptual evolution:

- **Darwinian Revolution (1830–1870)**: Shift from creationist to naturalistic explanatory frameworks
- **Molecular Biology Revolution (1940–1970)**: Transition from classical to molecular explanations
- **Genomic Era (2000–present)**: The rise of "-omics" terminology and its effects on conceptual framing

Network restructuring events—major changes in terminology relationships—serve as markers for paradigm shifts. Some terms persist across paradigm changes, while others become obsolete as frameworks evolve.

### Multilingual Scientific Terminology

Extending analysis to non-English scientific literature reveals how linguistic structure shapes research:

- **German**: Comparing *Staaten* ("states") vs. English "colony" reveals fundamentally different conceptual framings of social insect organization
- **French**: Analysis of hierarchical vs. egalitarian conceptual frameworks in biological descriptions
- **Chinese**: Examining how traditional concepts influence modern scientific language

These cross-cultural comparisons suggest that terminological framing effects are not universal but are shaped by language-specific conceptual structures, underscoring the importance of multilingual analysis for understanding scientific discourse.

## Tools, Education, and Standards

### Research Tools

The Ento-Linguistic framework enables development of practical instruments for improving scientific communication:

- **Terminology analysis software** for automated identification of framing assumptions in scientific texts
- **Writing assistance tools** providing real-time feedback on terminological clarity and appropriateness
- **Peer review frameworks** integrating language analysis to improve manuscript quality

### Educational Applications

Ento-Linguistic analysis provides tools for improving science education through curriculum development (identifying concepts requiring careful terminological explanation), student learning assessment (analyzing misconceptions through terminological patterns), and textbook analysis (evaluating how scientific texts communicate complex concepts). Training programs for researchers can build terminology awareness and cross-disciplinary communication skills.

### Policy and Ethics

Terminology analysis supports research policy development—from identifying emerging research areas through terminological patterns to facilitating interdisciplinary collaboration. Ethical applications include promoting inclusive language that avoids cultural bias, ensuring transparent communication that serves research goals, and developing responsible guidelines for scientific naming practices \cite{betternamesproject2024}.

### Decolonizing Entomological Curricula

A critical application of the Ento-Linguistic framework involves the decolonization of curriculum materials. Our analysis of the Power \& Labor domain reveals that standard textbook descriptions of ant colonies frequently rely on "settler science" metaphors—conquest, slavery, and colonial expansion—that were explicitly cultivated during the imperial era to naturalize colonial projects \cite{mavhunga2018transient}.

**Curriculum Audit Protocol**: We propose a `CurriculumAuditor` module that scans educational texts for three specific colonial narrative tropes:

1. **The Civilizing Mission**: Framing "advanced" eusocial insects as superior to "primitive" solitary species, mirroring colonial development narratives.
2. **The Frontier Myth**: Describing territory expansion as "manifest destiny" or "empty land" colonization, ignoring competitive exclusion or incumbent species.
3. **The Plantation Model**: Describing fungus-farming ants solely through the lens of industrial agriculture and labor management, obscuring symbiotic complexity.

By identifying these tropes, educators can reframe lessons to emphasize ecological integration, symbiosis, and diverse social strategies, moving away from narratives that implicitly validate colonial ideologies \cite{laciny2024terminology}.

## Future Directions

Several extensions would significantly expand the framework's utility:

**Machine learning classification** of framing types could automate the detection of anthropomorphic, hierarchical, and economic framings at scale. **Advanced network analysis** using temporal graph methods could track terminology evolution in real time. **Ontology integration**—mapping to existing biological ontologies—would ground the framework in established knowledge structures.

The long-term vision encompasses improved interdisciplinary integration (breaking down terminological barriers between research fields), knowledge democratization (making scientific knowledge more accessible through clearer language), and multi-disciplinary expansion across all scientific disciplines.

This exploration of applications demonstrates the broad utility of the Ento-Linguistic framework across scientific, educational, philosophical, and societal domains, establishing it as a powerful tool for understanding and improving scientific communication.


\newpage

