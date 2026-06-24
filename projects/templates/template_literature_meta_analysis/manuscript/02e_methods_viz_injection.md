# Visualization and Manuscript Injection

Figures are rendered headlessly (Agg backend) and deterministically from the analysis
artifacts: subfield distributions, the publication growth curve, the citation network,
topic–term bars, a term cloud, and embedding projections. This run produced
{{NUM_FIGURES}} figures.

The manuscript itself is generated, not hand-maintained. A variable computation step
reads the configuration and the pipeline outputs and emits a flat table of named values;
an injection step substitutes each named placeholder in these Markdown sections with its
computed value before rendering. Because the substitution is total — an unresolved
placeholder is an error, not a silent gap — every number in the rendered document is
guaranteed to trace to a committed artifact. Re-running the pipeline after a
configuration change re-computes the values and re-targets the prose automatically.
