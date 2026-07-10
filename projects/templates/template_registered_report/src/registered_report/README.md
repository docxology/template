# registered_report package

Two modules:

- `protocol.py` — freezes preregistration plans under a content hash, validates
  stage/ethics metadata and required sections, builds deviation ledgers and
  review packets, and separates confirmatory from exploratory analyses.
- `demo_study.py` — deterministic, dependency-free demonstration study
  (no real data): seeded two-group data synthesis, a two-sided
  label-permutation test, a plan-driven `run_registered_analysis` binding, and
  the pure figure-data helpers (`hypothesis_outcome_map`, `analysis_plan_stages`,
  `deviation_timeline`) consumed by `scripts/generate_figures.py`.

Computation lives here (tested, importable); figure rendering and I/O live in
`scripts/`.
