# Results: Hypotheses Explored

The template scores a configurable set of hypotheses about the topic. For this instance
{{N_HYPOTHESES}} hypotheses are declared in configuration; Table 2 lists them with their
scope and evidence score.

**Table 2. Hypotheses explored.**

{{HYPOTHESIS_TABLE}}

Evidence scores are produced by the optional, LLM-gated knowledge-graph stage. In the
offline default run that stage does not execute, so scores read *pending* — the
hypotheses, their names, and their scope are nonetheless reported directly from
configuration. A live run with a language model available populates the scores from
citation-weighted assertion extraction. Reported scores, when present, should be read as
relative rankings rather than calibrated probabilities: absolute magnitudes are inflated
by publication bias and the linguistic asymmetry of academic writing.
