# Optional Knowledge-Graph Layer

An optional, **LLM-gated** stage lifts the corpus from bibliometrics to hypothesis-level
evidence. For each record, a local language model extracts structured *assertions* —
each encoding a direction (supports / contradicts / neutral), a confidence score, and a
short natural-language justification — against the {{N_HYPOTHESES}} hypotheses declared in
configuration. Assertions are serialized as RDF-compatible nanopublications
[@kuhn2016decentralized] and scored by
a citation-weighted evidence function.

This stage is entirely optional and never runs in the offline default: with no language
model available it is skipped, and the hypothesis evidence scores read *pending*. The
hypotheses themselves — their names and scope — come from configuration and are reported
regardless of whether the scoring stage has run.

The hypotheses explored in this instance are: {{HYPOTHESIS_LIST}}.
