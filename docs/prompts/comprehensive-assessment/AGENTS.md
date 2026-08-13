# Comprehensive assessment skill

## Overview

Agent skill `template-comprehensive-assessment` — Full checkout audit with measured claims.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |
| [`README.md`](README.md) | Human-facing workflow index |
| [`references/`](references/) | Progressive-disclosure copy-paste launch prompt and reference documentation |

## Verification

```bash
uv run python scripts/audit/check_template_drift.py
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
- [`references/README.md`](references/README.md) — deep-review prompt index
