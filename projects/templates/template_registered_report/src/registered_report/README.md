# registered_report package

Three modules:

- `protocol.py` — freezes preregistration plans under a content hash, validates
  stage/ethics metadata and required sections, builds deviation ledgers and
  review packets, and separates confirmatory from exploratory analyses.
- `demo_study.py` — deterministic, dependency-free demonstration study
  (no real data): seeded two-group data synthesis, a two-sided
  label-permutation test, a plan-driven `run_registered_analysis` binding, and
  the pure figure-data helpers (`hypothesis_outcome_map`, `analysis_plan_stages`,
  `deviation_timeline`) consumed by the figure renderers.
- `figures.py` — immutable figure label/filename/caption/generator specs and
  the deterministic Matplotlib renderers (`plot_hypothesis_map`,
  `plot_analysis_dag`, `plot_deviation_timeline`, `plot_permutation_result`),
  plus `render_all_figures`.

Computation and deterministic figure rendering live here (tested, importable);
the thin `scripts/` orchestrators handle argument parsing, output mirroring,
and JSON I/O.
