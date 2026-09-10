# `template_prose_project/src/pipeline/`

Importable prose-review pipeline package.

`__init__.py` owns `run_prose_pipeline` and output orchestration. `checks.py`
owns the configured check registry and individual `_check_<name>` functions.
Scripts call this package; they do not reimplement manuscript analysis,
bibliography checks, or threshold logic.

## Files

| File | Role |
| --- | --- |
| `__init__.py` | `ProseRunArtifacts` and `run_prose_pipeline`. |
| `checks.py` | `CheckResult`, `CHECK_REGISTRY`, and configured check functions. |

## See Also

- [`../README.md`](../README.md) - project source overview
- [`../AGENTS.md`](../AGENTS.md) - source-layer editing rules
