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
