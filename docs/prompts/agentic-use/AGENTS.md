# Agentic use skill

## Overview

Agent skill `template-agentic-use` - skill discovery, routing hardening, and optional external-skill review for the Research Project Template.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |

## Verification

```bash
uv run python -m infrastructure.skills check
uv run python -m infrastructure.skills check-contracts
uv run pytest tests/infra_tests/skills -q
```

## See also

- [`../AGENTS.md`](../AGENTS.md) - prompts hub
- [`../SKILL.md`](../SKILL.md) - workflow router
- [`../../../infrastructure/skills/SKILL.md`](../../../infrastructure/skills/SKILL.md) - discovery API
