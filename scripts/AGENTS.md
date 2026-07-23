# scripts/ - Generic Entry Point Orchestrators

## Purpose

The `scripts/` directory contains thin, generic orchestrators for the build pipeline.
Business logic lives in `infrastructure/` or `projects/{name}/src/`. Scripts are
grouped by role under subpackages. The subpackage path is the only supported
repository-wide entrypoint; root-level duplicate launchers are intentionally absent.

## Subpackage layout

| Subpackage | AGENTS | Role |
| --- | --- | --- |
| [`pipeline/`](pipeline/AGENTS.md) | stage orchestrators (`stage_00_setup.py` … `stage_12_metadata.py`) |
| [`runner/`](runner/AGENTS.md) | `execute_pipeline.py`, `execute_multi_project.py`, `run_matrix.py`, bundle/archive/repro runners |
| [`audit/`](audit/AGENTS.md) | docs lint, drift, mock checks, tracked-resource guards |
| [`docgen/`](docgen/AGENTS.md) | `docs/_generated/` regenerators |
| [`shell/`](shell/AGENTS.md) | `run.sh` bootstrap, backup, local CI |
| [`publish/`](publish/AGENTS.md) | release and publishing helpers |
| [`gates/`](gates/AGENTS.md) | opt-in quality gates |
| [`maintenance/`](maintenance/AGENTS.md) | workspace and local maintenance |

## Current Entry Points (canonical paths)

**Pipeline stages** — prefer `scripts/pipeline/stage_*.py`:

- `pipeline/stage_00_setup.py` - environment and dependency validation
- `pipeline/stage_01_test.py` - infrastructure and project test orchestration
- `pipeline/stage_02_analysis.py` - project-script discovery and execution
- `pipeline/stage_03_render.py` - manuscript rendering orchestration
- `pipeline/stage_04_validate.py` - output validation orchestration
- `pipeline/stage_05_copy.py` - output copying orchestration
- `pipeline/stage_06_llm_review.py` - LLM review and translation orchestration
- `pipeline/stage_07_executive_report.py` - multi-project executive reporting
- `pipeline/stage_08_connector_search.py` - opt-in connector search
- `pipeline/stage_09_provenance_record.py` - opt-in provenance recording
- `pipeline/stage_10_research_workflow.py` - opt-in research workflow
- `pipeline/stage_11_ebook.py` - ebook generation (opt-in `ebook` tag)
- `pipeline/stage_12_metadata.py` - metadata package (opt-in `metadata` tag)

**Runners:**

- `runner/execute_pipeline.py` - single-project pipeline runner
- `runner/execute_multi_project.py` - multi-project pipeline runner (serial; `--parallel` for process-pool)
- `runner/run_matrix.py` - reproducible project × stage matrix runner
- `runner/bundle_executable.py` - executable bundle stage (opt-in `bundle` tag)
- `runner/archive_publication.py` - multi-target archival stage (opt-in `archival` tag)
- `runner/repro_bundle.py` - reproduction-bundle build/verify

**Derived-doc generators** (`docgen/`):

- `docgen/active_projects.py`, `docgen/api_reference.py`, `docgen/architecture_overview.py`
- `docgen/coverage_history.py`, `docgen/stage_table.py`, `docgen/exemplar_roster.py`
- `docgen/publication_records.py`, `docgen/counts.py`

**Repository-wide entrypoint rule:** use only the canonical paths under
`pipeline/`, `runner/`, `audit/`, `docgen/`, `publish/`, `shell/`, and `gates/`.
The old root-level numbered, generated-document, audit, shell, and runner
launchers have been removed so documentation and execution cannot drift between
two names for the same operation.

**Quality gates / audits** (`audit/`):

- `audit/lint_docs.py`, `audit/audit_documentation.py`, `audit/verify_no_mocks.py`
- `audit/audit_filepaths.py`, `audit/check_template_drift.py`
- `audit/check_tracked_*` guards, `audit/copy_exemplar.py`
- `gates/module_line_count_check.py` - line-count gate via `infrastructure.validation.line_count`

**Publishing** — `publish/publish_project_release.py` (opt-in unified release)

**Local CI (shell)** — `shell/ci_local.sh`, `shell/shell_bootstrap.sh`, `shell/bash_utils.sh`

> **Unified health command** — every quality gate listed below (mypy,
> ruff, ruff-format, bandit, `audit/verify_no_mocks.py`,
> `infrastructure.skills check-all-exports`, `audit/lint_docs.py`,
> `docgen/stage_table.py`, `docgen/api_reference.py --check`,
> architecture-overview) can be invoked together via
> `uv run python -m infrastructure.core.health`. The module lives in
> `infrastructure/core/health.py`; this directory remains the
> per-gate entry point. Independent gates run with bounded concurrency by
> default; use `--workers 1` for serial diagnostics and `--json` for CI
> artefacts.

## Stage Mapping

The canonical pipeline-stage table (rendered from
[`infrastructure/core/pipeline/pipeline.yaml`](../infrastructure/core/pipeline/pipeline.yaml)
by `scripts/docgen/stage_table.py`):

<!-- BEGIN:STAGE_TABLE -->
<!-- This block is generated from [`infrastructure/core/pipeline/pipeline.yaml`](../infrastructure/core/pipeline/pipeline.yaml) by `scripts/docgen/stage_table.py`. Do not hand-edit. Stage indices are **0-based positions in the YAML** and intentionally do **not** match the `scripts/pipeline/stage_NN_*.py` numeric prefixes (for example, stage 11, "Copy Outputs", runs `scripts/pipeline/stage_05_copy.py`). -->

| Stage | Script | Tags | Failure mode |
| ----- | ------ | ---- | ------------ |
| **0** Clean Output Directories | built-in `_run_clean_outputs` | `core`, `clean` | soft fail |
| **1** Environment Setup | `scripts/pipeline/stage_00_setup.py` | `core` | hard fail |
| **2** Infrastructure Tests | `scripts/pipeline/stage_01_test.py --infra-only --verbose --infra-scope pipeline-smoke` | `core`, `tests` | configurable tolerance |
| **3** Project Tests | `scripts/pipeline/stage_01_test.py --project-only --verbose` | `core`, `tests` | configurable tolerance |
| **4** Project Analysis | `scripts/pipeline/stage_02_analysis.py` | `core` | hard fail |
| **5** Connector Search | `scripts/pipeline/stage_08_connector_search.py` | `science` | skipped if not configured |
| **6** Provenance Record | `scripts/pipeline/stage_09_provenance_record.py --stage Connector Search` | `provenance` | skipped if not configured |
| **7** PDF Rendering | `scripts/pipeline/stage_03_render.py` | `core` | hard fail |
| **8** Output Validation | `scripts/pipeline/stage_04_validate.py` | `core` | warning + report |
| **9** LLM Scientific Review | `scripts/pipeline/stage_06_llm_review.py --reviews-only` | `llm` | skipped if Ollama absent |
| **10** LLM Translations | `scripts/pipeline/stage_06_llm_review.py --translations-only` | `llm` | skipped if Ollama absent |
| **11** Copy Outputs | `scripts/pipeline/stage_05_copy.py` | `core` | soft fail |
| **12** Ebook Generation | `scripts/pipeline/stage_11_ebook.py` | `core`, `ebook` | soft fail |
| **13** Metadata Package | `scripts/pipeline/stage_12_metadata.py` | `core`, `metadata` | soft fail |
| **14** Executable Bundle | `scripts/runner/bundle_executable.py` | `bundle` | soft fail |
| **15** Archival Publication | `scripts/runner/archive_publication.py` | `archival` | soft fail |
<!-- END:STAGE_TABLE -->

`runner/execute_pipeline.py` supports single-stage execution with stage keys such as `setup`, `infra_tests`, `project_tests`, `analysis`, `render_pdf`, `validate`, `copy`, `llm_reviews`, `llm_translations`, `executive_report`, `ebook_generation`, and `metadata_package`.

## Public Types

`scripts/__init__.py` exports only `ensure_repo_root_on_path()` — the idempotent
helper each script calls to put the repo root on `sys.path` (the repo sets
`[tool.uv] package = false`, so it is never installed into the venv). The former
`PipelineStageDefinition` / `MENU_SCRIPT_MAPPING` types were removed: they had no
functional consumers and had drifted from the live interactive menu, whose single
source of truth is `infrastructure.orchestration.menu.MENU_OPTIONS`.

## Execution Details

- `run.sh` is the primary user entry point.
- `secure_run.sh` runs the same pipeline DAG via Python (`PipelineRunner`), then steganographic PDF post-processing (`run_secure_pipeline`).
- `runner/execute_pipeline.py` uses `PipelineExecutor` from `infrastructure.core.pipeline`.
- `runner/execute_multi_project.py` uses `MultiProjectOrchestrator` from
  `infrastructure.core.pipeline.multi_project` for the default serial path.
  When invoked with `--parallel` (optionally `--max-workers=N`), it delegates
  to `infrastructure.core.pipeline.multi_project_parallel.run_projects_in_parallel`,
  which spawns one worker process per project via `ProcessPoolExecutor`.
  Worker count defaults to `min(N_projects, os.cpu_count() or 1)` and is
  overridable by the `MULTI_PROJECT_MAX_WORKERS` environment variable. The
  serial path remains the default.
- Reports are written under `projects/{name}/output/reports/` and `output/executive_summary/`.

## Module Delegation

Every script delegates to a sibling module so that `scripts/` stays a thin
orchestrator:

| Script invocation | Delegates to | Notes |
| --- | --- | --- |
| `pipeline/stage_01_test.py` | `infrastructure.reporting.pipeline_test_runner.execute_test_pipeline` | Default path: infra-then-project for one selected project. |
| `pipeline/stage_01_test.py --project-only --all-projects` | `infrastructure.core.test_runner.run_per_project_pytest` | One pytest process and isolated coverage datafile per discovered project (avoids `tests/conftest.py` plugin-name collision and parent coverage contamination), followed by a combined union `coverage report --fail-under=75` (`DEFAULT_FAIL_UNDER`). Add `--public-projects` for the public release/all-project lane; it restricts the loop to `infrastructure.project.public_scope`, so local rotating symlinks do not affect public-repo validation. CI `test-project` instead runs one isolated matrix job per public exemplar. **`./run.sh --all-projects --pipeline`** still runs the **per-project 90%** gate inside each project's own pytest invocation; the **75% union** gate applies only via this orchestrator path. |
| `pipeline/stage_02_analysis.py` | `infrastructure.core.runtime._python_env.build_analysis_script_cmd_and_env` | |
| `pipeline/stage_03_render.py` | `infrastructure.rendering.pipeline` | |
| `pipeline/stage_04_validate.py` | `infrastructure.validation.cli` | |
| `pipeline/stage_05_copy.py` | `infrastructure.reporting.output_organizer` | |
| `pipeline/stage_06_llm_review.py` | `infrastructure.llm.review` | Skipped when Ollama is absent. |
| `pipeline/stage_07_executive_report.py` | `infrastructure.reporting.multi_project_reporter.generate_multi_project_report`, `infrastructure.reporting.output_organizer.OutputOrganizer.copy_combined_pdfs` | Multi-project only; skips when one project discovered. |
| `pipeline/stage_11_ebook.py` | `infrastructure.rendering.ebook_stage.run_ebook_generation` | Opt-in ebook stage; gracefully skips (exit 2) when combined markdown absent. |
| `pipeline/stage_12_metadata.py` | `infrastructure.publishing.metadata_stage.run_metadata_package` | Opt-in metadata stage; gracefully skips (exit 2) when config.yaml absent. |
| `maintenance/render_working_projects.py` | `infrastructure.project.working_render` | Local WIP audit under `projects/working/`; not part of default pipeline. |
| `maintenance/rerender_working_pdfs.py` | subprocess over the `pipeline/stage_03_render.py` / `pipeline/stage_05_copy.py` stages (+ `infrastructure.project.working_render`) | Local-only working-PDF re-render; not part of default pipeline. |
| `maintenance/merge_test_supplements.py` | `infrastructure.validation.test_supplements.merge_supplements` | Local maintenance helper. |
| `runner/repro_bundle.py` | `infrastructure.publishing.repro_bundle` | Opt-in reproduction-bundle build/verify. |
| `docgen/exemplar_roster.py` | `infrastructure.project.exemplar_roster` | Derived public exemplar roster doc. |
| `docgen/publication_records.py` | `infrastructure.documentation.publication_records.write_publication_records_doc` | Derived publication-records doc. |
| `audit/lint_docs.py` | `infrastructure.validation.docs.lint_runner` | |
| `runner/execute_pipeline.py` (post-run) | `infrastructure.core.pipeline.post_run_reporting` | |
| `maintenance/show_project_info.py` | `infrastructure.project.info.collect_project_info` | Standalone CLI; not invoked by `run.sh` (the menu's `i` key prints only the current project name). |
| `audit/check_tracked_projects.py` | `infrastructure.project.git_guards.offending_tracked_projects` | |
| `audit/check_tracked_fonds.py` | `infrastructure.project.git_guards.offending_tracked_fonds` | |
| `audit/check_tracked_rules.py` | `infrastructure.project.git_guards.offending_tracked_rules` | |
| `audit/check_tracked_tools.py` | `infrastructure.project.git_guards.offending_tracked_tools` | |
| `audit/check_tracked_all.py` | all four `offending_tracked_*` guards | CI lint + pre-push |
| `audit/check_tracked_generated_artifacts.py` | `infrastructure.project.git_guards.tracked_generated_artifacts` | |
| `maintenance/codegraph_local.py` | `infrastructure.project.codegraph` | Optional local-only index helper; never a pipeline dependency |
| `maintenance/refresh_artifact_manifests.py` | `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest` | Explicit current-output integrity rebaseline after targeted renders; not stage provenance |
| `runner/bundle_executable.py` | `infrastructure.publishing.executable_bundle.bundle_project` | |
| `audit/check_template_drift.py` | `infrastructure.project.drift` (+ thin-orchestrator script checks) | |
| `maintenance/manage_workspace.py` | `infrastructure.project.workspace` | |
| `maintenance/batch_cogsec_improve.py` | `infrastructure.core.source_improve` | |
| `execute_pipeline.py` (HITL / single-stage) | `infrastructure.core.pipeline.hitl_cli`, `single_stage` | Post-run → `post_run_reporting` |
| `execute_multi_project.py` | `infrastructure.core.pipeline.multi_project_cli` | Serial + `--parallel` paths |
| `scripts/gates/module_line_count_check.py` | `infrastructure.validation.line_count` | |
| `scripts/gates/security_scan.py` | `infrastructure.validation.security_gate` | Opt-in |
| `scripts/gates/plugin_export_check.py` | `infrastructure.validation.plugin_export` | Opt-in |
| `scripts/gates/gate_cache.py` | `infrastructure.core.cache_gate` | Opt-in |
| `scripts/publish/*` | see [`publish/AGENTS.md`](publish/AGENTS.md) | |
| `scripts/fixtures/*` | see [`fixtures/AGENTS.md`](fixtures/AGENTS.md) | |

## Testing Expectations

- Use real subprocess execution for shell entry points.
- Preserve the thin-orchestrator pattern.
- Keep module-specific logic in `infrastructure/` or `projects/{name}/src/`.

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../docs/RUN_GUIDE.md`](../docs/RUN_GUIDE.md)
