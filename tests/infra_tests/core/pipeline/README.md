# core/pipeline/ - Quick Reference

Tests for shared pipeline helpers that are scoped below
`infrastructure.core.pipeline`.

## Run

```bash
uv run pytest tests/infra_tests/core/pipeline/ -q
```

## Contents

| File | Purpose |
| --- | --- |
| `test_multi_project_parallel.py` | Parallel project execution, stream isolation, failure isolation |
| `test_plugins.py` | Plugin-stage schema/loader/merge (PLUGIN-STAGES-1), default-off contract |
| `test_plugins_executor.py` | Executor merges opt-in plugin stages; default-off plan unchanged |

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
