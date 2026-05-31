---
name: infrastructure-sia
description: Skill for the Self-Improvement Agent (SIA) harness contract. Use when validating task public/private layouts, generation artifact trees, evaluation runners, fixture replay loops, or opt-in live Meta→Target→Feedback cycles in template projects.
---

# SIA Harness

Deterministic harness for Meta → Target → Feedback generation loops with
public/private task splits. Implements contracts inspired by
[hexo-ai/sia](https://github.com/hexo-ai/sia); does not vendor upstream code.

## Commands

```bash
uv run python -m infrastructure.sia.cli validate projects/templates/template_sia/tasks/mini_classify
uv run python scripts/02_run_analysis.py --project templates/template_sia
```

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

## Task layout

Each task directory exposes:

- `data/public/` — agent-visible inputs
- `data/private/` — evaluation-only labels
- `reference/` — baseline target agent
- `evaluate.py` — writes `results.json` with `metric_name`, `metric_value`, `n_samples`

## Exemplar project

[`projects/templates/template_sia/`](../../projects/templates/template_sia/) runs
fixture replay by default (`live=False`). Pass `--live-sia` on
`scripts/run_sia_loop.py` for opt-in Ollama-backed feedback (not CI).
