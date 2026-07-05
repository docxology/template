# Reproducibility: Seeded Regeneration and Artifact Trace

Re-running generation with seed `431` and the same lexicon produces the same token plan. The artifact set records `token_inventory.json`, `section_plan.json`, `injection_trace.json`, `manuscript_variables.json`, `figure_registry.json`, and the cover/results/configuration/evaluation figure set so the manuscript can be audited without reading the PDF.

The protocol emits MadlibConfig, review scenario, explicit/default path inventory, validated lexicon, digest input records, selection invariant set, TokenPlan, enabled section set, section variables, Markdown evidence tables, claim-aligned evidence surface, registered figure set, output/data, output/reports, and output/figures, output/manuscript, validated project output, review packet, copied publication-review bundle, fork migration notes. Project tests cover deterministic token choice, seed sensitivity, category-input sensitivity, malformed config rejection, section disablement, artifact writing, and unresolved manuscript-token detection. The shared output validator then checks rendered PDFs, Markdown, figure registry, evidence registry, and design overlays.

The copied root output is therefore a consequence of local source and config. Generated files remain disposable; the durable contract is the ability to regenerate them from the tracked project tree and to observe the same validation gates passing.

- Config hash: `00cac9dbdea9aae6`
- Generated: `2026-07-05T23:54:56Z`
- Python: `3.12.13`
- Platform: `Darwin arm64`
