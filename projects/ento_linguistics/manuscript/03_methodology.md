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
| Documents | **{{CORPUS_PUBLICATIONS}}** |
| Total processed tokens | **{{CORPUS_TOTAL_TOKENS}}** |
| Unique token types | **{{CORPUS_UNIQUE_TOKENS}}** |
| Candidate terms extracted | **{{CORPUS_CANDIDATE_TERMS}}** |
| Domain-assigned terms | **{{CORPUS_DOMAIN_TERMS}}** |

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
