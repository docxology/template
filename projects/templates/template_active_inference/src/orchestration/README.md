# Orchestration

- `analysis.py` — project-local analysis entry that runs the configured
  producers without importing the template infrastructure layer.
- `pipeline_manifest.py` — declares the analysis stages and their expected
  inputs/outputs so scripts, gates, and docs share one ordering contract.
- `coverage_pipeline.py` — refreshes sheaf coverage JSON, heatmap PNG, and the
  front-matter coverage page after compose or figure regeneration.
