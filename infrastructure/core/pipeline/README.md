# infrastructure/core/pipeline/ - Pipeline Helpers

Pipeline execution, summary, tracking, and multi-project orchestration helpers.

## Files

- `executor.py`
- `dag.py`
- `definition.py` — resolve `pipeline.yaml` for execution vs methods (`resolve_pipeline_source`)
- `incremental.py` — opt-in content-hash stage skipping (default OFF)
- `tool_bindings.py` — filesystem-only identities for effective executable selections and known launcher backends
- `multi_project.py`
- `multi_project_parallel.py`
- `multi_project_runtime.py` — frozen parent plans, finite queueing, isolated fresh workers, and descendant cleanup
- `multi_project_output.py` — continuous stdout/stderr draining with an 8 MiB spool cap
- `multi_project_summary.py` — supervised aggregate reporting within the remaining run budget
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
- `stage_registry.py` — `MENU_KEY_TO_STAGE` and `known_stage_keys`
- `single_stage.py` — `execute_single_stage()` subprocess runner using the same bounded deadline as the full pipeline
- `stage_vocabulary.py` — stage names from `pipeline.yaml`; `core_stage_names`, `live_stage_names`, and `default_run_stage_count(mode=...)` follow YAML `opt_in_tags`
- `pipeline.yaml` — default declared DAG plus `opt_in_tags` (the executor exclude set)
- `artifacts/` — stage-provenance manifests package ([`artifacts/AGENTS.md`](artifacts/AGENTS.md)); public import path unchanged (`infrastructure.core.pipeline.artifacts`). Snapshots exclude
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
hard-coded Python fallback plan. Entry scripts delegate to the canonical `ExecutionPlan` compiler and executor;
full, targeted, and matrix execution retain their explicit stage selection.

Serial and parallel multi-project runs freeze all effective plans before the
once-only shared infrastructure gate. Each project starts a fresh worker and
private bytecode cache with a pre-import executed-code audit; its original stage selection, matching typed outcomes,
and exact project set determine completion. `--run-timeout` bounds the entire
run, including queueing, locks, and aggregate reports. Interrupted or timed out
workers have their descendants cleaned; bounded cleanup cannot turn a late run
into success. Worker log overflow fails rather than growing its spool beyond
8 MiB. Aggregate reports live in ignored `output/multi_project_summary/`.
Shared verification retains its exact `infra_tests` selection, stage rows, and
typed outcomes in the public result and summary. An infrastructure child exit
2 remains visible beside aggregate exit 1; contradictory shared claims fail.

Project and public Source identities exclude `lean/.lake` only when a physical
`lean/lakefile.lean` declares that Lake root. The same classification is shared
by pipeline, project, and Root fingerprints. Lean implementation files,
`lake-manifest.json`, and `lean-toolchain` remain Source; unrelated nested
`.lake` directories remain authored inputs. Git ignore or forced tracking does
not change this boundary, and symbolic declaration/ancestor paths are refused.

Cache and resume identities include the stage's effective `FORMAL_JAVA_BIN`,
`PANDOC_PATH`, and `LATEX_COMPILER` selections, declared Lean/Lake pins, and
installed elan backend bytes. Fingerprinting reads bounded regular files and
does not invoke tools or acquire toolchains. A known missing backend changes
identity when installed. An unresolved launcher prevents cache reuse and blocks
resume with exit 75 while preserving the checkpoint; fresh execution remains
available. On macOS, nominate the actual absolute `JAVA_HOME` when selecting
`/usr/bin/java`, including through `FORMAL_JAVA_BIN`, to bind its runtime rather
than only the system launcher.

After intentionally regenerating outputs outside `PipelineExecutor`, refresh
their integrity baseline without inventing stage provenance:

```bash
uv run python scripts/maintenance/refresh_artifact_manifests.py \
  --project templates/template_code_project
```

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
