# scripts/shell/

Shell helpers used by root entry points and maintenance workflows:
- `bash_utils.sh` — shared helpers for backup and integration tests
- `shell_bootstrap.sh` — uv bootstrap sourced by `run.sh`
- `ci_local.sh` — `act` workflow reproduction, with a fail-closed direct-command fallback
- `health-check.sh` — pre-flight system health check
- `backup-daily.sh` / `backup-weekly.sh` — site-specific rsync tiers
- `backup-full.sh` — write-once-by-helper, metadata-bearing rsync snapshots
- `restore-test.sh` — private-scratch restore and transfer-consistency comparison

## Usage

```bash
bash scripts/shell/health-check.sh
bash scripts/shell/ci_local.sh
bash scripts/shell/ci_local.sh --no-act --dry-run
bash scripts/shell/backup-daily.sh
bash scripts/shell/backup-full.sh --dry-run backup pre-upgrade-2026-08-14
bash scripts/shell/backup-full.sh backup pre-upgrade-2026-08-14
bash scripts/shell/restore-test.sh --list backup pre-upgrade-2026-08-14
bash scripts/shell/restore-test.sh backup pre-upgrade-2026-08-14
```

Full snapshots use the fixed remote layout
`backups/full/<snapshot>/{.hermes,.cache,output}` plus a
`.template-full-backup` contract file. The remote filesystem path passed to
`ssh` never includes the rsync `host:` prefix. Existing snapshots are not
overwritten by cooperating helpers: an atomic per-name lock covers staging and
finalization. Partial failures retain both their partial and lock paths. Restore
puts its tree, diagnostics, and receipt inside a newly created mode-`0700`
control directory. Use `--local-root <absolute-dir>` to run a real disposable
local round trip before configuring an SSH destination.

These helpers do not provide encryption, credential provisioning, retention,
or authorization policy. The restore comparison is against the current stored
snapshot, not a creation-time digest; rsync archive mode also omits hard-link
relationships, ACLs, and extended attributes/resource forks. See
[`docs/operational/maintenance.md`](../../docs/operational/maintenance.md).
