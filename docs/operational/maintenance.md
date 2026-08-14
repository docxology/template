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

## Backup helpers and current limitation

The shell helpers under `scripts/shell/` are site-specific examples. They
assume an SSH-configured host named `backup`, transmit potentially sensitive
Hermes/cache/output content, and do not implement encryption, retention,
credential provisioning, or provider-independent verification.

| Script | Current documentation status |
| --- | --- |
| `backup-daily.sh` | Operator-configured rsync of `~/.hermes`; not a repository release gate. |
| `backup-weekly.sh` | Operator-configured rsync of `.cache`; not a repository release gate. |
| `backup-full.sh` | **Unavailable/unverified.** Remote path and saved directory layout do not match the restore helper's expectations. |
| `restore-test.sh` | **Unavailable/unverified.** It checks a colon-qualified remote path through `ssh` and expects a layout the full backup does not reliably create. |

Do not schedule or rely on the full-backup/restore pair until those path
contracts are repaired and a disposable end-to-end restore receipt passes.
File existence or an rsync exit code alone does not establish restorability.

### Requirements for a verified replacement

1. Explicit source and destination roots with no unresolved broad variable.
2. Dry-run/list mode before writes and deletes.
3. Encryption and access-control policy for secrets/private manuscripts.
4. Versioned retention policy with recoverable deletion.
5. Restore into a newly created scratch directory, never over the checkout.
6. Inventory and hash comparison, including symlinks and permissions.
7. `uv sync --frozen` plus a focused source-current pipeline from the restored
   checkout.
8. A redacted receipt binding source revision, snapshot identity, command,
   exit status, missing paths, and limitations.

Until then, use an independently managed backup product or storage workflow
whose restore procedure has already been tested for the operator's environment.
That external system and its authority are outside this repository.

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
