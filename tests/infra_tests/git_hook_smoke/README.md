# git_hook_smoke/ - Quick Reference

Fast pre-push smoke tests for hooks that should finish in a few seconds.

## Run

```bash
uv run pytest tests/infra_tests/git_hook_smoke/ -q --import-mode=importlib
```

## Contents

| File | Purpose |
| --- | --- |
| `test_hook_git_environment.py` | Real nested-Git index isolation, with an unsafe-prefix negative control |
| `test_gate.py` | Project discovery, pipeline config, import, validation CLI smoke |
| `test_tracked_generated_artifacts.py` | Generated-artifact guard regression tests |

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../README.md`](../README.md)

The push smoke and documentation hooks clear Git repository-local variables in
their child shell before running commands that create temporary repositories.
The staged-secret hook retains its index environment so it checks the actual
staged content. See [Git hook environment guidance](https://git-scm.com/docs/githooks).
