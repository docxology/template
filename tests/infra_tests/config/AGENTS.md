# config/ — infrastructure config tests

## Overview

Focused tests under `tests/infra_tests/config/` for configuration loading and schema contracts.

## Files

| File | Purpose |
| --- | --- |
| `test_secure_config_schema.py` | Secure config YAML schema validation |

## Verification

```bash
uv run pytest tests/infra_tests/config/ -v
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — infrastructure test suite
- [`../../../infrastructure/config/`](../../../infrastructure/config/) — config package
