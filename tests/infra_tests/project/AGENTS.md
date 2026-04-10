# tests/infra_tests/project/ — Tests for `infrastructure.project`

## Purpose

Tests for `infrastructure.project.discovery` (`discover_projects`, project metadata loading) and `infrastructure.project.validation` (`validate_project_structure`). All tests follow the No-Mocks Policy: real `tmp_path` directories with real files instead of mocks.

## Files

- `test_discovery.py` — exhaustive coverage of `discover_projects()`: nested project layouts, qualified-name handling, the `src/` + `tests/` runnable filter, manuscript-only projects, archived/in-progress filtering, edge cases (~47 KB)
- `test_validation.py` — `validate_project_structure()` happy paths and failure modes (missing dir, missing `src/`, missing `tests/`, no Python files in `src/`)

## Running

```bash
uv run pytest tests/infra_tests/project/ -v
uv run pytest tests/infra_tests/project/ --cov=infrastructure.project --cov-report=term-missing
```

## See Also

- [`../../../infrastructure/project/AGENTS.md`](../../../infrastructure/project/AGENTS.md) — module under test
- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
