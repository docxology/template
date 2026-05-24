# Reproducibility audit skill

## Overview

Agent skill `template-reproducibility-audit` — Determinism and regenerate-from-clean checks before release.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |

## Verification

```bash
./run.sh --project template_code_project --pipeline --core-only
```

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
