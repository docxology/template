# Backup Scripts

## Overview

Technical guide for `scripts/backup/` — placeholder directory for backup and restore scripts in the template repository.

## Current State

This directory is currently empty. Backup and restore helpers
(`backup-daily.sh`, `backup-weekly.sh`, `backup-full.sh`, `restore-test.sh`)
live in [`scripts/shell/`](../shell/) and are documented in
[`scripts/shell/AGENTS.md`](../shell/AGENTS.md).

This directory exists to provide a future home for backup-specific scripts as they are migrated or added.

## Key Conventions

- Backup scripts follow `set -euo pipefail` shell conventions.
- Remote mode uses `rsync` over SSH; the full/restore pair also supports a
  matching absolute `--local-root` for disposable local contract tests.
- Refer to [`docs/operational/maintenance.md`](../../docs/operational/maintenance.md) for the full backup strategy.

## See Also

- [README.md](README.md) — Quick navigation
- [`../AGENTS.md`](../AGENTS.md) — Scripts directory documentation
- [`../../docs/operational/maintenance.md`](../../docs/operational/maintenance.md) — Maintenance procedures
