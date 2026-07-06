# Documentation creation skill

## Overview

Agent skill `template-documentation-creation` — Author or refresh AGENTS.md and README.md for template directories.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |

## Verification

```bash
uv run python scripts/audit/lint_docs.py --consistency-only
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
