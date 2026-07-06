---
name: template-shell
version: 1.0.0
description: >
  Shell helper scripts for the template research framework.
  Covers system health checks, local CI reproduction, uv bootstrap,
  and rsync backup tiers.  Scripts live at scripts/ root level.
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

## Pitfalls

- `shell_bootstrap.sh` is sourced by `run.sh` — do not alter its `export` names.
- `bash_utils.sh` is for backup/health scripts and integration tests only.
- Backup scripts assume rsync is available and the `BACKUP_DEST` env var is set.
