# Real Codebases Fixtures

## Overview

Technical guide for `tests/fixtures/real_codebases/` — shallow-cloned real GitHub repositories used as integration test fixtures.

## Current Codebases

| Directory | Source | What's Included |
|-----------|--------|-----------------|
| `requests/` | `github.com/psf/requests` | `src/requests/` (library source only) |
| `fastapi/` | `github.com/tiangolo/fastapi` | `fastapi/` (main package directory) |

## Key Conventions

- Repos are cloned with `--depth=1` and git sparse-checkout to minimize disk usage.
- **Do not edit** fixture files — regenerate with `python scripts/fixtures/download_real_codebases.py`.
- These fixtures are excluded from git tracking; they must be downloaded locally.
- If a codebase directory already exists and is non-empty, the download script skips it.

## How to Regenerate

```bash
# Remove stale fixtures
rm -rf tests/fixtures/real_codebases/requests tests/fixtures/real_codebases/fastapi

# Re-download
python scripts/fixtures/download_real_codebases.py
```

## See Also

- [README.md](README.md) — Quick navigation
- [`../AGENTS.md`](../AGENTS.md) — Test fixtures documentation
- [`../../../scripts/fixtures/download_real_codebases.py`](../../../scripts/fixtures/download_real_codebases.py) — Download script
