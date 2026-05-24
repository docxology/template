# Validation quality skill

## Overview

Agent skill `template-validation-quality` — Validation CLI, PDF/markdown gates, and output checks.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |

## Verification

```bash
uv run python -m infrastructure.validation.cli --help
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
