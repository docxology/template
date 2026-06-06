# tests/infra_tests/reference/verification/

## Overview

| File | Focus |
| --- | --- |
| `test_resolver.py` | DOI/arXiv/title resolution, Crossref→OpenAlex fallback, SQLite cache (positive/negative/miss/TTL), offline-first |
| `test_verifier.py` | Status classification (ok/mismatch/fabricated/unverifiable/unchecked/anachronism), identifier extraction, database/file aggregation |
| `test_cli.py` | `verify` and `cache-clear` commands, exit codes, JSON output |

## Conventions

- No mocks. `pytest-httpserver` for Crossref/OpenAlex/arXiv; real temp SQLite for the cache.
- Offline tests assert `unchecked` (never silent `ok`) — preserve that honesty contract.

## Run

```bash
uv run pytest tests/infra_tests/reference/verification/ -v
```

## See also

- [`README.md`](README.md)
- [`../../../../infrastructure/reference/verification/AGENTS.md`](../../../../infrastructure/reference/verification/AGENTS.md)
