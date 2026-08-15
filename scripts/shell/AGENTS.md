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
| `backup-full.sh` | Write-once-by-helper, versioned rsync snapshot (`.hermes`, `.cache`, `output`) |
| `restore-test.sh` | Private-scratch restore plus metadata and transfer-consistency comparison |

## Usage

```bash
# System health check
bash scripts/shell/health-check.sh

# Local CI
bash scripts/shell/ci_local.sh
bash scripts/shell/ci_local.sh --no-act --dry-run

# Backup
bash scripts/shell/backup-daily.sh

# Inspect, create, list, and verify a named full snapshot
bash scripts/shell/backup-full.sh --dry-run backup pre-upgrade-2026-08-14
bash scripts/shell/backup-full.sh backup pre-upgrade-2026-08-14
bash scripts/shell/restore-test.sh --list backup pre-upgrade-2026-08-14
bash scripts/shell/restore-test.sh backup pre-upgrade-2026-08-14
```

## Full snapshot contract

- `backup-full.sh` maps sources to the fixed snapshot labels `.hermes/`,
  `.cache/`, and `output/`; it never appends an absolute source path.
- The SSH filesystem path is `backups/full/<snapshot>` relative to the remote
  login directory. Only rsync receives the `host:path` address.
- An atomic per-name `.lock` admits one cooperating writer. A snapshot is
  staged under a unique `.partial.*` name and finalized only
  after all transfers and `.template-full-backup` metadata succeed. Existing
  final snapshots are never overwritten by this helper; a failure retains the
  named partial and lock paths for explicit inspection.
- `restore-test.sh` never restores over a checkout and never deletes an older
  restore. It uses one mode-`0700` control directory for the restored tree,
  diagnostic output, and receipt; validates metadata; and compares the restored
  tree to the *current* snapshot with rsync checksums, links, permissions, and
  file timestamps.
- `--local-root <absolute-dir>` runs the same rsync contract against local
  storage for disposable end-to-end testing. It is not an off-site backup.
- The helpers do not supply encryption, credentials, retention, or owner
  authorization. Operators must provide those controls independently.
- The comparison proves round-trip transfer consistency, not creation-time or
  at-rest integrity: metadata has no content-digest manifest. Sources are not
  quiesced into one coherent point-in-time view, and rsync archive mode does not
  preserve hard-link relationships, ACLs, or extended attributes/resource
  forks.

## See also

- [`scripts/AGENTS.md`](../AGENTS.md) — full scripts inventory
- [`scripts/backup/`](../backup/) — backup scripts directory
