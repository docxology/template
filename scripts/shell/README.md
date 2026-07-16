# scripts/shell/

Shell helpers used by root entry points and maintenance workflows:
- `bash_utils.sh` — shared helpers for backup and integration tests
- `shell_bootstrap.sh` — uv bootstrap sourced by `run.sh`
- `ci_local.sh` — `act` workflow reproduction, with a fail-closed direct-command fallback
- `health-check.sh` — pre-flight system health check
- `backup-daily.sh` / `backup-weekly.sh` / `backup-full.sh` — rsync tiers
- `restore-test.sh` — backup-restore verification

## Usage

```bash
bash scripts/shell/health-check.sh
bash scripts/shell/ci_local.sh
bash scripts/shell/ci_local.sh --no-act --dry-run
bash scripts/shell/backup-daily.sh
```
