# Orchestration Module

> **Shell-replacement orchestration — the Python entry point invoked by `run.sh` and `secure_run.sh`.**

**Location:** `infrastructure/orchestration/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [Pipeline Reference](../../core/architecture.md) | [Code Review Checklist](../../development/code-review-checklist.md)

---

## Key Features

- **Shell replacement** — all logic that used to live in `run.sh` / `secure_run.sh` now lives here. The shells are thin dispatchers that bootstrap `uv`/`.venv` and exec `python -m infrastructure.orchestration`.
- **Pipeline runner** — `PipelineRunner` wraps the existing `infrastructure.core.pipeline.PipelineExecutor`. No pipeline logic is re-implemented here.
- **Project selection** — `select_project_interactive`, `validate_project_slug` (rejects path traversal).
- **Menu rendering** — deterministic interactive menu, fully unit-testable.
- **Stage logging** — per-stage log files via `setup_stage_log`.
- **Secure flow** — `run_secure_pipeline` wraps steganography post-processing.

---

## CLI

```bash
uv run python -m infrastructure.orchestration                 # interactive menu
uv run python -m infrastructure.orchestration --pipeline      # default full pipeline
uv run python -m infrastructure.orchestration secure --project <name>
```

`./run.sh` and `./secure_run.sh` are the user-facing entry points; they call the above.

---

## Public API

```python
from infrastructure.orchestration import (
    MENU_OPTIONS, PipelineRunner,
    build_parser, main,
    render_menu, run_secure_pipeline,
    select_project_interactive, setup_stage_log,
    validate_project_slug,
)
```

---

## Review Criteria Mapping

The orchestration module is reviewed primarily against criteria 2 (Composability — must not re-implement `infrastructure.core.pipeline` logic), 3 (Functionality / SSOT — orchestration is the *only* place that owns shell-side flow), and 5 (Validation — slug validation rejects traversal). See [Code Review Checklist](../../development/code-review-checklist.md).
