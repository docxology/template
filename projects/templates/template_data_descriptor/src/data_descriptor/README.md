# data_descriptor package

Reusable, tested logic for FAIR-style dataset descriptors. All business logic
lives here; scripts and manuscript prose consume this package rather than
duplicating rules. Modules:

- `descriptor.py` — schema validation, field-constraint summaries, order-independent
  schema fingerprints, readiness scoring, and the metadata-only release manifest.
- `verification.py` — byte-level checks: recompute each declared file's sha256
  digest and row count and reconcile them against the descriptor
  (`verify_descriptor_files`, `compute_file_digest`, `count_csv_rows`,
  `verification_summary`).
- `figures.py` — plot-ready data preparers with no matplotlib dependency
  (`schema_table_rows`, `file_inventory_rows`, `provenance_steps`,
  `severity_counts`, `demo_broken_descriptor`).
- `figure_pipeline.py` — lazy-headless rendering and source-bound publication
  (`load_descriptor_figure_inputs`, `render_descriptor_figures`,
  `publish_descriptor_figure_run`, `generate_descriptor_figure_assets`).
- `registry.py` — deterministic fail-closed figure mirroring and registry
  persistence for monorepo and standalone runs.

The public API is re-exported from `__init__.py`. Matplotlib is imported lazily
inside the explicit render API after the headless backend is selected; merely
importing descriptor validators has no rendering side effect. Scripts under
`scripts/` remain entry points and never reconstruct plot or registry logic.
