# Manuscript creation skill

## Overview

Agent skill `template-manuscript-creation` — Scaffold manuscript and project from a research brief.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |
| [`references/`](references/) | Progressive-disclosure checklists |

## Verification

```bash
uv run python -m infrastructure.validation.cli markdown projects/templates/template_code_project/manuscript/
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
