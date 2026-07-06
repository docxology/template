# scripts/shell/ — Shell Helper Scripts

## Purpose

This subdirectory (currently a stub) is the planned home for shell helper
scripts.  The shell scripts currently live at the root of `scripts/` or in the
`backup/` subdirectory.

## Shell scripts (at scripts/ root)

| Script | Purpose |
|--------|---------|
| `bash_utils.sh` | Shared shell helpers for backup/health scripts and integration tests |
| `shell_bootstrap.sh` | Shared `uv` bootstrap and sandbox env vars; sourced by `run.sh` / `secure_run.sh` |
| `ci_local.sh` | Local CI reproduction (`act` when available, else pure-Python fallback) |
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

# Backup
bash scripts/shell/backup-daily.sh
```

## See also

- [`scripts/AGENTS.md`](../AGENTS.md) — full scripts inventory
- [`scripts/backup/`](../backup/) — backup scripts directory
