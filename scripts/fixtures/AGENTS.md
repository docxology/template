# Fixture Download Scripts

## Overview

Technical guide for `scripts/fixtures/` — scripts that download or generate test fixture data for the template repository's test suites.

## Files

| File | Purpose |
|------|---------|
| `download_real_codebases.py` | Shallow-clones real GitHub repos (requests, fastapi) via sparse-checkout into `tests/fixtures/real_codebases/` |
| `download_timeseries_benchmarks.py` | Downloads M4 monthly timeseries data from Hugging Face, with synthetic fallback, into `tests/fixtures/timeseries/` |

## Key Conventions

- Both scripts are **resumable** — they skip downloading if the target directory already exists and is non-empty.
- Run from repo root: `python scripts/fixtures/download_real_codebases.py`
- Fixtures are stored under `tests/fixtures/` and consumed by test suites in `tests/`.
- The `requests` and `fastapi` repos use `--depth=1` and git sparse-checkout to minimize disk usage.

## See Also

- [README.md](README.md) — Quick navigation
- [`tests/fixtures/`](../../tests/fixtures/) — Fixture storage directory
- [`tests/AGENTS.md`](../../tests/AGENTS.md) — Test suite documentation
