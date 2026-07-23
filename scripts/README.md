# scripts/ - Quick Reference

Generic orchestrators for the research pipeline, organized by subpackage:

All repository-wide entry points live in the role-specific subpackages below.
There are no root-level duplicate entry points; use the canonical path shown in
each table and in the generated stage documentation.

| Subpackage | Role |
| --- | --- |
| [`pipeline/`](pipeline/) | Numbered stage scripts (`stage_00_setup.py` … `stage_12_metadata.py`) |
| [`runner/`](runner/) | Single- and multi-project pipeline execution |
| [`audit/`](audit/) | Documentation lint, drift, mock checks, tracked-resource guards |
| [`docgen/`](docgen/) | Regenerators for `docs/_generated/` |
| [`shell/`](shell/) | `run.sh` bootstrap, backup, local CI |
| [`publish/`](publish/) | Release and publishing helpers |
| [`gates/`](gates/) | Opt-in quality gates |
| [`maintenance/`](maintenance/) | Workspace and local maintenance tools |

## Entry Points

### Shell

```bash
./run.sh
./run.sh --pipeline --resume
./run.sh --all-projects --pipeline
./secure_run.sh --project template_code_project
```

### Python

```bash
uv run python scripts/runner/execute_pipeline.py --project template_code_project --core-only
uv run python scripts/runner/execute_multi_project.py --no-llm
uv run python scripts/pipeline/stage_07_executive_report.py
```

## Pipeline Stages

| Stage | Script | Responsibility |
| --- | --- | --- |
| 00 | `pipeline/stage_00_setup.py` | Validate Python, dependencies, build tools, and directories |
| 01 | `pipeline/stage_01_test.py` | Run infrastructure and project tests. Project pipelines use `--infra-scope pipeline-smoke` for a focused real infrastructure contract; explicit repo verification uses `--infra-scope full` for the coverage-bearing infrastructure suite. With `--project-only --all-projects`, delegates to `infrastructure.core.test_runner.run_per_project_pytest` (one pytest process per project, `--cov-append`, combined coverage gate for local all-project/release sweeps). |
| 02 | `pipeline/stage_02_analysis.py` | Discover and run `projects/{name}/scripts/` |
| 03 | `pipeline/stage_03_render.py` | Render manuscripts to PDF |
| 04 | `pipeline/stage_04_validate.py` | Validate PDFs, markdown, and integrity reports |
| 05 | `pipeline/stage_05_copy.py` | Copy final deliverables to `output/` |
| 06 | `pipeline/stage_06_llm_review.py` | Generate LLM reviews or translations when Ollama is available |
| 07 | `pipeline/stage_07_executive_report.py` | Build multi-project executive summaries and dashboards |

`runner/execute_pipeline.py` also supports single-stage execution with keys such as `setup`, `infra_tests`, `project_tests`, `analysis`, `render_pdf`, `validate`, `copy`, `llm_reviews`, `llm_translations`, and `executive_report`.

## Key Files

- `runner/execute_pipeline.py` / `runner/execute_multi_project.py` - single- and multi-project pipeline runners
- `docgen/active_projects.py` - regenerates `docs/_generated/active_projects.md`
- `docgen/api_reference.py` - regenerates the API reference (CI `validate --check`)
- `docgen/architecture_overview.py` - regenerates `docs/_generated/architecture_overview.{mmd,svg}`
- `docgen/coverage_history.py` - regenerates the coverage-history page from CI artefacts
- `docgen/stage_table.py` - regenerates the canonical stage-table marker block
- `docgen/exemplar_roster.py` - regenerates the public exemplar roster doc (`infrastructure.project.exemplar_roster`)
- `docgen/publication_records.py` - regenerates the publication-records doc (`infrastructure.documentation.publication_records`)
- `runner/repro_bundle.py` - builds/verifies reproduction bundles (`infrastructure.publishing.repro_bundle`)
- `audit/lint_docs.py` - runs Mermaid, link, consistency, and doc-pair documentation checks
- `audit/audit_documentation.py` - emits the advisory public documentation RedTeam audit
- `audit/verify_no_mocks.py` - lexical mock-framework gate; `--inventory` classifies semantic stand-ins
- `audit/audit_filepaths.py` - repository filepath and reference audit
- `audit/check_tracked_generated_artifacts.py` - rejects tracked generated outputs and package metadata
- `shell/ci_local.sh` - local CI reproduction (`act` when available, otherwise a pure-Python CI fallback; see [`../docs/maintenance/ci-local.md`](../docs/maintenance/ci-local.md))
- Maintenance helpers now live under [`maintenance/`](maintenance/) - `manage_workspace.py`, `show_project_info.py`, `render_working_projects.py`, `rerender_working_pdfs.py`, `organize_executive_outputs.py`, `merge_test_supplements.py`, `batch_cogsec_improve.py`, `setup_pre_commit.py`, `codegraph_local.py`, `refresh_artifact_manifests.py` (see [`maintenance/README.md`](maintenance/README.md) and [`maintenance/AGENTS.md`](maintenance/AGENTS.md)). `show_project_info.py` is a standalone project metadata CLI; it is **not** invoked by `run.sh` (the menu's `i` key prints only the current project name).
- `shell/bash_utils.sh` - shared shell helpers for backup/health scripts and integration tests (not sourced by `run.sh` / `secure_run.sh`)
- `shell/shell_bootstrap.sh` - shared `uv` bootstrap and sandbox env vars sourced by `run.sh` and `secure_run.sh`
- `shell/backup-daily.sh` / `shell/backup-weekly.sh` / `shell/backup-full.sh` - rsync backup tiers
- `shell/restore-test.sh` - non-destructive backup-restore verification
- `shell/health-check.sh` - pre-flight system health check (Python, uv, disk, Docker, repo)

## Quality gates (thin orchestrator)

| Gate | Command |
| --- | --- |
| Exemplar drift | `uv run python scripts/audit/check_template_drift.py --strict` |
| Documentation RedTeam audit | `uv run python scripts/audit/audit_documentation.py --format markdown` |
| Module line count | `uv run python scripts/gates/module_line_count_check.py` |
| Tracked projects guard | `uv run python scripts/audit/check_tracked_projects.py` |
| Tracked generated artifacts | `uv run python scripts/audit/check_tracked_generated_artifacts.py` |
| CodeGraph local scope | `codegraph files "$(pwd)" --json \| uv run python scripts/maintenance/codegraph_local.py verify-scope` |
| Unified health | `uv run python -m infrastructure.core.health` |
| Opt-in Stage 10 bundle | `uv run python scripts/runner/bundle_executable.py --project {name}` |
| Opt-in Stage 11 archival | `uv run python scripts/runner/archive_publication.py --project {name}` |

See [`docs/architecture/thin-orchestrator-summary.md`](../docs/architecture/thin-orchestrator-summary.md) and [`gates/AGENTS.md`](gates/AGENTS.md).

## Output Names

- `projects/{name}/output/reports/test_results.{json,md}`
- `projects/{name}/output/reports/validation_report.{json,md}`
- `projects/{name}/output/reports/log_summary.txt`
- `output/executive_summary/consolidated_report.{json,html,md}`
- `output/executive_summary/dashboard.{png,pdf,html}`

## Notes

- Project-specific analysis scripts belong in `projects/{name}/scripts/`.
- The subpackage scripts stay generic and work with any active project discovered from `projects/`.
- Use `uv run` for direct Python entry points (`runner/execute_pipeline.py`, `runner/execute_multi_project.py`, `pipeline/stage_07_executive_report.py`).
- `run.sh` and `secure_run.sh` are thin bootstrap shells: they source `shell/shell_bootstrap.sh`, then `exec uv run python -m infrastructure.orchestration` (menu, pipeline, and secure subcommands live in Python). Bare `./run.sh` relies on `uv run` to sync the workspace; pipeline-flag invocations also run `uv sync` when `.venv` is missing.

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
- [`../docs/RUN_GUIDE.md`](../docs/RUN_GUIDE.md)
