# Syntax guide — template_sia

## Manuscript tokens

Hydrated by `scripts/z_generate_manuscript_variables.py` from loop outputs:

| Token | Source |
| --- | --- |
| `${CONFIG_TITLE}` | `manuscript/config.yaml` → `paper.title` |
| `${SIA_GENERATION_COUNT}` | Number of completed generations |
| `${SIA_FINAL_METRIC}` | Last generation `metric_value` |
| `${SIA_FINAL_METRIC_NAME}` | Last generation `metric_name` |
| `${SIA_IMPROVEMENT_DELTA}` | Final minus first metric |
| `${SIA_TASK_NAME}` | `sia.task_name` from config |

Use `${TOKEN}` form in manuscript markdown (resolved to `{{TOKEN}}` internally by the injection pass).

## Task directory layout

```
tasks/<task_name>/
  data/public/
    task.md          # Agent-visible instructions
    train.csv        # Public training rows
    evaluate.py      # Writes results.json when passed --gen-dir
  data/private/
    labels.csv       # Held-out labels (eval only)
  reference/
    reference_target_agent.py
```

Validate with:

```bash
uv run python -m infrastructure.sia.cli validate projects/templates/template_sia/tasks/mini_classify
```

## `results.json` schema

```json
{
  "metric_name": "accuracy",
  "metric_value": 0.8333,
  "n_samples": 12
}
```

## Cross-references

Use Pandoc section labels in manuscript (`[@sec:methodology]`) consistent with other exemplars. See [`../manuscript/preamble.md`](../manuscript/preamble.md) for LaTeX packages.
