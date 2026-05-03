---
name: infrastructure-orchestration
description: Python CLI and menu orchestration for pipeline runs — project slug validation, interactive picker, PipelineRunner wrapping PipelineExecutor, per-stage logs, secure pipeline wrapper. Use when extending run.sh behavior, fixing menu/CLI routing, or testing discovery helpers.
---

# Orchestration (Layer 1)

Entry: `python -m infrastructure.orchestration` (`build_parser`, `main` from `cli.py`).

## Key imports

```python
from infrastructure.orchestration import (
    PipelineRunner,
    validate_project_slug,
    select_project_interactive,
    setup_stage_log,
    run_secure_pipeline,
)
```

## Tests

```bash
uv run pytest tests/infra_tests/orchestration/ -v
```
