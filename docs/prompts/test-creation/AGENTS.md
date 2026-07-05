# Test creation skill

## Overview

Agent skill `template-test-creation` — Tests under the no-mocks policy.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |
| [`references/`](references/) | Progressive-disclosure checklists |

## Verification

```bash
uv run pytest projects/templates/template_code_project/tests/ -q
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
