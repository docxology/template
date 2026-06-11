# benchmark/ - Quick Reference

Performance benchmarks for infrastructure paths that are too expensive for a
benchmark-only run, but still part of the full infra suite.

## Run

```bash
uv run pytest tests/infra_tests/benchmark/ -m bench --benchmark-only --timeout=180
```

Use `-m bench --benchmark-only` when you want to isolate the benchmark pass.

## Contents

| File | Purpose |
| --- | --- |
| `test_analysis_pipeline_bench.py` | Real subprocess overhead for analysis scripts |
| `test_setup_hook_bench.py` | Setup-hook discovery and subprocess overhead |
| `conftest.py` | Local `bench` marker registration |

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
