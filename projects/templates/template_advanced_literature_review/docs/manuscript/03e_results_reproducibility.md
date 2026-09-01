# Results: Reproducibility Assessment

An optional, **LLM-gated** stage decomposes each paper's described pipeline into a
workflow graph of source, method, experiment, and sink steps, rates how reproducible
each step is from the paper's own text, and combines a content score with a structural
graph-coverage score into one composite reproducibility score per paper (geometric mean,
so a paper cannot buy a high score by being strong on one axis alone). Across
{{REPRODUCIBILITY_N_PAPERS_SCORED}} scored papers the mean composite score is
{{REPRODUCIBILITY_MEAN_SCORE}}, with {{REPRODUCIBILITY_LOW_SCORE_COUNT}} papers falling
below the configured low-score threshold.

## Low-Scoring Papers

Table 8 lists the papers with the lowest composite reproducibility scores, alongside
their content and structural component scores.

**Table 8. Low-scoring papers by composite reproducibility score.**

{{REPRODUCIBILITY_TABLE}}

## Gating and Defaults

This stage is optional and gated by full-text availability. With no fulltext
available and no language model configured, the stage is skipped and the
reproducibility aggregates read *pending* — the same graceful-degradation convention used by the
knowledge-graph assertion-extraction stage (see
[`02d_methods_knowledge_graph.md`](02d_methods_knowledge_graph.md)). When fulltext is
available and a language model is explicitly configured, the mean score, low-score
count, and per-paper table are populated from extracted workflow graphs. The default
fixture run does not imply that this optional model-backed assessment has occurred.

## Interpretation

A low composite score can reflect either weak content (the paper's own text does not
describe its sources, methods, experiments, or outputs in enough detail to rate highly)
or weak structure (the described steps do not chain into a coherent source-to-sink
pipeline, or reference steps that were never themselves described). The two axes are
reported separately in Table 8 precisely so a low composite score can be diagnosed
rather than treated as a single undifferentiated verdict.
