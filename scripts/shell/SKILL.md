---
name: template-shell
version: 1.1.0
description: >
  Shell helper scripts for the template research framework.
  Covers system health checks, local CI reproduction, uv bootstrap,
  and rsync backup/restore contracts under scripts/shell/.
tags:
  - shell
  - bash
  - backup
  - ci
  - template
trigger: "shell scripts|bash scripts|health check|ci local|backup|restore test|shell_bootstrap"
---

# template-shell

Shell helper scripts for the template framework.

## When to use

Load this skill when you need to:
- Run the system health check before a pipeline run
- Reproduce CI locally
- Configure or run backup scripts
- Understand the shell bootstrap sourced by `run.sh`

## Key scripts

| Script | Purpose |
|--------|---------|
| `scripts/shell/health-check.sh` | Pre-flight check (Python, uv, disk, Docker, repo) |
| `scripts/shell/ci_local.sh` | Local CI reproduction |
| `scripts/shell/shell_bootstrap.sh` | uv bootstrap + sandbox env vars |
| `scripts/shell/bash_utils.sh` | Shared helpers (do not source directly in pipeline) |
| `scripts/shell/backup-daily.sh` | Site-configured daily `.hermes` rsync tier |
| `scripts/shell/backup-weekly.sh` | Site-configured weekly repository-cache rsync tier |
| `scripts/shell/backup-full.sh` | Named, metadata-bearing `.hermes`/`.cache`/`output` snapshot |
| `scripts/shell/restore-test.sh` | Private-scratch metadata and transfer-consistency verification |

## Pitfalls

- `shell_bootstrap.sh` is sourced by `run.sh` — do not alter its `export` names.
- `bash_utils.sh` is for backup/health scripts and integration tests only.
- Remote backup helpers require `rsync`, `ssh`, and an SSH alias or
  `user@hostname` positional argument (default: `backup`); they do not use a
  `BACKUP_DEST` environment variable.
- Use matching `--local-root <absolute-dir>` arguments for a disposable local
  full-backup/restore round trip. Local success does not prove off-site
  availability, creation-time integrity, encryption, retention, or source
  quiescence.
