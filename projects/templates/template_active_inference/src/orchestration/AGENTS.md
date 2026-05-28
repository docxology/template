# Orchestration Notes

The manifest is the contract between scripts and outputs. Keep it in sync with
`../../scripts/` and the gate artifact manifest in `../gates/artifact_manifest.py`;
a stage that declares an output must actually produce it.

**Sheaf coverage artifact order (canonical):** `compose_all_sections` →
`emit_coverage_artifacts` (JSON only). `generate_all_figures` →
`ensure_coverage_artifacts` (JSON if stale, heatmap PNG, coverage page) then
`FIGURE_GENERATORS` dispatch. Prefer `ensure_coverage_artifacts` when adding new
entry points; use `run_coverage_pipeline(..., force=True)` for explicit full refresh.
