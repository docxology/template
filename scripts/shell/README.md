# scripts/shell/

Shell helpers used by root entry points and maintenance workflows:
- `bash_utils.sh` — shared helpers for backup and integration tests
- `shell_bootstrap.sh` — prepared root-Python selection sourced by `run.sh` and `secure_run.sh`
- `setup-system-deps.sh` — one-shot installer for pandoc, XeLaTeX + LaTeX packages, and uv (`--check` = verify only)
- `prepare_pinned_elan.sh` — sourced hosted Elan 4.2.4 bootstrap with immutable official archive pins and acquisition-only credential scope
- `ci_local.sh` — `act` workflow reproduction, with a fail-closed direct-command fallback
- `health-check.sh` — pre-flight system health check (Python, uv, pandoc, xelatex, Docker)
- `backup-daily.sh` / `backup-weekly.sh` — site-specific rsync tiers
- `backup-full.sh` — write-once-by-helper, metadata-bearing rsync snapshots
- `restore-test.sh` — private-scratch restore and transfer-consistency comparison

## Usage

```bash
bash scripts/shell/health-check.sh
bash scripts/shell/setup-system-deps.sh --check
bash scripts/shell/setup-system-deps.sh
# After your explicit locked sync, preserve its selected Python dependencies:
bash scripts/shell/setup-system-deps.sh --prepared-python .venv/bin/python
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

## Hosted Lean preparation

Existing hosted workflow steps source `prepare_pinned_elan.sh` before their
unchanged source-pinned Lean installation commands. The shared helper replaces
a checksum-pinned script whose secondary installer download still used mutable
`latest`. Exact official asset IDs, complete byte lengths and SHA-256 values
now bind the actual Elan 4.2.4 installer for Linux/macOS on X64/ARM64.

Source the helper inside the original step so its timeout still covers both
bootstrap and compiler setup. Acquisition alone receives the step's GitHub token;
the installer and following compiler commands do not. There is no implicit
default Lean installation, browser-download fallback or acceptance output.
This installer is for isolated hosted runners, not a shared workstation.

