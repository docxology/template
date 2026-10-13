# Fixture Download Scripts

> Scripts that fetch or generate test fixture data

**Quick Reference:** [download_real_codebases.py](download_real_codebases.py) | [download_timeseries_benchmarks.py](download_timeseries_benchmarks.py)

## Contents

| Script | Description |
|--------|-------------|
| [`download_real_codebases.py`](download_real_codebases.py) | Shallow-clone real GitHub repos into `tests/fixtures/real_codebases/` |
| [`download_timeseries_benchmarks.py`](download_timeseries_benchmarks.py) | Download M4 timeseries data (or generate synthetic fallback) into `tests/fixtures/timeseries/` |
| [`prepare_acceptance.py`](prepare_acceptance.py) | Prepare the committed exact official-codebase and synthetic-seed contract in fresh owned targets, without platform dependencies |

## Usage

```bash
# Download real codebase fixtures
python scripts/fixtures/download_real_codebases.py

# Download timeseries benchmark data
python scripts/fixtures/download_timeseries_benchmarks.py
```

Both scripts are **idempotent** — re-running skips already-downloaded data.

For hosted acceptance or a matching fresh local fixture tree, use
`python3 -S scripts/fixtures/prepare_acceptance.py`. It refuses existing targets
and binds every prepared body to the committed fixture manifest or seed. The
legacy shallow-clone command selects mutable HEAD and retains `.git` metadata;
that local exploration output is not admitted pinned acceptance DATA.

## See Also

- [Test Fixtures](../../tests/fixtures/) — Where fixture data is stored
- [Test Suite](../../tests/README.md) — Test documentation
