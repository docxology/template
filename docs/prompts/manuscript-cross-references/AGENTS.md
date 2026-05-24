# Manuscript cross-references skill

## Overview

Agent skill `template-manuscript-cross-references` — Registry/token cross-refs and citation integrity.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |

## Verification

```bash
uv run python -m infrastructure.validation.cli markdown projects/template_code_project/manuscript/
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
