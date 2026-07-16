# scripts/shell/ — Shell Helper Scripts

## Purpose

This subdirectory contains the shared shell helpers and local CI entry point
used by the repository's root wrappers and maintenance workflows.

## Shell scripts

| Script | Purpose |
|--------|---------|
| `bash_utils.sh` | Shared shell helpers for backup/health scripts and integration tests |
| `shell_bootstrap.sh` | Shared `uv` bootstrap and sandbox env vars; sourced by `run.sh` / `secure_run.sh` |
| `ci_local.sh` | Local CI reproduction (`act` when available, else a documented fail-closed direct-command subset) |
| `health-check.sh` | Pre-flight system health check (Python, uv, disk, Docker, repo) |
| `backup-daily.sh` | Daily rsync backup tier |
| `backup-weekly.sh` | Weekly rsync backup tier |
| `backup-full.sh` | Full rsync backup |
| `restore-test.sh` | Non-destructive backup-restore verification |

## Usage

```bash
# System health check
bash scripts/shell/health-check.sh

# Local CI
bash scripts/shell/ci_local.sh
bash scripts/shell/ci_local.sh --no-act --dry-run

# Backup
bash scripts/shell/backup-daily.sh
```

## See also

- [`scripts/AGENTS.md`](../AGENTS.md) — full scripts inventory
- [`scripts/backup/`](../backup/) — backup scripts directory
