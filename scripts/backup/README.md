# Backup Scripts

> Backup and restore scripts for repository data

This directory is a placeholder for backup-specific scripts. Current backup
and restore helpers reside under [`scripts/shell/`](../shell/):

| Script | Description |
|--------|-------------|
| [`../shell/backup-daily.sh`](../shell/backup-daily.sh) | Site-configured daily rsync of `~/.hermes/` |
| [`../shell/backup-weekly.sh`](../shell/backup-weekly.sh) | Site-configured weekly rsync of repository `.cache/`, excluding named transient paths |
| [`../shell/backup-full.sh`](../shell/backup-full.sh) | Named, write-once-by-helper snapshot of the present `.hermes`, `.cache`, and `output` sources |
| [`../shell/restore-test.sh`](../shell/restore-test.sh) | Private-scratch metadata validation and current snapshot-to-copy consistency comparison |

## See Also

- [Maintenance Procedures](../../docs/operational/maintenance.md) — Backup strategy and schedule
- [Scripts README](../README.md) — All pipeline scripts
