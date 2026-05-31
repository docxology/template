# SIA Harness Module

> **Deterministic Meta → Target → Feedback loops for self-improvement tasks.**

**Location:** `infrastructure/sia/`
**Quick Reference:** [Modules Guide](../modules-guide.md) | [SIA Exemplar](../../../projects/templates/template_sia/README.md)

---

## Key Features

- **Task layout gate** — `validate_task_dir()` enforces public/private/reference splits.
- **Fixture replay** — `run_sia_loop(..., live=False)` copies recorded generations for CI.
- **Bounded live path** — `live=True` runs target agents via subprocess; optional Ollama feedback when `llm_model` is set.
- **Evaluation runner** — `run_evaluation()` invokes task `evaluate.py` and normalizes `results.json`.
- **Context ledger** — append-only `context.md` per run under `output/runs/run_{id}/`.

---

## CLI

```bash
uv run python -m infrastructure.sia.cli validate projects/templates/template_sia/tasks/mini_classify
uv run python -m infrastructure.sia.cli inspect-run projects/templates/template_sia/output/runs/run_1/run_summary.json --json
```

---

## Public API

```python
from infrastructure.sia import (
    RunConfig,
    TaskLayout,
    load_agent_execution,
    run_evaluation,
    run_sia_loop,
    validate_task_dir,
)
```

See `infrastructure/sia/__init__.py` for the authoritative export list.

---

## Exemplar project

[`projects/templates/template_sia/`](../../../projects/templates/template_sia/) wires the harness to the `mini_classify` task. Default pipeline runs fixture replay; pass `--live-sia` on `scripts/run_sia_loop.py` for opt-in live execution (not CI).
