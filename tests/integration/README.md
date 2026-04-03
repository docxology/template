# tests/integration/ - Integration Test Suite

Integration tests validate the repository-level wiring between scripts, infrastructure modules, and output handling.

## Run

```bash
uv run pytest tests/integration/ -v
uv run pytest tests/integration/test_execute_pipeline_cli.py -v
uv run pytest tests/integration/test_run_sh.py -v
uv run pytest tests/integration/test_full_pipeline.py -v
```

## Current Files

- `conftest.py`
- `test_bash_utils.sh`
- `test_edge_cases_and_error_paths.py`
- `test_environment_setup.py`
- `test_execute_pipeline_cli.py`
- `test_executive_report_generation.py`
- `test_figure_equation_citation.py`
- `test_full_pipeline.py`
- `test_logging.py`
- `test_module_interoperability.py`
- `test_output_copying.py`
- `test_run_sh.py`

## Focus

- shell entry points
- pipeline orchestration
- output copying
- cross-module behavior
- end-to-end pipeline flow

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../../README.md`](../../README.md)
