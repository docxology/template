# infrastructure/core/pipeline/ - Pipeline Helper Documentation

## Purpose

The `infrastructure/core/pipeline/` package contains the executor, DAG, summary, and multi-project orchestration helpers used by the pipeline entry points.

## Files

- `executor.py` - pipeline execution (thin `_execute_stage` delegates to `_stage_execution`); acquires `project_output_lock` for the resolved project directory for the full run
- `_stage_execution.py` - stage orchestration: HITL pauses, pre/post hooks, retries, telemetry (`execute_stage`, `handle_post_stage_success`, `handle_stage_failure`, `handle_stage_exception`)
- `dag.py` - stage dependency graph helpers; `opt_in_tags` / `load_opt_in_tags` / `opt_in_tags_from_mapping` are the YAML-owned default-run exclude set
- `definition.py` - `resolve_pipeline_source`, `PipelineSource`, `PipelinePurpose`, `PipelineSourceOrigin` — deterministic YAML lookup (explicit path, project `pipeline.yaml` / `methods_pipeline.yaml`, repository DAG, package data)
- `incremental.py` - **opt-in** content-hash stage skipping (INCREMENTAL-PIPELINE-1). DEFAULT-OFF via `PipelineConfig.incremental` (`IncrementalConfig(enabled=False)`). When enabled, hashes a stage's declared `input_artifacts` (file content) and skips a stage only when the recorded input hash matches AND all declared outputs exist; otherwise runs and re-records. Manifest at `output/.pipeline/incremental.json`. Downstream invalidation flows through declared-input file content (a downstream stage consumes the upstream's output file). Fail-safe: never skips when an output is absent or no outputs are declared. With the feature disabled the executor never reads/writes the manifest and behavior is byte-identical to before.
- `plugins.py` - **opt-in** schema-validated plugin stages (PLUGIN-STAGES-1). DEFAULT-OFF: no `projects/{name}/pipeline_plugins.yaml` → no plugin stages merged. Declarations validated via :func:`load_plugin_stages` / :func:`merge_plugin_stages`; malformed entries raise :class:`PluginStageError`. Executor lazy-imports this module only when a project declares plugins. Tests: `tests/infra_tests/core/pipeline/test_plugins.py`.
- `multi_project.py` - multi-project orchestration (serial)
- `multi_project_parallel.py` - bounded-parallel multi-project orchestration
- `multi_project_cli.py` - CLI for `scripts/runner/execute_multi_project.py` (serial + `--parallel`)
  through fresh subprocess workers. Public entry point:
  `run_projects_in_parallel(...) -> ParallelRunResult`. Worker count defaults
  to `min(N_projects, os.cpu_count() or 1)` and is overridable by the
  `MULTI_PROJECT_MAX_WORKERS` environment variable or by passing
  `max_workers=N` explicitly. The parent freezes every effective project plan
  before shared verification, executes the shared gate once, and transports
  each exact plan to a new worker with a private bytecode prefix and a pre-import
  audit of actual executed public code. Queueing,
  locks, stages, and reporting share `--run-timeout` (default 14,400 seconds).
  Timeout and interruption clean descendant processes and retain their typed
  outcomes. Finite cleanup may outlast an expired work deadline; it cannot
  grant success. Worker stdout/stderr is drained into an 8 MiB capped spool
  and overflow fails the worker. Each project's captured log stays under its
  own `output/logs/`. `multi_project_summary.py` supervises aggregate rendering
  within the remaining deadline and publishes runtime reports only beneath
  ignored `output/multi_project_summary/`. Original expected stage selections
  and matching typed stage rows determine aggregate completion.
  A positively identified guardian custody refusal is blocked (75); cleanup
  still reaps the child, drains its capped output, and retains actual child and
  stage evidence. Ordinary child/setup failures remain failed.
- `resume.py` - checkpoint resume helpers
- `stages.py` - subprocess execution and public multi-project test helpers; script stages use a 7,200-second descendant-tree-killing boundary, and stage definitions live only in `pipeline.yaml`
- `stage_monitor.py` - stage resource monitoring
- `_stage_tracker.py` - tracking internals
- `_performance_monitor.py` - performance internals
- `_monitor_types.py` - shared monitoring types
- `post_run_reporting.py` - post-run JSON/HTML/Markdown report generation
- `hitl_cli.py` - non-interactive HITL CLI (`PipelineArgs`, `handle_hitl_command`)
- `stage_registry.py` - menu keys and canonical declared stage keys (`MENU_KEY_TO_STAGE`, `known_stage_keys`)
- `single_stage.py` - compiles a targeted immutable plan and delegates to the same executor and deadline as complete pipeline execution
- `stage_vocabulary.py` - canonical stage names/aliases from `pipeline.yaml` (shared with menu banners and eval grader). `core_stage_names()` excludes opt-in and live stages; `live_stage_names()` includes explicitly enabled live stages; `default_run_stage_count(mode=...)` is the menu/CLI count helper.
- `summary_formatters.py` - summary formatting
- `summary_helpers.py` - summary helpers
- `summary_models.py` - summary dataclasses
- `types.py` - shared pipeline types
- `artifacts/` — advisory per-stage artifact manifests package ([`artifacts/AGENTS.md`](artifacts/AGENTS.md)); public import path unchanged. Exports include `declared_output_paths`, `compute_sha256`, `write_stage_artifact_manifest`, `aggregate_artifact_manifests`, `snapshot_current_artifact_manifest`, `validate_artifact_manifest`; dataclasses `ArtifactManifestEntry`, `ArtifactManifest`, `ArtifactValidationReport`. `collect_stable_output_inventory()` and `StableOutputInventory` are the one read-only inventory contract shared by manifests and statistics; supported lazy exports also include `OutputInventoryMode`, both mode constants, and `output_inventory_mode_for_project`. Public exemplars default to fail-closed `stable-shippable-output-v1`; only explicitly resolved non-template lifecycle projects may receive `stable-local-output-v1`, so ignore-policy drift cannot silently weaken a public gate. Each manifest persists the selected mode; legacy payloads default to strict shippable mode, and current validation rejects a mode/lifecycle mismatch. Manifest JSON uses one strict parser across aggregation, validation, Methods, and AutoResearch: entries require canonical POSIX `output/...` paths, exact booleans/non-negative integers, complete stage fields, and lowercase SHA-256 values; duplicates, omissions, and entries outside the selected stable inventory are invalid. Local mode bypasses only a whole-output packaging rule when Git can identify it and still honors selective ignores. Both modes reject hidden path components, runtime/control/build residue, and symlinks while retaining the explicit `output/fulltext/fulltext_inventory.json` evidence exception. Git path exchange is NUL-safe for Unicode/newline names; Git-query failures block inventory inside detected worktrees while genuine non-repository trees retain the documented static fallback. Copied root mirrors map relative paths to the canonical project output for ignore evaluation. The explicit snapshot labels entries `current-output-snapshot`, omits wall-clock timestamps unless `SOURCE_DATE_EPOCH` is set, and must not be described as stage provenance.
- `control.py` - advisory pipeline control config parsing/merging with precedence default YAML → project YAML → CLI HITL mode (`load_pipeline_control_config`, `merge_control_configs`, `control_config_from_dict`)
- `run_matrix.py` - reproducible project × stage run matrix from a `run.config` YAML file; canonically orders steps so a given config reproduces byte-for-byte (`parse_run_config`, `resolve_run_plan`, `execute_run_plan`, `find_run_config`, `format_report`)
- `smart_pause.py` - advisory SmartPause recommendation scoring from run reports (report-first; the default pipeline does not pause) (`compute_pause_recommendations`, `write_pause_recommendations`, `PauseRecommendation`)
- `snapshot.py` - pipeline output snapshots and comparison reports (`create_snapshot`, `compare_snapshots`, `write_snapshot_comparison`, `snapshot_compare_to_markdown`, `main`)

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)

## Release acceptance modules

| Module | Role |
| --- | --- |
| `artifact_contracts.py` | Executable artifact prerequisites and immutable consumed-input custody. |
| `execution_custody.py` | Revalidate the frozen execution identity at launch, reuse, and completion. |
| `execution_environment.py` | Digest the effective child environment without recording its values. |
| `execution_records.py` | Source-bound execution records shared by every executor entry point. |
| `execution_session.py` | Whole-run deadline and lock composition for every resolved-plan executor. |
| `fingerprint_files.py` | Held-directory filesystem observations for content fingerprints. |
| `fingerprints.py` | Content identities for source trees and stable deliverables. |
| `hitl_context.py` | Public artifact context for a bound human review. |
| `hitl_responses.py` | Typed validation of responses bound to a specific paused execution. |
| `hitl_storage.py` | Confined, serialized mutations of human decision state. |
| `multi_project_summary_worker.py` | Generate a typed aggregate summary only within its private scratch boundary. |
| `multi_project_support.py` | Shared verification and aggregate completion for project orchestrators. |
| `multi_project_worker.py` | Fresh-bytecode worker consuming the parent's exact immutable execution plan. |
| `native_analysis_current.py` | Fresh Current execution through the existing complete native core controller. |
| `native_stage_launch.py` | Use the single fixed audited child for an already-owned native stage. |
| `observability.py` | Pipeline logging, telemetry initialization, and advisory reports. |
| `plan_custody.py` | Freeze declaration bytes and source identity before any plan policy parsing. |
| `plan_serialization.py` | Strict transport decoding for immutable resolved execution plans. |
| `report_finalization.py` | Supervised final reports within the executor's finite run deadline. |
| `report_worker.py` | Fresh-bytecode worker for source-bound pipeline report generation. |
| `runtime_namespace.py` | Admit the canonical isolated storage role before shared execution begins. |
| `skip_receipts.py` | Fresh, parent-bound reasons for an explicitly skippable child stage. |
| `stage_admission.py` | Original input and human review bindings transported to actual stage attempts. |
| `stage_launch.py` | Fresh Python stage supervision and source-bound original exit receipts. |
| `stage_worker.py` | Execute a declared Python stage with fresh caches and checked source custody. |
| `target_contracts.py` | Canonical executable capabilities that declarations cannot weaken. |
