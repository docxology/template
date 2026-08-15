# Recovery procedures

Recovery begins with evidence preservation. Do not delete the virtual
environment, lockfile, checkpoint, output tree, cache, or user changes merely
because a pipeline failed.

## 1. Capture the failed state

From the repository root:

```bash
git status --short --branch
git rev-parse HEAD
git remote -v
git submodule status --recursive
df -h .
ps aux | rg '[e]xecute_pipeline|[s]tage_[0-9]+|[o]llama'
find projects -path '*/output/logs/*.log' -type f -print
```

Record the exact command, selected project, stable stage key/name, exit code,
and relevant log/report paths. Do not paste secrets, the entire environment, or
private manuscript contents into an issue.

## 2. Classify the failure

| Class | Evidence | Recovery direction |
| --- | --- | --- |
| Source/test defect | Reproducible focused test failure | Fix source producer and add/retain a regression test. |
| Dependency/environment | Import or executable resolution fails before project behavior | Verify the lock and create an isolated environment before replacing the existing one. |
| Generated-evidence drift | Source/config revision differs from report, manifest, figure, or hydrated manuscript | Regenerate in producer order; never edit the generated artifact. |
| Checkpoint mismatch | Checkpoint belongs to another revision/configuration or cannot decode | Preserve it as suspect evidence and run a fresh candidate. |
| Optional capability | Tool/service is intentionally absent | Report `skipped` or `unavailable`; run only an explicitly supported reduced lane. |
| Resource exhaustion | Exit 137, disk pressure, timeout, or active producer | Inspect process, disk, and output movement before stopping or restarting. |
| External authority | Credential, owner approval, branch setting, or provider action is required | Stop at the strongest local state and name the required authority. |

## 3. Verify dependencies without deleting the current environment

First check the locked environment:

```bash
uv lock --check
uv sync --frozen
uv run python -c 'import infrastructure; print("infrastructure import OK")'
```

If the existing `.venv` is suspect, prove a clean install in a separate
temporary environment:

```bash
recovery_venv=$(mktemp -d)
UV_PROJECT_ENVIRONMENT="$recovery_venv" uv sync --frozen
UV_PROJECT_ENVIRONMENT="$recovery_venv" uv run python -c \
  'import infrastructure; print("isolated import OK")'
```

Keep the temporary path until diagnosis is complete. A successful isolated
install does not authorize deleting the original `.venv` or changing
`uv.lock`.

## 4. Re-run the smallest authoritative producer

Use a qualified project name and regenerate downstream artifacts in order:

```bash
# Project tests
uv run python scripts/pipeline/stage_01_test.py \
  --project templates/template_code_project --project-only

# Analysis producers
uv run python scripts/pipeline/stage_02_analysis.py \
  --project templates/template_code_project

# Hydrated manuscript and render
uv run python scripts/pipeline/stage_03_render.py \
  --project templates/template_code_project

# Output/provenance validation
uv run python scripts/pipeline/stage_04_validate.py \
  --project templates/template_code_project
```

Run project-specific scripts only when the project's `AGENTS.md` declares them
as canonical producers. A script exiting zero without the declared artifacts is
not recovery.

## 5. Checkpoint recovery

Use `--resume` only when the checkpoint matches the intended project, source
revision, inputs, and configuration:

```bash
uv run python scripts/runner/execute_pipeline.py \
  --project templates/template_code_project --core-only --resume
```

If a checkpoint is malformed or mismatched, do not delete it. Preserve its path
and hash, move it to a clearly named suspect location within the same generated
output tree, then run a fresh non-resume candidate. Moving or replacing a
checkpoint changes generated state and should be done only for the exact
selected project.

## 6. Git recovery boundary

Git can show the last committed version without modifying the worktree:

```bash
git diff -- <path>
git show HEAD:<path>
git ls-files --error-unmatch <path>
```

Do not run `git checkout --`, `git restore`, `git reset`, or `git clean` unless
the owner explicitly requests discarding the exact identified changes. Output
trees are often ignored or generated and may have no committed version to
restore.

## 7. Backup restore boundary

The tracked full-backup and restore-test helpers now share the versioned layout
`backups/full/<snapshot>/{.hermes,.cache,output}`. Remote shell checks use the
filesystem path without an rsync `host:` prefix. Full backup refuses to replace
an existing snapshot and serializes cooperating writers with an atomic lock.
Restore validates `.template-full-backup`, creates a private control directory,
compares the current snapshot with its restored copy, and writes a receipt
without deleting any prior restore.

```bash
# Inspect without writing, then list without restoring
bash scripts/shell/backup-full.sh --dry-run backup <snapshot>
bash scripts/shell/restore-test.sh --list backup <snapshot>

# Restore only into a generated scratch directory and verify it
bash scripts/shell/restore-test.sh backup <snapshot>
```

A successful helper receipt validates current snapshot-to-restore transfer
consistency. It is not evidence for creation-time or at-rest integrity, source
quiescence, hard links/ACLs/xattrs, encryption, retention, remote-host authority,
Git source recovery, or a source-current research pipeline. Those remain
separate gates.

For an operator-managed backup system:

1. list the exact snapshot and destination without writing;
2. restore into a newly created scratch directory, never over the checkout;
3. compare inventories, checksums, symlinks, permissions, and file timestamps;
4. run `uv sync --frozen` and a focused pipeline in the scratch checkout;
5. review the generated receipt, missing labels, and secret-handling boundaries;
6. promote restored data only after an owner reviews the comparison.

## 8. Safe diagnostic bundle

Collect versions and paths, not credentials:

```bash
python --version
uv --version
pandoc --version 2>/dev/null || true
xelatex --version 2>/dev/null || true
uv tree --depth 2
uv run pytest tests/infra_tests/ --collect-only -q
git status --short --branch
```

Before sharing, review logs and reports for tokens, home-directory paths,
private project names, unpublished manuscript content, and credentialed URLs.

## Getting help

Include:

1. a sanitized error excerpt and exact command;
2. OS, Python/uv/tool versions, checkout SHA, and project name;
3. whether the worktree was dirty before recovery;
4. the smallest reproducer;
5. explicit status for every skipped, blocked, unavailable, and unrun lane.

See [Common Errors](common-errors.md), [Environment Setup](environment-setup.md),
[Build Tools](build-tools.md), and the
[GitHub issue tracker](https://github.com/docxology/template/issues).
