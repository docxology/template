# Feature addition skill

## Overview

Agent skill `template-feature-addition` — Cross-layer features spanning src, scripts, tests, and docs.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |
| [`references/`](references/) | Progressive-disclosure checklists |

## Verification

```bash
uv run python scripts/pipeline/stage_01_test.py --project template_code_project
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
