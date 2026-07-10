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

The public API is re-exported from `__init__.py`. Figure rendering and file I/O
belong in the thin scripts under `scripts/`, never here.
