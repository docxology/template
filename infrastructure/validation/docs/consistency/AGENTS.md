# consistency/ — documentation consistency checks

## Overview

Python modules backing `check_*` functions re-exported from [`../consistency_lint.py`](../consistency_lint.py).

## Modules

| Module | Check |
| --- | --- |
| `package_counts.py` | `check_module_count_claims` |
| `ghost_paths.py` | `check_no_ghost_projects` |
| `_shared.py` | Shared helpers, `Inconsistency`, doc iteration |
| `import_resolution.py` | `check_doc_imports_resolve` |
| `readme_inventory.py` | `check_readme_files_list`, `check_canonical_count_singularity` |
| `shell_contracts.py` | `check_command_conventions`, `check_stale_shell_contracts` |
| `memory_decision.py` | `check_memory_decision_rule_links` |
| `project_discovery.py` | `check_project_discovery_claims` |

## Verification

```bash
uv run pytest tests/infra_tests/validation/docs/test_consistency_lint.py -q
uv run python scripts/audit/lint_docs.py --consistency-only
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — validation docs package
- [`../../../../tests/infra_tests/validation/docs/`](../../../../tests/infra_tests/validation/docs/) — regression tests
