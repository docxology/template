# tests/integration/ - Integration Test Documentation

## Purpose

The `tests/integration/` directory contains repository-level integration tests that verify scripts, modules, and output handling work together correctly.

## Standards

- Use real execution paths.
- Avoid mocks and fake subprocesses.
- Prefer temporary directories and actual generated files.
- Keep shell tests and Python tests aligned with the live pipeline entry points.

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

## Notes

- `test_execute_pipeline_cli.py` covers the Python pipeline entry point.
- `test_run_sh.py` covers the shell wrapper.
- `test_full_pipeline.py` covers the end-to-end pipeline path.

## See Also

- [`README.md`](README.md)
- [`../../AGENTS.md`](../../AGENTS.md)
