# Operations Scripts

## Overview

Technical guide for `docs/operational/scripts/` — operational helper scripts referenced by the runbook and maintenance docs.

## Files

| File | Purpose |
|------|---------|
| `rotate-logs.sh` | Rotates and compresses Hermes agent logs older than 30 days; cleans project pipeline logs older than 90 days |

## Key Conventions

- Scripts are standalone shell scripts (`set -euo pipefail`).
- Run from repo root unless noted otherwise.
- `rotate-logs.sh` is also documented in [`../maintenance.md`](../maintenance.md).

## Quick Commands

```bash
# Manual log rotation
bash docs/operational/scripts/rotate-logs.sh
```

## See Also

- [README.md](README.md) — Quick navigation
- [../runbook.md](../runbook.md) — Operations runbook
- [../maintenance.md](../maintenance.md) — Maintenance procedures
