# config/ — infrastructure config tests

## Overview

Focused tests under `tests/infra_tests/config/` for configuration loading and schema contracts.

## Files

| File | Purpose |
| --- | --- |
| `test_secure_config_schema.py` | Secure config YAML schema validation |
| `test_ci_gate.py` | Real workflow aggregate execution, conditional skip reasons and required-job failures |
| `test_rebind_workflow.py` | Real post-merge rebind execution: receipt-affecting path decision, loop termination, submodule-first ordering and the commit guard that refuses an unverified tree |

## Verification

```bash
uv run pytest tests/infra_tests/config/ -v
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — infrastructure test suite
- [`../../../infrastructure/config/`](../../../infrastructure/config/) — config package
