# Code development skill

## Overview

Agent skill `template-code-development` — Standards-compliant code in infrastructure or project src/.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |
- [`references/`](references/) — progressive-disclosure checklists

## Verification

```bash
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60 -q
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
