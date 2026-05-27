# Orchestration Notes

The manifest is the contract between scripts and outputs. Keep it in sync with
`../../scripts/` and `../../autoresearch`-style expected artifacts; a stage that
declares an output must actually produce it.

**Sheaf coverage artifact order (canonical):** `emit_coverage_artifacts` (JSON) →
`run_coverage_figures_and_page` (heatmap PNG + coverage page). `run_coverage_pipeline`
wraps both. `compose_all_sections` and `generate_all_figures` call this sequence at
their boundaries; prefer `run_coverage_pipeline` when adding new entry points.
