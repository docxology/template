The appendix `assumption_index` row points to
`output/data/analytical_assumption_index.json`. It binds
{{analytical_assumption_count}} finite Bernoulli-Ising assumption rows to
{{analytical_equation_count}} equation identifiers and generated artifacts, with
indexed status `{{analytical_assumptions_indexed}}`.

The point is to make analytical signposting mechanical. If an equation is added
without an assumption row, or if a row loses its evidence artifact, the index
gate fails and the manuscript cannot present the equation as part of the
validated finite toy proof surface.
