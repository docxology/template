# Syntax guide — template_sia

## Manuscript tokens

Hydrated by `scripts/z_generate_manuscript_variables.py` from loop outputs:

| Token | Source |
| --- | --- |
| `{{CONFIG_TITLE}}` | `manuscript/config.yaml` → `paper.title` |
| `{{SIA_RUN_ID}}` | Identifier of the replayed/executed run |
| `{{SIA_TASK_NAME}}` | `sia.task_name` from config |
| `{{SIA_LIVE_MODE}}` | Whether the run was live or fixture-replay |
| `{{SIA_GENERATION_COUNT}}` | Number of completed generations |
| `{{SIA_MAX_GENERATIONS}}` | Configured generation budget |
| `{{SIA_FINAL_METRIC_NAME}}` | Last generation `metric_name` |
| `{{SIA_FINAL_METRIC_VALUE}}` | Last generation `metric_value` |
| `{{SIA_FINAL_N_SAMPLES}}` | Last generation `n_samples` |
| `{{SIA_METRIC_DELTA}}` | Final minus first metric |
| `{{SIA_METRICS_TABLE}}` | Per-generation metrics table |

Write tokens in the `{{TOKEN}}` double-brace form **directly** in manuscript markdown — that is exactly what the injection pass (`scripts/z_generate_manuscript_variables.py`) resolves. (There is no `${...}` indirection.)

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
  "n_samples": 6
}
```

## Cross-references

Use Pandoc section labels in manuscript (`[@sec:methodology]`) consistent with other exemplars. See [`../manuscript/preamble.md`](../manuscript/preamble.md) for LaTeX packages.
