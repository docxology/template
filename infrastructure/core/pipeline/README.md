# infrastructure/core/pipeline/ - Pipeline Helpers

Pipeline execution, summary, tracking, and multi-project orchestration helpers.

## Files

- `executor.py`
- `dag.py`
- `incremental.py` — opt-in content-hash stage skipping (default OFF)
- `multi_project.py`
- `multi_project_parallel.py`
- `resume.py`
- `stages.py` — subprocess execution through the 7,200-second descendant-tree-killing boundary; it does not duplicate the YAML stage plan
- `stage_monitor.py`
- `_stage_tracker.py`
- `_performance_monitor.py`
- `_monitor_types.py`
- `summary.py`
- `summary_formatters.py`
- `summary_helpers.py`
- `summary_models.py`
- `types.py`
- `stage_registry.py` — `STAGE_DISPATCH`, `MENU_KEY_TO_STAGE` (single source for `--stage` and menu keys)
- `single_stage.py` — `execute_single_stage()` subprocess runner using the same bounded deadline as the full pipeline
- `stage_vocabulary.py` — stage names from `pipeline.yaml`
- `pipeline.yaml` — default declared DAG definition consumed by the executor
- `artifacts.py` — stage-provenance manifests plus an explicit, deterministic
  current-output integrity snapshot for targeted renders. Snapshots exclude
  control reports, provider-controlled `output/fulltext/` caches, and transient
  TeX/log files; they attest stable derived outputs rather than local caches.
  `collect_stable_output_inventory()` is the shared read-only source for these
  manifests and provenance-bound output statistics. Public exemplars use
  fail-closed Git-shippable filtering; explicitly resolved non-template
  lifecycle projects may use stable-local mode without claiming Git
  shippability. Manifests persist the selected mode, validators compare it with
  the lifecycle-authorized mode, and legacy manifests without the field retain
  the strict Git-shippable interpretation. Manifest readers share an exact schema
  parser (canonical POSIX `output/...` paths, complete typed fields, lowercase
  SHA-256 values), and validation rejects duplicates, omitted stable artifacts,
  or entries outside the lifecycle-authorized inventory. Both modes exclude
  every hidden path component and retain fail-closed symlink diagnostics. It
  uses NUL-safe Git path
  transport; unavailable, failed, or malformed Git-ignore evaluation blocks a
  detected worktree, while genuine non-repository trees retain static fallback.
  It can map an ignored root delivery mirror back to its canonical
  project-output paths, preserving source-scoped ignore decisions without
  erasing the copied publication tree. The supported lazy package API exports
  `StableOutputInventory`, `OutputInventoryMode`, both mode constants, the
  collector, and `output_inventory_mode_for_project`; shippable mode is always
  the collector default.

`pipeline.yaml` is the only full-pipeline stage plan. Temporary repositories
and installed wheels resolve the packaged copy of that same file; there is no
hard-coded Python fallback plan. Root numbered scripts and
`scripts/runner/execute_pipeline.py` are compatibility wrappers over the canonical
`scripts/pipeline/` and `scripts/runner/` implementations.

After intentionally regenerating outputs outside `PipelineExecutor`, refresh
their integrity baseline without inventing stage provenance:

```bash
uv run python scripts/maintenance/refresh_artifact_manifests.py \
  --project templates/template_code_project
```

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
