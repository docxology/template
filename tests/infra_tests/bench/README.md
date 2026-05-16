# bench/ - Quick Reference

Opt-in performance benchmarks for infrastructure paths that are too expensive
for ordinary CI.

## Run

```bash
uv run pytest tests/infra_tests/bench/ -m bench --benchmark-only --timeout=180
```

Default test runs skip this directory through the `bench` marker.

## Contents

| File | Purpose |
| --- | --- |
| `test_analysis_pipeline_bench.py` | Real subprocess overhead for analysis scripts |
| `test_setup_hook_bench.py` | Setup-hook discovery and subprocess overhead |
| `conftest.py` | Local `bench` marker registration |

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
