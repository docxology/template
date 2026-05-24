# Refactoring skill

## Overview

Agent skill `template-refactoring` — Clean-break refactors with migration notes and coverage preserved.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |

## Verification

```bash
uv run pytest tests/infra_tests/ -q
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
