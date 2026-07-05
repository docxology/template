# Methods orchestration skill

## Overview

Agent skill `template-methods-orchestration` — repo-wide methods orchestration:
audit, plan, and repair method-to-pipeline provenance across manuscript methods
files, `pipeline.yaml` stage contracts, artifact manifests, and evidence
registries.

## Files

| File | Role |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Routable workflow (canonical) |

## Verification

```bash
uv run python -m infrastructure.methods plan --project <project> --format json --check
```

Keep edits in source layers. Generated output is evidence, not the fix target.

## See also

- [`../AGENTS.md`](../AGENTS.md) — prompts hub
- [`SKILL.md`](SKILL.md) — full workflow
