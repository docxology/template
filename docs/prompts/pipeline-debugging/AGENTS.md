# Pipeline debugging skill

## Overview

Agent skill `template-pipeline-debugging` — DAG stage failure triage and reproduction.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |

## Verification

```bash
uv run python scripts/runner/execute_pipeline.py --project template_code_project --core-only
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
