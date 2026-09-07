# Maintenance procedures

These procedures maintain a public template checkout without conflating local
housekeeping, source changes, generated evidence, remote synchronization, or
release authority. Always inspect the current checkout and the relevant
`AGENTS.md` before acting.

## Maintenance status vocabulary

Use only `passed`, `failed`, `blocked`, `not run`, `not applicable`, and
`unavailable` for gates. Optional-tool output that says `skipped` stays
`skipped`; it is not a clean result. Record command, revision, scope, exit code,
and limitations for every cited result.

## Log rotation

The tracked helper
[`scripts/rotate-logs.sh`](scripts/rotate-logs.sh) currently has two policies:

| Target | Implemented action |
| --- | --- |
| `~/.hermes/logs/*.log` older than 30 days | gzip and move to `~/.hermes/logs/archive/` |
| Any `*/output/logs/*.log` older than 90 days beneath the checkout | delete |

The second action is destructive. Preview exact targets before running it:

```bash
find "$HOME/.hermes/logs" -name '*.log' -type f -mtime +30 -print 2>/dev/null
find . -path '*/output/logs/*.log' -type f -mtime +90 -print
```

Confirm that no live producer is writing those files and that retention or
incident requirements allow removal. Then, if authorized:

```bash
bash docs/operational/scripts/rotate-logs.sh
```

The separate `infrastructure/logrotate.d/template` configuration applies to
`~/.template/logs/*.log`, not Hermes or project pipeline logs. Installing it
under `/etc/logrotate.d/` is a privileged system change; use `logrotate -d`
against a reviewed copy before installation.

## Dependency maintenance

`pyproject.toml` owns declared requirements and `uv.lock` owns the resolved
environment. Start with read-only or lock-preserving checks:

```bash
git status --short --branch
uv lock --check
uv pip list --outdated
uv run pip-audit --locked .
```

`uv pip list --outdated` and `pip-audit` depend on current index/advisory
access. Network failure is `unavailable`, not evidence that dependencies are
current or vulnerability-free.

Make upgrades on a dedicated branch with a preserved recovery path:

```bash
# Narrow upgrade preferred
uv lock --upgrade-package <package>
uv sync --frozen

# Inspect exactly what changed
git diff -- pyproject.toml uv.lock
```

Use `uv lock --upgrade` only for a deliberately broad update. Do not blindly
commit a regenerated lockfile; review source, version, platform, and transitive
changes, then run the applicable Python matrix, package/build, security,
project, and render gates. Hosted CI remains the evidence for all supported
interpreters and OSes.

Security advisories require prompt triage, not an automatic unrestricted
upgrade. Confirm applicability, patched versions, compatibility, and the
time-bounded ignore policy in `.github/pip-audit-ignore.txt`.

## Storage inspection

The core pipeline writes file-backed checkpoints, logs, reports, and artifacts,
but individual projects or optional modules may use additional stores. Discover
current paths rather than relying on copied size estimates:

```bash
du -sh .venv .cache output projects/*/output 2>/dev/null | sort -h
df -h .
find output projects -type f -size +100M -print 2>/dev/null
docker system df 2>/dev/null
```

Do not write local audit snapshots under `docs/`; that tree is public source.
Store operator-only measurements outside the repository or in a declared,
gitignored run directory. Before deleting caches, models, Docker data, or
outputs, resolve exact targets and confirm they are not the only copy of
unpublished evidence.

## Backup helpers and acceptance boundary

The shell helpers under `scripts/shell/` are site-specific examples. They
assume an SSH-configured host named `backup`, transmit potentially sensitive
Hermes/cache/output content, and do not implement encryption, retention,
credential provisioning, or provider-independent verification.

| Script | Current documentation status |
| --- | --- |
| `backup-daily.sh` | Operator-configured rsync of `~/.hermes`; not a repository release gate. |
| `backup-weekly.sh` | Operator-configured rsync of `.cache`; not a repository release gate. |
| `backup-full.sh` | Available as an operator-configured helper. Creates a write-once-by-cooperating-helper snapshot with fixed `.hermes`, `.cache`, and `output` labels; `--dry-run` performs no network or filesystem writes. |
| `restore-test.sh` | Available for non-destructive transfer verification. `--list` is read-only; restore uses a private control directory, validates snapshot metadata, compares the current snapshot with its restored copy, and emits a restricted receipt. |

The full pair now uses one layout contract:
`backups/full/<snapshot>/{.hermes,.cache,output}` relative to the remote login
directory, plus `.template-full-backup` metadata. `ssh` receives only that
remote filesystem path; rsync alone receives `host:path`. Backup refuses to
overwrite an existing snapshot, uses an atomic per-name directory lock across
staging and finalization, retains explicitly named partial and lock paths on
failure, and records every present or absent source label. Restore never removes
a prior scratch tree, keeps its restored tree/diagnostics/receipt together under
one mode-`0700` control directory, rejects a local scratch parent inside the
backup namespace, and fails closed on undeclared layout or malformed metadata.

```bash
# Resolve and inspect mappings without connecting or writing
bash scripts/shell/backup-full.sh --dry-run backup pre-upgrade-2026-08-14

# Create, list, then verify a write-once-by-helper remote snapshot
bash scripts/shell/backup-full.sh backup pre-upgrade-2026-08-14
bash scripts/shell/restore-test.sh --list backup pre-upgrade-2026-08-14
bash scripts/shell/restore-test.sh backup pre-upgrade-2026-08-14
```

For a disposable real-rsync round trip without SSH, pass the same absolute
local root to both scripts:

```bash
BACKUP_SCRATCH_ROOT="$(mktemp -d)"
bash scripts/shell/backup-full.sh \
  --local-root "${BACKUP_SCRATCH_ROOT}/backups/full" local-contract-test
bash scripts/shell/restore-test.sh \
  --local-root "${BACKUP_SCRATCH_ROOT}/backups/full" \
  --scratch-parent "${BACKUP_SCRATCH_ROOT}" local-contract-test
```

The local transport establishes the script and layout contract, not remote
availability. Run the remote `--list` and restore against the operator's actual
SSH host before treating a snapshot as recoverable there.

### Implemented checks and remaining operator controls

Implemented by the pair:

1. Explicit repository/home sources and a validated destination/snapshot name.
2. Non-writing `--dry-run` and read-only `--list` modes.
3. A newly created scratch restore, never the checkout or a reused directory.
4. Versioned layout metadata that records the repository revision when
   available and classifies every expected source label as present or absent.
5. A post-restore comparison of the current stored snapshot with its restored
   copy using rsync checksums, symlinks, permissions, file timestamps,
   additions, and deletions.
6. A mode-`0600` receipt binding snapshot, recorded repository revision,
   source, scratch target, command, exit status, file counts, missing labels,
   verification result, and known limitations.

Still owned by the operator or backup provider:

1. encryption at rest/in transit beyond SSH and access-control policy for
   Hermes secrets, private manuscripts, caches, and outputs;
2. credential provisioning, host authenticity, storage quotas, monitoring,
   and a versioned retention/deletion policy;
3. a successful receipt from the actual remote host and independent review of
   the restored files;
4. Git/source recovery and `uv sync --frozen` plus a focused pipeline from a
   restored checkout—the full helper preserves `.hermes`, repository `.cache`,
   and `output`, not the Git working tree itself;
5. creation-time content digests and at-rest tamper/corruption detection—the
   current checksum pass cannot detect bad bytes already present when restore
   begins;
6. a quiesced point-in-time source view and filesystem metadata outside rsync
   archive semantics: hard-link relationships, ACLs, extended attributes, and
   macOS resource forks are not preserved or verified.

File existence or one successful rsync exit code alone does not establish a
complete disaster-recovery system. Use an independently managed product for
controls the repository helper does not provide.

## Remote synchronization

Fetch before claiming synchronization:

```bash
git status --short --branch
git remote -v
git fetch origin
git rev-list --left-right --count HEAD...origin/main
git rev-parse HEAD
git rev-parse origin/main
```

Fetching does not merge. If local work exists, inspect overlap and preserve a
recoverable copy before integrating upstream. Prefer a fast-forward when the
history permits; do not reset or discard unrelated work to force equality.
After any push, verify the remote ref SHA independently before reporting it as
published. A local commit and a successful test run are not a push.

## Generated artifacts and public boundaries

Before staging or pushing:

```bash
uv run python scripts/audit/check_tracked_all.py
uv run python scripts/audit/check_tracked_generated_artifacts.py
uv run python scripts/audit/check_mirror_symlinks.py
uv run python scripts/audit/check_staged_secrets.py
uv run python scripts/audit/check_tracked_secrets.py
```

Only the declared public `templates/` surfaces of `projects/`, `fonds/`,
`rules/`, and `tools/` may be tracked. Runtime links under lifecycle folders
remain local-only. Regenerate public evidence through its producer; do not add
logs, `.pipeline` state, local snapshots, telemetry, caches, or build
intermediates merely because they helped diagnosis.

## Suggested cadence

Cadence is operator policy, not a claim that an automated service exists:

| Frequency | Suggested review |
| --- | --- |
| Per change | Dirty state, focused tests, docs/contracts, confidentiality, generated artifacts, secret scan. |
| Weekly or before release | Hosted CI state, dependency advisories, public project matrix, source-current render/publication audit for affected artifacts. |
| Monthly | Log-retention preview, dependency update review, disk growth, external backup restore evidence. |
| Quarterly | Supported-runtime matrix, branch-protection settings, credential inventory/expiry, archival reachability, disaster-recovery drill. |

External CI, branch protection, credentials, archive/provider state, owner
approval, tags, releases, and deposits must be recaptured at decision time.

## Disaster-recovery drill

1. Select a known snapshot in the operator's verified backup system.
2. Restore to a new scratch location.
3. Compare inventories/hashes and review secret permissions.
4. Run `uv lock --check`, `uv sync --frozen`, and a focused project pipeline.
5. Record exact passed/failed/blocked/unavailable lanes and restore time.
6. Do not promote the scratch restore over the working checkout until the owner
   reviews the comparison and preservation plan.

See the [operations runbook](runbook.md) and
[recovery procedures](troubleshooting/recovery-procedures.md).
