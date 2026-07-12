# infrastructure/core/pipeline/ - Pipeline Helpers

Pipeline execution, summary, tracking, and multi-project orchestration helpers.

## Files

- `executor.py`
- `dag.py`
- `incremental.py` — opt-in content-hash stage skipping (default OFF)
- `multi_project.py`
- `multi_project_parallel.py`
- `resume.py`
- `stages.py`
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
- `single_stage.py` — `execute_single_stage()` subprocess runner
- `stage_vocabulary.py` — stage names from `pipeline.yaml`
- `pipeline.yaml` — default declared DAG definition consumed by the executor
- `artifacts.py` — stage-provenance manifests plus an explicit, deterministic
  current-output integrity snapshot for targeted renders

After intentionally regenerating outputs outside `PipelineExecutor`, refresh
their integrity baseline without inventing stage provenance:

```bash
uv run python scripts/maintenance/refresh_artifact_manifests.py \
  --project templates/template_code_project
```

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
