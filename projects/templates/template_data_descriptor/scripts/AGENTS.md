# scripts - AGENTS.md

Keep scripts thin and delegate all validation, figure-data preparation,
rendering, publication, and verification to `src/data_descriptor/`.
`generate_figures.py` calls the typed producer in `figure_pipeline.py` and
prints its returned paths; `generate_release_artifacts.py` serializes tested
report/manifest objects to `output/reports/`. Neither script may implement
validation or plotting logic, compute checksums inline, or hardcode dataset
values — every number must come from a tested `src/` function.

The source-owned figure pipeline mirrors the complete PNG set to
`output/figures/` and writes `figure_registry.json` from the data-bound
`DESCRIPTOR_FIGURE_SPECS`. It validates the full source set before copying, so a
missing renderer output cannot produce a partial registry. The project-local
publisher is byte-compatible with the monorepo registry and keeps standalone
clones self-contained.
