# Infrastructure module skill

## Overview

Agent skill `template-infrastructure-module` — New generic packages under infrastructure/.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |

## Verification

```bash
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60 -q
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
