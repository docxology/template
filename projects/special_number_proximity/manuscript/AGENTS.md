# manuscript/ — `special_number_proximity`

## Files

| File | Role |
|------|------|
| `config.yaml` | Paper metadata, `testing.*`, `experiment.*` (`quadratic_candidates`, `compare_mod1`, `q_sensitivity`, `histogram_uniform_cap`, …) |
| `preamble.md` | LaTeX package block for PDF rendering |
| `references.bib` | Khinchin, Hurwitz, Cassels, Rockett–Szüsz |
| `00_abstract.md` | Abstract |
| `01_introduction.md` | Motivation |
| `02_problem_statement.md` | Definition of $\delta_Q$ |
| `03a_measure_theory_context.md` | Almost-all / badly approximable background |
| `03b_continued_fractions_method.md` | CF recurrence; implementation note |
| `03c_monte_carlo_design.md` | Reference laws and outputs |
| `03d_scaled_lattice_formulation.md` | $\|qx\|/q$ identity; Dirichlet residual |
| `03e_q_squared_quality.md` | $\mu_Q$ / Lagrange–Hurwitz scale |
| `03f_implementation_validation.md` | Three-$p$ lemma, tests, CF and lattice checks |
| `04_results.md` | JSON-driven results; two histograms |
| `05_conclusion.md` | Interpretation |
| `06_reproducibility.md` | Commands, paths, CLI |
| `07_limitations.md` | Scope and reference-law caveats |
| `08_notation_and_symbols.md` | Symbols, pooled reference definition |
| `09_reader_guide_constants.md` | Short notes per registered constant |

Conventions: [`../docs/manuscript_conventions.md`](../docs/manuscript_conventions.md) (not part of the built PDF).

## Cross-refs

Figures under `../output/figures/` (`proximity_histogram.png`, `proximity_histogram_pooled.png`, `proximity_histogram_mu.png`).
