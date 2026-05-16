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

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
