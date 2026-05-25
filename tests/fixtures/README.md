# Test Fixtures

> Shared test data consumed by the test suites

**Quick Reference:** [Real Codebases](real_codebases/) | [Download Scripts](../../scripts/fixtures/)

## Directory Structure

| Directory | Description |
|-----------|-------------|
| [`real_codebases/`](real_codebases/) | Shallow-cloned real GitHub repos (requests, fastapi) — required for `external_fixture` integration tests |
| [`private_project/cogant/`](private_project/cogant/) | Committed COGANT tool + manuscript stubs for `private_project` infra tests (staging tree overrides when present) |
| `timeseries/` | M4/synthetic series — created by `download_timeseries_benchmarks.py` (required for `bench` integration tests) |

## Setup

Fixtures must be downloaded or generated before running tests that depend on them:

```bash
# Download real codebase fixtures
python scripts/fixtures/download_real_codebases.py

# Download timeseries benchmark data
python scripts/fixtures/download_timeseries_benchmarks.py
```

Both scripts are **idempotent** — safe to re-run.

Timeseries benchmark tests also require optional Python deps:

```bash
uv sync --group timeseries-bench
```

## See Also

- [Real Codebases](real_codebases/) — Cloned repo fixtures
- [Download Scripts](../../scripts/fixtures/) — Fixture generators
- [Test Suite](../README.md) — Full test documentation
