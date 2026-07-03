# scripts/ - Generic Entry Point Orchestrators

## Purpose

The `scripts/` directory contains thin, generic orchestrators for the build pipeline. They coordinate stage execution and reporting, but they do not implement project-specific analysis, rendering, or validation logic.

## Current Entry Points

**Pipeline orchestrators (numbered stages + runners):**

- `00_setup_environment.py` - environment and dependency validation
- `01_run_tests.py` - infrastructure and project test orchestration
- `02_run_analysis.py` - project-script discovery and execution
- `03_render_pdf.py` - manuscript rendering orchestration
- `04_validate_output.py` - output validation orchestration
- `05_copy_outputs.py` - output copying orchestration
- `06_llm_review.py` - LLM review and translation orchestration
- `07_generate_executive_report.py` - multi-project executive reporting
- `11_ebook_generation.py` - ebook generation orchestration (EPUB, MOBI, DOCX; opt-in `ebook` tag)
- `12_metadata_package.py` - metadata package generation (ONIX XML, metadata.json, OPF; opt-in `metadata` tag)
- `10_repro_bundle.py` - reproduction-bundle build/verify (`infrastructure.publishing.repro_bundle`)
- `execute_pipeline.py` - single-project pipeline runner
- `execute_multi_project.py` - multi-project pipeline runner (serial; `--parallel` for process-pool)
- `run_matrix.py` - reproducible project × stage matrix runner (`infrastructure.core.pipeline.run_matrix`); reads `run.config`, resolves projects + orders stages canonically, runs each via `execute_single_stage`. Deterministic alternative to the interactive menu.

**Derived-doc generators (write `docs/_generated/` and in-place doc blocks):**

- `generate_active_projects_doc.py` - derived active-project inventory
- `generate_api_reference_doc.py` - API reference from `__all__` (CI `validate --check`)
- `generate_architecture_overview.py` - architecture `.mmd`/`.svg` from live state
- `generate_coverage_history.py` - coverage-history page from CI artefacts
- `generate_stage_table_doc.py` - canonical pipeline stage table (marker block)
- `generate_exemplar_roster_doc.py` - public exemplar roster doc (`infrastructure.project.exemplar_roster`)
- `generate_publication_records_doc.py` - publication-records doc (`infrastructure.documentation.publication_records`)

**Quality gates / audits:**

- `lint_docs.py` - thin CLI over `infrastructure.validation.docs.lint_runner.run_docs_lint`
- `audit_documentation.py` - advisory RedTeam documentation audit over public docs and def/class surfaces
- `verify_no_mocks.py` - mock-usage checker
- `audit_filepaths.py` - repository filepath audit
- `check_tracked_generated_artifacts.py` - git-index hygiene guard for generated outputs (untracked helper; exercised by `tests/infra_tests/git_hook_smoke/`)
- `check_template_drift.py` - thin CLI over `infrastructure.project.drift` for exemplar doc/code drift
- `gates/module_line_count_check.py` - line-count gate via `infrastructure.validation.line_count` (infra/scripts + `projects/*/scripts/`)
- `check_tracked_projects.py` - confidentiality guard via `infrastructure.project.git_guards`
- `08_executable_bundle.py` - bundle stage via `infrastructure.publishing.executable_bundle`
- `09_archive_publication.py` - multi-target archival stage via `infrastructure.publishing.archival`
- `publish_project_release.py` - unified GitHub + Zenodo release via `infrastructure.publishing.release_workflow` (opt-in)

**Maintenance helpers (now under [`maintenance/`](maintenance/) — see [`maintenance/AGENTS.md`](maintenance/AGENTS.md)):**

- `maintenance/setup_pre_commit.py` - install and validate pre-commit hooks
- `maintenance/manage_workspace.py` - workspace helper (status, per-project deps)
- `maintenance/show_project_info.py` - standalone project metadata CLI; **not** invoked by `run.sh` (the menu's `i` key prints only the current project name)
- `maintenance/organize_executive_outputs.py` - executive output organizer
- `maintenance/batch_cogsec_improve.py` - thin orchestrator applying mechanical source improvements
- `maintenance/render_working_projects.py` - batch core pipeline for `projects/working/` WIP trees
- `maintenance/rerender_working_pdfs.py` - re-render working-project PDFs via subprocess over the 03/05 render/copy stages
- `maintenance/merge_test_supplements.py` - merge supplementary test results (`infrastructure.validation.test_supplements`)
- `maintenance/codegraph_local.py` - optional local CodeGraph command/scope helper via `infrastructure.project.codegraph`

**Local CI (shell):**

- `ci_local.sh` - local CI reproduction (`act` when available, otherwise a pure-Python CI fallback; see [`../docs/maintenance/ci-local.md`](../docs/maintenance/ci-local.md))

**Backup / operations (shell):**

- `backup-daily.sh`, `backup-weekly.sh`, `backup-full.sh` - rsync backup tiers
- `restore-test.sh` - non-destructive backup-restore verification
- `health-check.sh` - pre-flight system health check (Python, uv, disk, Docker, repo)
- `shell_bootstrap.sh` - shared `uv` bootstrap and sandbox env vars sourced by `run.sh` / `secure_run.sh`
- `bash_utils.sh` - shared shell helpers for backup/health scripts and integration tests (not sourced by root entry points)

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
by `scripts/generate_stage_table_doc.py`):

<!-- BEGIN:STAGE_TABLE -->
<!-- This block is generated from [`infrastructure/core/pipeline/pipeline.yaml`](../infrastructure/core/pipeline/pipeline.yaml) by `scripts/generate_stage_table_doc.py`. Do not hand-edit. Stage indices are **0-based positions in the YAML** and intentionally do **not** match the `scripts/NN_*.py` numeric prefixes (for example, stage 9 runs `05_copy_outputs.py`). -->

| Stage | Script | Tags | Failure mode |
| ----- | ------ | ---- | ------------ |
| **0** Clean Output Directories | built-in `_run_clean_outputs` | `core`, `clean` | soft fail |
| **1** Environment Setup | `00_setup_environment.py` | `core` | hard fail |
| **2** Infrastructure Tests | `01_run_tests.py --infra-only --verbose --infra-scope pipeline-smoke` | `core`, `tests` | configurable tolerance |
| **3** Project Tests | `01_run_tests.py --project-only --verbose` | `core`, `tests` | configurable tolerance |
| **4** Project Analysis | `02_run_analysis.py` | `core` | hard fail |
| **5** PDF Rendering | `03_render_pdf.py` | `core` | hard fail |
| **6** Output Validation | `04_validate_output.py` | `core` | warning + report |
| **7** LLM Scientific Review | `06_llm_review.py --reviews-only` | `llm` | skipped if Ollama absent |
| **8** LLM Translations | `06_llm_review.py --translations-only` | `llm` | skipped if Ollama absent |
| **9** Copy Outputs | `05_copy_outputs.py` | `core` | soft fail |
| **10** Ebook Generation | `11_ebook_generation.py` | `core`, `ebook` | soft fail |
| **11** Metadata Package | `12_metadata_package.py` | `core`, `metadata` | soft fail |
| **12** Executable Bundle | `08_executable_bundle.py` | `bundle` | soft fail |
| **13** Archival Publication | `09_archive_publication.py` | `archival` | soft fail |
<!-- END:STAGE_TABLE -->

`execute_pipeline.py` supports single-stage execution with stage keys such as `setup`, `tests`, `analysis`, `render_pdf`, `validate`, `copy`, `llm_reviews`, `llm_translations`, `executive_report`, `ebook_generation`, and `metadata_package`.

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
| `check_tracked_generated_artifacts.py` | `infrastructure.project.git_guards.tracked_generated_artifacts` | |
| `maintenance/codegraph_local.py` | `infrastructure.project.codegraph` | Optional local-only index helper; never a pipeline dependency |
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
