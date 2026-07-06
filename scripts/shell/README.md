# scripts/shell/

Shell helper scripts (stub directory).

The shell scripts currently live at the `scripts/` root level:
- `bash_utils.sh` — shared helpers for backup and integration tests
- `shell_bootstrap.sh` — uv bootstrap sourced by `run.sh`
- `ci_local.sh` — local CI reproduction
- `health-check.sh` — pre-flight system health check
- `backup-daily.sh` / `backup-weekly.sh` / `backup-full.sh` — rsync tiers
- `restore-test.sh` — backup-restore verification

## Usage

```bash
bash scripts/health-check.sh
bash scripts/ci_local.sh
bash scripts/backup-daily.sh
```
