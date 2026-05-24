# Literature synthesis skill

## Overview

Agent skill `template-literature-synthesis` — LLM prompt blocks for literature search corpus synthesis.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |
- [`references/`](references/) — progressive-disclosure checklists

## Verification

```bash
uv run pytest tests/infra_tests/search/ -q
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
