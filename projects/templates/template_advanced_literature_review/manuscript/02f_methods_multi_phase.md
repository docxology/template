# Multi-Phase Search Strategy and Results

## Three-Phase Architecture

This review employs a **three-phase search strategy** that progressively refines
coverage from broad foundational literature through technology-specific studies
to targeted molecular detection analyses. Each phase builds on prior phases through
cross-phase citation validation and shared deduplication.

### Phase 1: Exoplanet Atmosphere Foundation

**Objective:** Establish the foundational literature on exoplanet atmospheric
studies, covering the broadest range of research from 2010 onwards.

**Queries:**
1. `"exoplanet atmosphere" OR "exoplanet atmospheric"`
2. `"transit spectroscopy" AND "atmosphere"`
3. `"atmospheric composition" AND "exoplanet"`

**Engines:** arXiv, OpenAlex, Crossref, Semantic Scholar

**Deterministic Filters:**
- Minimum year: 2010
- Maximum year: 2026
- Minimum citation count: 0 (inclusive to capture recent work)

**Results:** {{PHASE_1_PAPERS}} papers discovered, forming the foundational
knowledge base for the review. This phase captures the broadest scope of
atmospheric research, from observational characterizations to theoretical
modeling studies.

### Phase 2: James Webb Space Telescope Studies

**Objective:** Identify papers specifically utilizing JWST observational data
for exoplanet atmospheric analysis, capturing the post-launch (2021+) surge in
high-precision spectroscopic observations.

**Queries:**
1. `"James Webb" AND "atmosphere" AND ("exoplanet" OR "planet")`
2. `"JWST" AND "transit" AND "spectroscopy"`
3. `"NIRSpec" OR "MIRI" OR "NIRCam" AND "exoplanet"`

**Engines:** arXiv, OpenAlex, Crossref, Semantic Scholar

**Deterministic Filters:**
- Minimum year: 2020 (capturing pre-launch calibration papers)
- Maximum year: 2026

**Dependencies:** Builds on Phase 1 foundational papers.

**Results:** {{PHASE_2_PAPERS}} papers after deterministic filtering. This phase
targets records associated with JWST-era observations and analysis. Any claim about
instrumental capability or scientific findings requires live, source-backed review.

### Phase 3: Molecular Detection Studies

**Objective:** Identify papers focused on detecting and analyzing specific
atmospheric molecules (H₂O, CO₂, CH₄, H₂S, Na, K) in the configured domain.

**Queries:**
1. `"water vapor" AND "exoplanet" AND ("detection" OR "abundance")`
2. `"carbon dioxide" AND "exoplanet" AND ("CO2" OR "atmosphere")`
3. `"methane" AND "exoplanet" AND ("CH4" OR "atmosphere")`
4. `"hydrogen sulfide" OR "H2S" AND "exoplanet"`
5. `"sodium" OR "potassium" AND "exoplanet atmosphere"`

**Engines:** arXiv, OpenAlex, Crossref, Semantic Scholar

**Deterministic Filters:**
- Minimum year: 2015
- Maximum year: 2026

**Dependencies:** Builds on both Phase 1 and Phase 2 papers.

**Results:** {{PHASE_3_PAPERS}} papers covering molecular detection across
diverse exoplanet populations, from hot Jupiters to terrestrial worlds.

## Cross-Phase Analysis

### Phase Overlap
The three phases produced complementary but overlapping corpora, with
{{CROSS_PHASE_OVERLAP_PCT}}% average Jaccard similarity between phases. Papers
discovered in multiple phases are tracked with full provenance, enabling
analysis of papers that span multiple research paradigms.

### Citation Validation
Cross-phase citation analysis records that {{CROSS_PHASE_CITATION_RATE}}% of
later-phase papers cite foundational work from Phase 1. This is a descriptive
connection statistic for the retained corpus; it does not establish methodological
coherence across the field.

### Combined Corpus
The deduplicated combined corpus contains {{CORPUS_SIZE}} unique papers spanning
{{YEAR_START}}--{{YEAR_END}} ({{YEAR_SPAN}} years). It provides a multi-phase
description of the retained retrieval slice, not a comprehensive account of the field.

## LLM-Based Content Filtering

Three LLM-based content filters were designed for this review:

1. **Study Type Classification**: Categorizes papers as observational,
   theoretical, review, or other. Keeps only observational and theoretical
   studies for analysis.

2. **JWST Data Analysis**: Identifies papers that analyze actual JWST
   observational data, distinguishing from theoretical JWST predictions.

3. **Molecular Detection Focus**: Filters for papers primarily focused on
   detecting and measuring specific atmospheric molecules.

These filters are configurable through `manuscript/config.yaml` and can be
enabled for specific phases or applied across the entire corpus. When enabled,
they use a local Ollama LLM instance for cost-effective, privacy-preserving
content classification.
