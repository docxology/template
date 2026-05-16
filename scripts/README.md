# scripts/ - Quick Reference

Root-level scripts are generic orchestrators for the research pipeline. They coordinate setup, tests, analysis, rendering, validation, copying, LLM review, and executive reporting without implementing project-specific business logic.

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
uv run python scripts/execute_pipeline.py --project template_code_project --core-only
uv run python scripts/execute_multi_project.py --no-llm
uv run python scripts/07_generate_executive_report.py
```

## Pipeline Stages

| Stage | Script | Responsibility |
| --- | --- | --- |
| 00 | `00_setup_environment.py` | Validate Python, dependencies, build tools, and directories |
| 01 | `01_run_tests.py` | Run infrastructure and project tests with coverage gates. With `--project-only --all-projects`, delegates to `infrastructure.core.test_runner.run_per_project_pytest` (one pytest process per project, `--cov-append`, combined coverage gate — used by CI). |
| 02 | `02_run_analysis.py` | Discover and run `projects/{name}/scripts/` |
| 03 | `03_render_pdf.py` | Render manuscripts to PDF |
| 04 | `04_validate_output.py` | Validate PDFs, markdown, and integrity reports |
| 05 | `05_copy_outputs.py` | Copy final deliverables to `output/` |
| 06 | `06_llm_review.py` | Generate LLM reviews or translations when Ollama is available |
| 07 | `07_generate_executive_report.py` | Build multi-project executive summaries and dashboards |

`execute_pipeline.py` also supports single-stage execution with keys such as `setup`, `tests`, `analysis`, `render_pdf`, `validate`, `copy`, `llm_reviews`, `llm_translations`, and `executive_report`.

## Key Files

- `execute_pipeline.py` / `execute_multi_project.py` - single- and multi-project pipeline runners
- `generate_active_projects_doc.py` - regenerates `docs/_generated/active_projects.md`
- `generate_api_reference_doc.py` - regenerates the API reference (CI `validate --check`)
- `generate_architecture_overview.py` - regenerates `docs/_generated/architecture_overview.{mmd,svg}`
- `generate_coverage_history.py` - regenerates the coverage-history page from CI artefacts
- `generate_stage_table_doc.py` - regenerates the canonical stage-table marker block
- `lint_docs.py` - runs Mermaid, link, consistency, and doc-pair documentation checks
- `verify_no_mocks.py` - checks tests for mock usage
- `audit_filepaths.py` - repository filepath and reference audit
- `check_tracked_generated_artifacts.py` - rejects tracked generated outputs and package metadata
- `setup_pre_commit.py` - installs and validates pre-commit hooks
- `manage_workspace.py` - workspace management helper
- `show_project_info.py` - project metadata helper (used by `run.sh` interactive menu)
- `organize_executive_outputs.py` - reorganizes executive report outputs by file type
- `batch_cogsec_improve.py` - thin orchestrator applying mechanical source improvements
- `bash_utils.sh` - shared shell helpers used by `run.sh` and `secure_run.sh`
- `backup-daily.sh` / `backup-weekly.sh` / `backup-full.sh` - rsync backup tiers
- `restore-test.sh` - non-destructive backup-restore verification
- `health-check.sh` - pre-flight system health check (Python, uv, disk, Docker, repo)

## Output Names

- `projects/{name}/output/reports/pipeline_report.{json,html,md}`
- `projects/{name}/output/reports/test_results.{json,md}`
- `projects/{name}/output/reports/validation_report.{json,md}`
- `projects/{name}/output/reports/log_summary.txt`
- `output/executive_summary/consolidated_report.{json,html,md}`
- `output/executive_summary/dashboard.{png,pdf,html}`

## Notes

- Project-specific analysis scripts belong in `projects/{name}/scripts/`.
- The root scripts stay generic and work with any active project discovered from `projects/`.
- Use `uv run` for direct Python entry points (`execute_pipeline.py`, `execute_multi_project.py`, `07_generate_executive_report.py`).
- `run.sh` and `secure_run.sh` resolve Python through the `get_python_cmd` helper in `bash_utils.sh`, which prefers the uv-managed `.venv/bin/python` and falls back to `python3`. This is equivalent to `uv run python` for the commands these shells issue; no separate `uv run` wrapping is required inside `run.sh`.

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
- [`../docs/RUN_GUIDE.md`](../docs/RUN_GUIDE.md)
