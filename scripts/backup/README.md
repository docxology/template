# Backup Scripts

> Backup and restore scripts for repository data

This directory is a placeholder for backup-specific scripts. Current backup scripts reside in the parent [`scripts/`](../) directory:

| Script | Description |
|--------|-------------|
| [`../backup-daily.sh`](../backup-daily.sh) | Daily rsync of `~/.template/` to remote host |
| [`../backup-weekly.sh`](../backup-weekly.sh) | Weekly backup with longer retention |
| [`../backup-full.sh`](../backup-full.sh) | Full backup of all critical directories |

## See Also

- [Maintenance Procedures](../../docs/operational/maintenance.md) — Backup strategy and schedule
- [Scripts README](../README.md) — All pipeline scripts
