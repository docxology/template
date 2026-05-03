# Logrotate Configuration

## Overview

Technical guide for `infrastructure/logrotate.d/` — logrotate configuration files for the template repository's log rotation.

## Files

| File | Purpose |
|------|---------|
| `template` | Logrotate configuration for template pipeline and agent logs |

## Key Conventions

- Configuration follows standard logrotate syntax.
- Install system-wide with: `sudo cp infrastructure/logrotate.d/template /etc/logrotate.d/`
- Test dry-run with: `logrotate -d /etc/logrotate.d/template`
- The manual rotation script lives at [`docs/operations/scripts/rotate-logs.sh`](../../docs/operations/scripts/rotate-logs.sh).

## See Also

- [README.md](README.md) — Quick navigation
- [../../docs/operations/maintenance.md](../../docs/operations/maintenance.md) — Maintenance procedures
- [../../docs/operations/scripts/rotate-logs.sh](../../docs/operations/scripts/rotate-logs.sh) — Manual rotation script
