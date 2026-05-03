# Fixture Download Scripts

> Scripts that fetch or generate test fixture data

**Quick Reference:** [download_real_codebases.py](download_real_codebases.py) | [download_timeseries_benchmarks.py](download_timeseries_benchmarks.py)

## Contents

| Script | Description |
|--------|-------------|
| [`download_real_codebases.py`](download_real_codebases.py) | Shallow-clone real GitHub repos into `tests/fixtures/real_codebases/` |
| [`download_timeseries_benchmarks.py`](download_timeseries_benchmarks.py) | Download M4 timeseries data (or generate synthetic fallback) into `tests/fixtures/timeseries/` |

## Usage

```bash
# Download real codebase fixtures
python scripts/fixtures/download_real_codebases.py

# Download timeseries benchmark data
python scripts/fixtures/download_timeseries_benchmarks.py
```

Both scripts are **idempotent** — re-running skips already-downloaded data.

## See Also

- [Test Fixtures](../../tests/fixtures/) — Where fixture data is stored
- [Test Suite](../../tests/README.md) — Test documentation
