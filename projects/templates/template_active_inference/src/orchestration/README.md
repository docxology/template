# Orchestration

- `analysis.py` — project-local analysis entry that runs the configured
  producers without importing the template infrastructure layer.
- `pipeline_manifest.py` — declares the analysis stages and their expected
  inputs/outputs so scripts, gates, and docs share one ordering contract.
- `coverage_pipeline.py` — refreshes sheaf coverage JSON, heatmap PNG, and the
  front-matter coverage page after compose or figure regeneration.
- `full_verification.py` — ordered producer/gate refresh plus chunked cumulative
  coverage; when invoked by the generic Stage-01 adapter it emits one fresh,
  run-bound receipt from the final coverage groups and settled postflight state.
  Those groups use the adapter's pinned interpreter and emit hardened-XML JUnit
  outcomes plus pytest sidecars with real warning and discovery counts.
- `portable_execution.py` — standalone credential-redacted subprocess boundary;
  timeouts terminate the entire descendant tree, including nested sessions.
