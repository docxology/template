# scripts/ - Generic Entry Point Orchestrators

## Purpose

The `scripts/` directory contains thin, generic orchestrators for the build pipeline.
Business logic lives in `infrastructure/` or `projects/{name}/src/`. Scripts are
grouped by role under subpackages; root-level filenames remain as backward-compatible
shims where noted in each subpackage's `AGENTS.md`.

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

**Root-level modules and compatibility shims** (canonical location noted where the file has moved under a subpackage):

- `generate_active_projects_doc.py` - root-level entry point for `docs/_generated/active_projects.md`; delegates to `infrastructure.documentation.active_projects_doc.write_active_projects_doc` (canonical: `docgen/active_projects.py`)
- `generate_architecture_overview.py` - regenerates `docs/_generated/architecture_overview.{mmd,svg}` via `infrastructure.documentation.architecture_overview.render_architecture_svg` (canonical: `docgen/architecture_overview.py`)
- `generate_counts.py` - writes/checks `docs/_generated/COUNTS.md` via `infrastructure.documentation.counts_doc` (`--write` / `--check`; canonical: `docgen/counts.py`)
- `generate_coverage_history.py` - builds `docs/_generated/coverage_history.md` from CI coverage XML via `infrastructure.reporting.coverage_history` (`--from-dir` / `--from-gh`; canonical: `docgen/coverage_history.py`)
- `10_research_workflow.py` - deprecated shim that warns and delegates to `pipeline/stage_10_research_workflow.py`
- `mcp_server_template.py` - thin launcher for the stdio MCP server (equivalent to `python -m infrastructure.mcp_server`); opt-in agent surface, not part of the default pipeline/CI
- `exit_codes.py` - `ExitCode` IntEnum naming the shared orchestrator exit-code contract (`SUCCESS=0`, `FAILURE=1`, `SKIP=2`, `VALIDATION_FAILED=3`, `MISSING_DEPENDENCY=4`); importing changes no return value

**Quality gates / audits** (`audit/`):

- `audit/lint_docs.py`, `audit/audit_documentation.py`, `audit/verify_no_mocks.py`
- `audit/audit_filepaths.py`, `audit/check_template_drift.py`
- `audit/check_tracked_*` guards, `audit/copy_exemplar.py`
- `gates/module_line_count_check.py` - line-count gate via `infrastructure.validation.line_count`

**Publishing** — `publish/publish_project_release.py` (opt-in unified release)

**Local CI (shell)** — `shell/ci_local.sh`, `shell/shell_bootstrap.sh`, `shell/bash_utils.sh`

> **Unified health command** — every quality gate listed below (mypy,
> ruff, ruff-format, bandit, `verify_no_mocks.py`,
> `infrastructure.skills check-all-exports`, `lint_docs.py`,
> `generate_stage_table_doc.py`, `generate_api_reference_doc.py --check`,
> architecture-overview) can be invoked together via
> `uv run python -m infrastructure.core.health`. The module lives in
> `infrastructure/core/health.py`; this directory remains the
> per-gate entry point. Add `--json` to feed CI artefacts.

## Stage Mapping

The canonical pipeline-stage table (rendered from
[`infrastructure/core/pipeline/pipeline.yaml`](../infrastructure/core/pipeline/pipeline.yaml)
by `scripts/docgen/stage_table.py`):

<!-- BEGIN:STAGE_TABLE -->
<!-- This block is generated from [`infrastructure/core/pipeline/pipeline.yaml`](../infrastructure/core/pipeline/pipeline.yaml) by `scripts/docgen/stage_table.py`. Do not hand-edit. Stage indices are **0-based positions in the YAML** and intentionally do **not** match the `scripts/NN_*.py` numeric prefixes (for example, stage 9 runs `05_copy_outputs.py`). -->

| Stage | Script | Tags | Failure mode |
| ----- | ------ | ---- | ------------ |
| **0** Clean Output Directories | built-in `_run_clean_outputs` | `core`, `clean` | soft fail |
| **1** Environment Setup | `00_setup_environment.py` | `core` | hard fail |
| **2** Infrastructure Tests | `01_run_tests.py --infra-only --verbose --infra-scope pipeline-smoke` | `core`, `tests` | configurable tolerance |
| **3** Project Tests | `01_run_tests.py --project-only --verbose` | `core`, `tests` | configurable tolerance |
| **4** Project Analysis | `02_run_analysis.py` | `core` | hard fail |
| **5** Connector Search | `08_connector_search.py` | `science` | skipped if not configured |
| **6** Provenance Record | `09_provenance_record.py --stage Connector Search` | `provenance` | skipped if not configured |
| **7** PDF Rendering | `03_render_pdf.py` | `core` | hard fail |
| **8** Output Validation | `04_validate_output.py` | `core` | warning + report |
| **9** LLM Scientific Review | `06_llm_review.py --reviews-only` | `llm` | skipped if Ollama absent |
| **10** LLM Translations | `06_llm_review.py --translations-only` | `llm` | skipped if Ollama absent |
| **11** Copy Outputs | `05_copy_outputs.py` | `core` | soft fail |
| **12** Ebook Generation | `11_ebook_generation.py` | `core`, `ebook` | soft fail |
| **13** Metadata Package | `12_metadata_package.py` | `core`, `metadata` | soft fail |
| **14** Executable Bundle | `08_executable_bundle.py` | `bundle` | soft fail |
| **15** Archival Publication | `09_archive_publication.py` | `archival` | soft fail |
<!-- END:STAGE_TABLE -->

`runner/execute_pipeline.py` supports single-stage execution with stage keys such as `setup`, `tests`, `analysis`, `render_pdf`, `validate`, `copy`, `llm_reviews`, `llm_translations`, `executive_report`, `ebook_generation`, and `metadata_package`.

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
- `execute_pipeline.py` uses `PipelineExecutor` from `infrastructure.core.pipeline`.
- `execute_multi_project.py` uses `MultiProjectOrchestrator` from
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
| `01_run_tests.py` | `infrastructure.reporting.pipeline_test_runner.execute_test_pipeline` | Default path: infra-then-project for one selected project. |
| `01_run_tests.py --project-only --all-projects` | `infrastructure.core.test_runner.run_per_project_pytest` | One pytest process per discovered project (avoids `tests/conftest.py` plugin-name collision), `--cov-append` accumulation, combined union `coverage report --fail-under=75` (`DEFAULT_FAIL_UNDER`). Add `--public-projects` for the public release/all-project lane; it restricts the loop to `infrastructure.project.public_scope`, so local rotating symlinks do not affect public-repo validation. CI `test-project` instead runs one isolated matrix job per public exemplar. **`./run.sh --all-projects --pipeline`** still runs the **per-project 90%** gate inside each project's own pytest invocation; the **75% union** gate applies only via this orchestrator path. |
| `02_run_analysis.py` | `infrastructure.core.runtime._python_env.build_analysis_script_cmd_and_env` | |
| `03_render_pdf.py` | `infrastructure.rendering.pipeline` | |
| `04_validate_output.py` | `infrastructure.validation.cli` | |
| `05_copy_outputs.py` | `infrastructure.reporting.output_organizer` | |
| `06_llm_review.py` | `infrastructure.llm.review` | Skipped when Ollama is absent. |
|| `07_generate_executive_report.py` | `infrastructure.reporting.multi_project_reporter.generate_multi_project_report`, `infrastructure.reporting.output_organizer.OutputOrganizer.copy_combined_pdfs` | Multi-project only; skips when one project discovered. |
|| `11_ebook_generation.py` | `infrastructure.rendering.ebook_stage.run_ebook_generation` | Opt-in ebook stage; gracefully skips (exit 2) when combined markdown absent. |
|| `12_metadata_package.py` | `infrastructure.publishing.metadata_stage.run_metadata_package` | Opt-in metadata stage; gracefully skips (exit 2) when config.yaml absent. |
| `maintenance/render_working_projects.py` | `infrastructure.project.working_render` | Local WIP audit under `projects/working/`; not part of default pipeline. |
| `maintenance/rerender_working_pdfs.py` | subprocess over the `03_render_pdf.py` / `05_copy_outputs.py` stages (+ `infrastructure.project.working_render`) | Local-only working-PDF re-render; not part of default pipeline. |
| `maintenance/merge_test_supplements.py` | `infrastructure.validation.test_supplements.merge_supplements` | Local maintenance helper. |
| `10_repro_bundle.py` | `infrastructure.publishing.repro_bundle` | Opt-in reproduction-bundle build/verify. |
| `generate_exemplar_roster_doc.py` | `infrastructure.project.exemplar_roster` | Derived public exemplar roster doc. |
| `generate_publication_records_doc.py` | `infrastructure.documentation.publication_records.write_publication_records_doc` | Derived publication-records doc. |
| `lint_docs.py` | `infrastructure.validation.docs.lint_runner` | |
| `execute_pipeline.py` (post-run) | `infrastructure.core.pipeline.post_run_reporting` | |
| `00_setup_environment.py` | `infrastructure.core.runtime.environment`, `setup_checks`, `env_deps` | |
| `maintenance/show_project_info.py` | `infrastructure.project.info.collect_project_info` | Standalone CLI; not invoked by `run.sh` (the menu's `i` key prints only the current project name). |
| `check_tracked_projects.py` | `infrastructure.project.git_guards.offending_tracked_projects` | |
| `check_tracked_fonds.py` | `infrastructure.project.git_guards.offending_tracked_fonds` | |
| `check_tracked_rules.py` | `infrastructure.project.git_guards.offending_tracked_rules` | |
| `check_tracked_tools.py` | `infrastructure.project.git_guards.offending_tracked_tools` | |
| `check_tracked_all.py` | all four `offending_tracked_*` guards | CI lint + pre-push |
| `check_tracked_generated_artifacts.py` | `infrastructure.project.git_guards.tracked_generated_artifacts` | |
| `maintenance/codegraph_local.py` | `infrastructure.project.codegraph` | Optional local-only index helper; never a pipeline dependency |
| `maintenance/refresh_artifact_manifests.py` | `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest` | Explicit current-output integrity rebaseline after targeted renders; not stage provenance |
| `08_executable_bundle.py` | `infrastructure.publishing.executable_bundle.bundle_project` | |
| `check_template_drift.py` | `infrastructure.project.drift` (+ thin-orchestrator script checks) | |
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
