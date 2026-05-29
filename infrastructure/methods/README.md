# Methods Orchestration

`infrastructure.methods` builds a deterministic methods orchestration plan for a
project. The plan connects the pipeline DAG, manuscript method sections
(discovered by filename token or by an in-body Methods/Methodology heading),
artifact manifests, evidence registries, and validation commands without moving
stage logic out of the existing pipeline.

Run:

```bash
uv run python -m infrastructure.methods plan --project template_code_project --format markdown
uv run python -m infrastructure.methods plan --project template_code_project --format json --check
```

The package is read-only. It reports missing methods/evidence surfaces; pipeline
execution still lives in `scripts/execute_pipeline.py` and stage scripts.
