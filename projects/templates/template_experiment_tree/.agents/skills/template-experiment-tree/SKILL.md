---
name: template-experiment-tree
description: Use when working inside template_experiment_tree — a living research record with a version-controlled experiment tree with frozen nodes. Answers, freezes, reports, and manuscript hydration all flow through the tree store.
---

# template_experiment_tree

## When to use
Working inside `projects/templates/template_experiment_tree/` — recording
experiment answers, freezing preregistrations, regenerating the living
record.

## Quick reference
```bash
uv run python projects/templates/template_experiment_tree/scripts/init_tree.py
uv run python projects/templates/template_experiment_tree/scripts/record_experiment.py <id> <answer> <win|loss|dead_end>
uv run python projects/templates/template_experiment_tree/scripts/report.py
uv run python projects/templates/template_experiment_tree/scripts/z_generate_manuscript_variables.py
```

## Pitfalls
- Frozen nodes refuse answers (by design) — unfreeze is not possible; add a child node instead.
- One run_command per tree: duplicates fail at add time.
- Manuscript tokens must map to tree-derived `{{EXP_*}}` variables; unbacked tokens fail hydration.
