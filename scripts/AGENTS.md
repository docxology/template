# scripts/ - Generic Entry Point Orchestrators

## Purpose

The `scripts/` directory contains thin, generic orchestrators for the build pipeline. They coordinate stage execution and reporting, but they do not implement project-specific analysis, rendering, or validation logic.

## Current Entry Points

- `00_setup_environment.py` - environment and dependency validation
- `01_run_tests.py` - infrastructure and project test orchestration
- `02_run_analysis.py` - project-script discovery and execution
- `03_render_pdf.py` - manuscript rendering orchestration
- `04_validate_output.py` - output validation orchestration
- `05_copy_outputs.py` - output copying orchestration
- `06_llm_review.py` - LLM review and translation orchestration
- `07_generate_executive_report.py` - multi-project executive reporting
- `execute_pipeline.py` - single-project pipeline runner
- `execute_multi_project.py` - multi-project pipeline runner
- `audit_filepaths.py` - repository filepath audit
- `generate_active_projects_doc.py` - derived project inventory documentation
- `organize_executive_outputs.py` - executive output organizer
- `manage_workspace.py` - workspace helper
- `show_project_info.py` - project metadata helper (used by `run.sh` interactive menu)
- `verify_no_mocks.py` - mock-usage checker

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
| **2** Infrastructure Tests | `01_run_tests.py --infra-only --verbose` | `core`, `tests` | configurable tolerance |
| **3** Project Tests | `01_run_tests.py --project-only --verbose` | `core`, `tests` | configurable tolerance |
| **4** Project Analysis | `02_run_analysis.py` | `core` | hard fail |
| **5** PDF Rendering | `03_render_pdf.py` | `core` | hard fail |
| **6** Output Validation | `04_validate_output.py` | `core` | warning + report |
| **7** LLM Scientific Review | `06_llm_review.py --reviews-only` | `llm` | skipped if Ollama absent |
| **8** LLM Translations | `06_llm_review.py --translations-only` | `llm` | skipped if Ollama absent |
| **9** Copy Outputs | `05_copy_outputs.py` | `core` | soft fail |
<!-- END:STAGE_TABLE -->

`execute_pipeline.py` supports single-stage execution with stage keys such as `setup`, `tests`, `analysis`, `render_pdf`, `validate`, `copy`, `llm_reviews`, `llm_translations`, and `executive_report`.

## Public Types

### `PipelineStageDefinition`

```python
@dataclass
class PipelineStageDefinition:
    script: str
    requires_ollama: bool
    description: str
    note: Optional[str] = None
```

### `MENU_SCRIPT_MAPPING`

Typed mapping used by `scripts/__init__.py` to document the interactive menu-to-script relationship.

## Execution Details

- `run.sh` is the primary user entry point.
- `secure_run.sh` runs the pipeline and then steganographic PDF post-processing.
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
| `01_run_tests.py --project-only --all-projects` | `infrastructure.core.test_runner.run_per_project_pytest` | One pytest process per discovered project (avoids `tests/conftest.py` plugin-name collision), `--cov-append` accumulation, combined `coverage report --fail-under` gate. Mirrors the loop previously open-coded in `.github/workflows/ci.yml#test-project`. |
| `02_run_analysis.py` | `infrastructure.core.runtime._python_env.build_analysis_script_cmd_and_env` | |
| `03_render_pdf.py` | `infrastructure.rendering.pipeline` | |
| `04_validate_output.py` | `infrastructure.validation.cli` | |
| `05_copy_outputs.py` | `infrastructure.reporting.output_organizer` | |
| `06_llm_review.py` | `infrastructure.llm.review` | Skipped when Ollama is absent. |
| `07_generate_executive_report.py` | `infrastructure.reporting.executive_reporter` | |

## Testing Expectations

- Use real subprocess execution for shell entry points.
- Preserve the thin-orchestrator pattern.
- Keep module-specific logic in `infrastructure/` or `projects/{name}/src/`.

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../docs/RUN_GUIDE.md`](../docs/RUN_GUIDE.md)
