# tests/infra_tests/project/ — Tests for `infrastructure.project`

## Purpose

Tests for `infrastructure.project.discovery` (`discover_projects`, project metadata loading) and `infrastructure.project.validation` (`validate_project_structure`). All tests follow the No-Mocks Policy: real `tmp_path` directories with real files instead of mocks.

## Files

- `test_discovery.py` — exhaustive coverage of `discover_projects()`: nested project layouts, qualified-name handling, the `src/` + `tests/` runnable filter, manuscript-only projects, archived/in-progress filtering, edge cases (~47 KB)
- `test_validation.py` — `validate_project_structure()` happy paths and failure modes (missing dir, missing `src/`, missing `tests/`, no Python files in `src/`)
- `test_thin_orchestrator_drift.py` — drift policy: **repo** `scripts/` fat files emit **WARNING**; **project** `scripts/` fat files emit **ERROR**; `scan_project_scripts()` only scans `PUBLIC_PROJECT_NAMES` exemplars

## Drift vs line-count policies

| Scope | Tool | Fat script (≥200 lines, 3+ non-trivial functions) |
| --- | --- | --- |
| `scripts/` (repo) | `check_repo_scripts()` | WARNING — consider moving helpers to `infrastructure/` |
| `projects/{name}/scripts/` | `check_project_scripts()` | ERROR — move logic to `src/` |
| Public exemplar scripts | `scan_project_scripts()` | FAIL at 250 lines (WARN at 150) |

Project script detection uses paths starting with `projects/` and containing `/scripts/`.

## Running

```bash
uv run pytest tests/infra_tests/project/ -v
uv run pytest tests/infra_tests/project/ --cov=infrastructure.project --cov-report=term-missing
```

## See Also

- [`../../../infrastructure/project/AGENTS.md`](../../../infrastructure/project/AGENTS.md) — module under test
- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
