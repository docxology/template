# benchmark/ - Quick Reference

Performance benchmarks for infrastructure paths that are too expensive for a
benchmark-only run, but still part of the full infra suite.

## Run

```bash
uv run pytest tests/infra_tests/benchmark/ -m bench --benchmark-only --timeout=180
```

Use `-m bench --benchmark-only` when you want to isolate the benchmark pass.

The analysis-pipeline benchmark executes all 1, 5, or 25 scripts in order
through the genuine guarded subprocess path. Its single-script member records
three measured rounds after one warmup. The 5- and 25-script members each record
one complete cold run; their statistics do not establish timing stability.
Explicit member safety limits are 60, 60, and 180 seconds respectively. The
25-script limit follows the documented benchmark budget above, replacing the
former function-level 60-second marker that overrode that command. These are
diagnostic safety limits, not performance targets; measured runtime remains
visible. Production, Root acceptance, and workflow deadlines are unchanged.

## Contents

| File | Purpose |
| --- | --- |
| `test_analysis_pipeline_bench.py` | Real subprocess overhead for analysis scripts |
| `test_setup_hook_bench.py` | Setup-hook discovery and subprocess overhead |
| `conftest.py` | Local `bench` marker registration |

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
