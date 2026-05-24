# tests/infra_tests/validation/docs/consistency/

Tests for repository documentation consistency linters in
`infrastructure/validation/docs/consistency_lint.py`.

## Modules under test

| Test file | Linter entry |
| --- | --- |
| `test_readme_inventory.py` | `check_readme_files_list` |
| `test_shell_contracts.py` | shell command contract checks |
| `test_import_resolution.py` | import path resolution |
| `test_ghost_paths.py` | stale path references |
| `test_package_counts.py` | package count claims |

Fixtures live in `conftest.py` (`scaffold_repo`, `write_doc`).

## Commands

```bash
uv run pytest tests/infra_tests/validation/docs/consistency/ -q
```
