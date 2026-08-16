# infrastructure/core/pipeline/ - Pipeline Helper Documentation

## Purpose

The `infrastructure/core/pipeline/` package contains the executor, DAG, summary, and multi-project orchestration helpers used by the pipeline entry points.

## Files

- `executor.py` - pipeline execution (thin `_execute_stage` delegates to `_stage_execution`); acquires `project_output_lock` for the resolved project directory for the full run
- `_stage_execution.py` - stage orchestration: HITL pauses, pre/post hooks, retries, telemetry (`execute_stage`, `handle_post_stage_success`, `handle_stage_failure`, `handle_stage_exception`)
- `dag.py` - stage dependency graph helpers
- `incremental.py` - **opt-in** content-hash stage skipping (INCREMENTAL-PIPELINE-1). DEFAULT-OFF via `PipelineConfig.incremental` (`IncrementalConfig(enabled=False)`). When enabled, hashes a stage's declared `input_artifacts` (file content) and skips a stage only when the recorded input hash matches AND all declared outputs exist; otherwise runs and re-records. Manifest at `output/.pipeline/incremental.json`. Downstream invalidation flows through declared-input file content (a downstream stage consumes the upstream's output file). Fail-safe: never skips when an output is absent or no outputs are declared. With the feature disabled the executor never reads/writes the manifest and behavior is byte-identical to before.
- `plugins.py` - **opt-in** schema-validated plugin stages (PLUGIN-STAGES-1). DEFAULT-OFF: no `projects/{name}/pipeline_plugins.yaml` → no plugin stages merged. Declarations validated via :func:`load_plugin_stages` / :func:`merge_plugin_stages`; malformed entries raise :class:`PluginStageError`. Executor lazy-imports this module only when a project declares plugins. Tests: `tests/infra_tests/core/pipeline/test_plugins.py`.
- `multi_project.py` - multi-project orchestration (serial)
- `multi_project_parallel.py` - bounded-parallel multi-project orchestration
- `multi_project_cli.py` - CLI for `scripts/runner/execute_multi_project.py` (serial + `--parallel`)
  via `concurrent.futures.ProcessPoolExecutor`. Public entry point:
  `run_projects_in_parallel(...) -> ParallelRunResult`. Worker count defaults
  to `min(N_projects, os.cpu_count() or 1)` and is overridable by the
  `MULTI_PROJECT_MAX_WORKERS` environment variable or by passing
  `max_workers=N` explicitly. Each worker redirects FD 1/2 to its
  per-project `projects/<name>/output/logs/pipeline.log` so the parent
  never sees interleaved output.
- `resume.py` - checkpoint resume helpers
- `stages.py` - subprocess execution and public multi-project test helpers; script stages use a 7,200-second descendant-tree-killing boundary, and stage definitions live only in `pipeline.yaml`
- `stage_monitor.py` - stage resource monitoring
- `_stage_tracker.py` - tracking internals
- `_performance_monitor.py` - performance internals
- `_monitor_types.py` - shared monitoring types
- `post_run_reporting.py` - post-run JSON/HTML/Markdown report generation
- `hitl_cli.py` - non-interactive HITL CLI (`PipelineArgs`, `handle_hitl_command`)
- `stage_registry.py` - canonical stage-key → script map (`STAGE_DISPATCH`, `MENU_KEY_TO_STAGE`)
- `single_stage.py` - subprocess single-stage runner; consumes `stage_registry.script_argv_for_stage()` and shares the full pipeline's 7,200-second descendant-tree-killing boundary
- `stage_vocabulary.py` - canonical stage names/aliases from `pipeline.yaml` (shared with menu banners and eval grader)
- `summary_formatters.py` - summary formatting
- `summary_helpers.py` - summary helpers
- `summary_models.py` - summary dataclasses
- `types.py` - shared pipeline types
- `artifacts.py` - advisory per-stage artifact manifests with content-hash provenance (`compute_sha256`, `write_stage_artifact_manifest`, `aggregate_artifact_manifests`, `snapshot_current_artifact_manifest`, `validate_artifact_manifest`; dataclasses `ArtifactManifestEntry`, `ArtifactManifest`, `ArtifactValidationReport`). `collect_stable_output_inventory()` and `StableOutputInventory` are the one read-only inventory contract shared by manifests and statistics; supported lazy exports also include `OutputInventoryMode`, both mode constants, and `output_inventory_mode_for_project`. Public exemplars default to fail-closed `stable-shippable-output-v1`; only explicitly resolved non-template lifecycle projects may receive `stable-local-output-v1`, so ignore-policy drift cannot silently weaken a public gate. Each manifest persists the selected mode; legacy payloads default to strict shippable mode, and current validation rejects a mode/lifecycle mismatch. Manifest JSON uses one strict parser across aggregation, validation, Methods, and AutoResearch: entries require canonical POSIX `output/...` paths, exact booleans/non-negative integers, complete stage fields, and lowercase SHA-256 values; duplicates, omissions, and entries outside the selected stable inventory are invalid. Local mode bypasses only a whole-output packaging rule when Git can identify it and still honors selective ignores. Both modes reject hidden path components, runtime/control/build residue, and symlinks while retaining the explicit `output/fulltext/fulltext_inventory.json` evidence exception. Git path exchange is NUL-safe for Unicode/newline names; Git-query failures block inventory inside detected worktrees while genuine non-repository trees retain the documented static fallback. Copied root mirrors map relative paths to the canonical project output for ignore evaluation. The explicit snapshot labels entries `current-output-snapshot`, omits wall-clock timestamps unless `SOURCE_DATE_EPOCH` is set, and must not be described as stage provenance.
- `control.py` - advisory pipeline control config parsing/merging with precedence default YAML → project YAML → CLI HITL mode (`load_pipeline_control_config`, `merge_control_configs`, `control_config_from_dict`)
- `run_matrix.py` - reproducible project × stage run matrix from a `run.config` YAML file; canonically orders steps so a given config reproduces byte-for-byte (`parse_run_config`, `resolve_run_plan`, `execute_run_plan`, `find_run_config`, `format_report`)
- `smart_pause.py` - advisory SmartPause recommendation scoring from run reports (report-first; the default pipeline does not pause) (`compute_pause_recommendations`, `write_pause_recommendations`, `PauseRecommendation`)
- `snapshot.py` - pipeline output snapshots and comparison reports (`create_snapshot`, `compare_snapshots`, `write_snapshot_comparison`, `snapshot_compare_to_markdown`, `main`)

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
