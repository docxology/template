# Operations runbook

This runbook covers safe diagnosis and routine verification for the public
template checkout. It deliberately separates read-only inspection, local
environment changes, generated-output regeneration, git publication, and
external release/deposit authority.

## Operating rules

1. Read the applicable `AGENTS.md` before acting.
2. Capture the checkout before changing it: branch, upstream, revision,
   divergence, dirty paths, untracked paths, and nested repositories.
3. Preserve unrelated and user-owned work. Do not use `git reset --hard`,
   `git clean`, destructive checkout, broad recursive deletion, or an
   unreviewed restore command as incident response.
4. Treat `projects/{active,working,ongoing,archive}/` and non-template
   `fonds/`, `rules/`, and `tools/` content as local-only. Runtime discovery
   does not authorize tracking or publication.
5. Regenerate outputs from their source producers. Do not hand-edit generated
   reports, manifests, hydrated manuscripts, PDFs, or receipts to clear a gate.
6. Report `passed`, `failed`, `blocked`, `not run`, `not applicable`, and
   `unavailable` distinctly. A skipped optional tool is not a passing result.
7. Local validation does not grant merge, tag, push, release, deposit, or
   publication authority.

## Baseline capture

Run from the repository root:

```bash
git status --short --branch
git remote -v
git rev-parse HEAD
git branch --show-current
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
git submodule status --recursive
df -h .
```

If an upstream is configured, refresh remote-tracking information without
merging or overwriting local work:

```bash
git fetch origin
git rev-list --left-right --count HEAD...origin/main
git rev-parse origin/main
```

Record fetch failures as `unavailable`; do not claim remote synchronization
from local refs alone. Before pushing, re-check that the intended local SHA and
remote target are exact and that no local-only path is tracked.

## Daily checks

### CLI and repository health

Read-only command discovery:

```bash
./run.sh --help
uv run python scripts/runner/execute_pipeline.py --help
uv run python -m infrastructure.core.health --help
```

The standalone health script also runs `uv sync --quiet`, so it can update the
local environment and may require dependency/network access:

```bash
bash scripts/shell/health-check.sh
```

Its optional Ollama/Docker warnings do not fail the script. Read its individual
lines; the final exit code establishes only the checks implemented there.

### Logs and disk

Pipeline logs are project-local generated state. Inspect current paths without
assuming a hard-coded project roster:

```bash
find projects -path '*/output/logs/*.log' -type f -print
find projects -path '*/output/logs/*.log' -type f -exec tail -n 40 {} \;
du -sh output projects/*/output 2>/dev/null
df -h .
```

Hermes logs under `~/.hermes/logs/` exist only when that external tool is
installed. Their absence says nothing about this repository's pipeline.

## Change and CI-parity checks

Choose checks based on the changed surface. The hosted workflow remains the
authority for OS/Python matrices and exact job wiring.

```bash
# Static public source surface
LINT=$(uv run python -m infrastructure.project.public_scope lint-paths)
SRC=$(uv run python -m infrastructure.project.public_scope source-paths)
uv run ruff check $LINT
uv run ruff format --check $LINT
uv run python scripts/gates/mypy_ratchet.py $SRC

# Coverage-bearing Layer-1 contract
uv run python scripts/pipeline/stage_01_test.py --infra-only --infra-scope full

# One public project, isolated
uv run python scripts/pipeline/stage_01_test.py \
  --project templates/template_code_project --project-only

# Documentation and public-scope contracts
uv run python scripts/audit/lint_docs.py --quiet
uv run python scripts/audit/check_template_drift.py --strict
uv run python scripts/audit/check_tracked_all.py
uv run python scripts/audit/check_tracked_generated_artifacts.py
uv run python scripts/audit/check_mirror_symlinks.py
uv run python scripts/audit/verify_no_mocks.py
uv run python scripts/audit/verify_no_mocks.py \
  --inventory --max-dependency-replacements 0
```

The full public project matrix is expensive and runs one project per process:

```bash
uv run python scripts/pipeline/stage_01_test.py \
  --project-only --all-projects --public-projects --profile release \
  --project-workers serial
```

Do not substitute one giant `pytest projects/*/tests` process; project
`tests.conftest` packages can collide.

## Security review

Use the repository commands, not a package-list pipeline or a guessed scanner:

```bash
uv run python scripts/audit/check_staged_secrets.py
uv run python scripts/audit/check_tracked_secrets.py
uv run bandit -c bandit.yaml -r -ll infrastructure/ scripts/ projects/
uv run pip-audit --locked .
uv run python scripts/gates/security_scan.py
```

`pip-audit` needs current advisory/network data. The optional security gate can
report missing tools under `skipped_tools`; that is `skipped`, not clean. The
hosted security job's retry and ignore-file policy in
[`../../.github/workflows/ci.yml`](../../.github/workflows/ci.yml) is the exact
CI contract.

## Source-current pipeline check

For a focused canonical exemplar:

```bash
uv run python scripts/runner/execute_pipeline.py \
  --project templates/template_code_project --core-only
```

This can clean and regenerate the selected project's output. Inspect dirty and
generated paths first. A green core run establishes the implemented engineering
pipeline only; it does not by itself establish current scholarship, statistical
claim validity, semantic accessibility, owner approval, or publication.

Use `--resume` only when the checkpoint belongs to the same intended project,
inputs, configuration, and revision:

```bash
uv run python scripts/runner/execute_pipeline.py \
  --project templates/template_code_project --core-only --resume
```

If checkpoint identity is uncertain, preserve it for diagnosis and create a
fresh isolated candidate rather than deleting it in place.

## Monthly log rotation

The tracked helper is destructive for old project logs: it compresses and moves
Hermes `.log` files older than 30 days and deletes project pipeline `.log` files
older than 90 days. Preview the exact candidates first:

```bash
find "$HOME/.hermes/logs" -name '*.log' -type f -mtime +30 -print 2>/dev/null
find . -path '*/output/logs/*.log' -type f -mtime +90 -print
```

Only after confirming retention policy and backups:

```bash
bash docs/operational/scripts/rotate-logs.sh
```

See [`maintenance.md`](maintenance.md) for backup limitations and verification
requirements.

## Incident triage

### Port or process conflict

Inspect first:

```bash
lsof -nP -iTCP -sTCP:LISTEN
docker compose -f infrastructure/docker/docker-compose.yml ps
ps aux | rg '[o]llama|[h]ermes|execute_pipeline'
```

Do not kill a process until its owner, command, target project, and recoverable
state are known. Use the service's normal stop command when authorized.

### Disk pressure

Locate large consumers without deleting them:

```bash
du -sh .venv .cache output projects/*/output 2>/dev/null | sort -h
docker system df 2>/dev/null
find output projects -type f -size +100M -print 2>/dev/null
```

Move or delete only explicit, verified, regenerable targets. `docker system
prune`, cache deletion, model removal, and broad `find -delete` operations are
separate destructive actions and are not default incident steps.

### LLM capability unavailable

```bash
ollama list
curl --fail --silent --show-error http://localhost:11434/api/tags
```

If LLM stages are not required, select the supported core path:

```bash
uv run python scripts/runner/execute_pipeline.py \
  --project templates/template_code_project --core-only
```

Do not report the omitted LLM review/translation lanes as passed.

### Pipeline failure

1. Capture the exact command, revision, project, failing stable stage key/name,
   and exit code.
2. Inspect the project log and structured report.
3. Determine whether the failure is code, data, generated-evidence freshness,
   optional capability, resource exhaustion, or external authority.
4. Reproduce the smallest source-current lane without weakening a gate.
5. Preserve failed artifacts and checkpoints needed for diagnosis.

See [`troubleshooting/README.md`](troubleshooting/README.md) and
[`troubleshooting/recovery-procedures.md`](troubleshooting/recovery-procedures.md).

## Backup and restore status

The daily/weekly shell helpers require an operator-configured SSH destination.
The full-backup/restore pair now has a tested, versioned layout contract:
`backup-full.sh --dry-run` previews without connecting, backup refuses to
overwrite an existing snapshot, `restore-test.sh --list` reads without writing,
and restore uses a private control directory followed by a current
snapshot-to-copy consistency comparison and restricted receipt. It is available
as an operator-configured file
transfer helper, but it is not by itself a recovery gate: encryption,
credentials, retention, remote-host authority, Git recovery, and a
source-current pipeline remain external checks. Creation-time/at-rest integrity,
source quiescence, hard links, ACLs, and xattrs are also outside the current
contract. Details and commands are in
[`maintenance.md`](maintenance.md).

## Escalation record

For any unresolved incident, record:

- checkout path, branch, local SHA, upstream, and remote SHA if fetched;
- dirty/untracked and nested-repository state;
- exact command, environment/capability selection, exit status, and timestamps;
- affected project and canonical input/output paths;
- logs or receipt paths without secret values;
- which lanes passed, failed, were blocked, skipped, unavailable, or not run;
- the next safe action and the person or external authority required.
