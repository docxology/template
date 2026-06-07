# infrastructure/core/pipeline/ - Pipeline Helper Documentation

## Purpose

The `infrastructure/core/pipeline/` package contains the executor, DAG, summary, and multi-project orchestration helpers used by the pipeline entry points.

## Files

- `executor.py` - pipeline execution (thin `_execute_stage` delegates to `_stage_execution`); acquires `project_output_lock` for the resolved project directory for the full run
- `_stage_execution.py` - stage orchestration: HITL pauses, pre/post hooks, retries, telemetry (`execute_stage`, `handle_post_stage_success`, `handle_stage_failure`, `handle_stage_exception`)
- `dag.py` - stage dependency graph helpers
- `incremental.py` - **opt-in** content-hash stage skipping (INCREMENTAL-PIPELINE-1). DEFAULT-OFF via `PipelineConfig.incremental` (`IncrementalConfig(enabled=False)`). When enabled, hashes a stage's declared `input_artifacts` (file content) and skips a stage only when the recorded input hash matches AND all declared outputs exist; otherwise runs and re-records. Manifest at `output/.pipeline/incremental.json`. Downstream invalidation flows through declared-input file content (a downstream stage consumes the upstream's output file). Fail-safe: never skips when an output is absent or no outputs are declared. With the feature disabled the executor never reads/writes the manifest and behavior is byte-identical to before.
- `multi_project.py` - multi-project orchestration (serial)
- `multi_project_parallel.py` - bounded-parallel multi-project orchestration
- `multi_project_cli.py` - CLI for `scripts/execute_multi_project.py` (serial + `--parallel`)
  via `concurrent.futures.ProcessPoolExecutor`. Public entry point:
  `run_projects_in_parallel(...) -> ParallelRunResult`. Worker count defaults
  to `min(N_projects, os.cpu_count() or 1)` and is overridable by the
  `MULTI_PROJECT_MAX_WORKERS` environment variable or by passing
  `max_workers=N` explicitly. Each worker redirects FD 1/2 to its
  per-project `projects/<name>/output/logs/pipeline.log` so the parent
  never sees interleaved output.
- `resume.py` - checkpoint resume helpers
- `stages.py` - stage definitions
- `stage_monitor.py` - stage resource monitoring
- `_stage_tracker.py` - tracking internals
- `_performance_monitor.py` - performance internals
- `_monitor_types.py` - shared monitoring types
- `post_run_reporting.py` - post-run JSON/HTML/Markdown report generation
- `hitl_cli.py` - non-interactive HITL CLI (`PipelineArgs`, `handle_hitl_command`)
- `stage_registry.py` - canonical stage-key → script map (`STAGE_DISPATCH`, `MENU_KEY_TO_STAGE`)
- `single_stage.py` - subprocess single-stage runner; consumes `stage_registry.script_argv_for_stage()`
- `stage_vocabulary.py` - canonical stage names/aliases from `pipeline.yaml` (shared with menu banners and eval grader)
- `summary_formatters.py` - summary formatting
- `summary_helpers.py` - summary helpers
- `summary_models.py` - summary dataclasses
- `types.py` - shared pipeline types

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
