# config/ — infrastructure config tests

## Overview

Focused tests under `tests/infra_tests/config/` for configuration loading and schema contracts.

## Files

| File | Purpose |
| --- | --- |
| `test_secure_config_schema.py` | Secure config YAML schema validation |
| `test_ci_gate.py` | Real workflow aggregate execution, conditional skip reasons and required-job failures |
| `test_rebind_workflow.py` | Real rebind-workflow execution: receipt-affecting path decision, dispatch semantics, loop termination, submodule-first and commit-then-verify ordering, and the commit and push guards (a dry run, an unverified tree or a moved `main` can never push) |

## Verification

```bash
uv run pytest tests/infra_tests/config/ -v
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — infrastructure test suite
- [`../../../infrastructure/config/`](../../../infrastructure/config/) — config package
