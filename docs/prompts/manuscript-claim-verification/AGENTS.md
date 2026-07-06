# Manuscript claim verification skill

## Overview

Agent skill `template-manuscript-claim-verification` — Triple-check manuscript claims against code, data, and renderer output.

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
