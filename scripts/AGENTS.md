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
- `generate_pipeline_reports.py` - pipeline report helper
- `generate_test_summary.py` - test summary helper
- `organize_executive_outputs.py` - executive output organizer
- `manage_workspace.py` - workspace helper
- `show_project_info.py` - project metadata helper
- `verify_no_mocks.py` - mock-usage checker

## Stage Mapping

| Stage | Script | Notes |
| --- | --- | --- |
| 00 | `00_setup_environment.py` | Validates Python, dependencies, tools, and directories |
| 01 | `01_run_tests.py` | Runs infra and project tests with coverage gates |
| 02 | `02_run_analysis.py` | Discovers `projects/{name}/scripts/` and executes them |
| 03 | `03_render_pdf.py` | Renders markdown manuscripts to PDF |
| 04 | `04_validate_output.py` | Validates PDFs, markdown, and integrity reports |
| 05 | `05_copy_outputs.py` | Copies final deliverables into `output/` |
| 06 | `06_llm_review.py` | Runs LLM review or translation when Ollama is available |
| 07 | `07_generate_executive_report.py` | Generates cross-project reports and dashboards |

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
- `execute_multi_project.py` uses `MultiProjectOrchestrator` from `infrastructure.core.pipeline.multi_project`.
- Reports are written under `projects/{name}/output/reports/` and `output/executive_summary/`.

## Testing Expectations

- Use real subprocess execution for shell entry points.
- Preserve the thin-orchestrator pattern.
- Keep module-specific logic in `infrastructure/` or `projects/{name}/src/`.

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../docs/RUN_GUIDE.md`](../docs/RUN_GUIDE.md)
