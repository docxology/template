# Backup Scripts

## Overview

Technical guide for `scripts/backup/` — placeholder directory for backup and restore scripts in the template repository.

## Current State

This directory is currently empty. Backup scripts (`backup-daily.sh`, `backup-weekly.sh`, `backup-full.sh`) live in the parent [`scripts/`](../) directory and are documented in [`scripts/AGENTS.md`](../AGENTS.md).

This directory exists to provide a future home for backup-specific scripts as they are migrated or added.

## Key Conventions

- Backup scripts follow `set -euo pipefail` shell conventions.
- Scripts use `rsync` over SSH for remote backup targets.
- Refer to [`docs/operations/maintenance.md`](../../docs/operations/maintenance.md) for the full backup strategy.

## See Also

- [README.md](README.md) — Quick navigation
- [`../AGENTS.md`](../AGENTS.md) — Scripts directory documentation
- [`../../docs/operations/maintenance.md`](../../docs/operations/maintenance.md) — Maintenance procedures
