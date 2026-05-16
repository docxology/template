# git_hook_smoke/ - Quick Reference

Fast pre-push smoke tests for hooks that should finish in a few seconds.

## Run

```bash
uv run pytest tests/infra_tests/git_hook_smoke/ -q --import-mode=importlib
```

## Contents

| File | Purpose |
| --- | --- |
| `test_gate.py` | Project discovery, pipeline config, import, validation CLI smoke |
| `test_tracked_generated_artifacts.py` | Generated-artifact guard regression tests |

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)
