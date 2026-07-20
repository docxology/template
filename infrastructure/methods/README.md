# Methods Orchestration

`infrastructure.methods` builds deterministic single-project and aggregate
methods audit plans. Each plan connects the selected pipeline DAG, manuscript method sections
(discovered by filename token or by an in-body Methods/Methodology heading),
artifact manifests, evidence registries, and validation commands without moving
stage logic out of the existing pipeline.

Run:

```bash
uv run python -m infrastructure.methods plan --project templates/template_code_project --format markdown
uv run python -m infrastructure.methods plan --all-public --artifact-mode source --format json
uv run python -m infrastructure.methods plan --all-public --artifact-mode rendered --format json
```

`--project` and `--all-public` are mutually exclusive. Rendered validation is
the default; source mode validates authoring contracts without requiring built
evidence. Exit codes are `0` for clean/warnings, `1` for validation errors, and
`2` for invalid invocation or configuration. The historical `--check` flag is
retained but no longer changes those standardized codes.

The package is read-only. It reports missing methods/evidence surfaces; pipeline
execution still lives in `scripts/runner/execute_pipeline.py` and stage scripts.
