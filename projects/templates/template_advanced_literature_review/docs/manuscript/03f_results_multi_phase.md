# Multi-Phase Results and Cross-Phase Analysis

## Phase-Specific Findings

### Foundation Phase (Phase 1)

The configured foundation phase retained {{PHASE_1_PAPERS}} records after its search,
filtering, and de-duplication rules. Its taxonomy includes transit spectroscopy,
emission spectroscopy, phase-curve analysis, and direct imaging. These labels describe
the configured retrieval design; the synthetic fixture cannot establish how widely
those approaches occur in the published literature.

### JWST Phase (Phase 2)

Phase 2 retained {{PHASE_2_PAPERS}} records under the JWST-oriented queries and the
configured year filter (≥2020). The boundary is intended to include pre-launch
calibration work and post-launch observations. It is a design choice, not evidence
that the phase is exhaustive or that any instrument caused a change in the field.

### Molecular Detection Phase (Phase 3)

Phase 3 retained {{PHASE_3_PAPERS}} records under five configured molecule-oriented
query groups: H₂O, CO₂, CH₄, H₂S, and Na/K. The query groups operationalize the review
question; they do not assert that these are the most commonly detected species or that
the fixture establishes a scientific trend.

## Knowledge Graph Results

The optional knowledge-graph stage reports **{{TOTAL_ASSERTIONS}}** assertions from
the eligible sample. The configuration-derived hypothesis table is the authoritative
mapping from review question to score:

{{HYPOTHESIS_TABLE}}

The configured scores are descriptive evidence summaries, not calibrated probabilities,
causal effects, or conclusions about instrument performance. The table should be read
together with the claim ledger and source-tier metadata. A fixture run cannot establish
whether models and observations agree in the broader literature.

## Citation Network Analysis

The combined corpus contains **{{CITATION_EDGES}}** citation relationships
across **{{CITATION_NODES}}** papers, with a network density of
{{CITATION_DENSITY_PCT}}%. This is a descriptive statistic for the retained
corpus; it does not establish a field-wide citation structure or community claim.

## Reproducibility Assessment

Reproducibility assessment of the sampled papers revealed a mean composite
reproducibility score of {{REPRO_MEAN_SCORE}}, with {{REPRO_PAPERS_SCORED}}
papers successfully scored. This analysis examines the computational workflow
transparency of each paper, evaluating source data availability, method
documentation, experimental reproducibility, and output accessibility.
