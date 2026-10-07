# Canonical synthetic time-series seed

These ten benchmark fixtures are the actual output of
[`generate_synthetic_timeseries`](../../../scripts/fixtures/download_timeseries_benchmarks.py)
with its declared NumPy seed 42. They are synthetic test inputs, not empirical
research observations or a downloaded M4 dataset. The committed snapshot keeps
floating-point serialization identical across macOS/Linux and Python minors.

The hosted fixture action checks [SHA256SUMS](SHA256SUMS) and copies these bytes to
`tests/fixtures/timeseries/synthetic/` before every source observation and reader.
See [AGENTS.md](AGENTS.md) for regeneration custody.
