# Maintenance Procedures

This document covers routine maintenance tasks for the Research Project Template infrastructure.

## Table of Contents

- [Log Rotation](#log-rotation)
- [Dependency Updates](#dependency-updates)
- [Database & Storage](#database--storage)
- [Backup Strategy](#backup-strategy)
- [Scheduled Maintenance Calendar](#scheduled-maintenance-calendar)

---

## Log Rotation

### Overview

The system generates logs in multiple locations:

| Log Type | Location | Retention |
|----------|----------|-----------|
| Pipeline logs | `projects/*/output/logs/` | 30 days rotated, 90 days archived |
| Hermes agent logs | `~/.hermes/logs/` | 30 days rotated, 1 year archived |
| Docker logs | `docker compose logs` | Managed by Docker daemon (configure log driver) |

### Rotation Configuration

A logrotate configuration is provided at `infrastructure/logrotate.d/hermes`:

```
~/.hermes/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    dateext
    dateformat -%Y%m%d-%s
}
```

**Installation (system-level, optional):**

```bash
sudo cp infrastructure/logrotate.d/hermes /etc/logrotate.d/
sudo logrotate -d /etc/logrotate.d/hermes  # test dry-run
```

### Manual Rotation

If system logrotate is unavailable, use the provided script:

```bash
./docs/operations/scripts/rotate-logs.sh
```

**Script behavior:**
- Compresses `.log` files older than 30 days with `gzip`
- Moves archived logs to `~/.hermes/logs/archive/`
- Deletes project logs older than 90 days
- Preserves recent logs for active debugging

### Monitoring

Ensure rotation runs successfully by checking cron logs or script output:

```bash
# View rotation logs (if script outputs to syslog or a file)
tail -20 /var/log/syslog | grep rotate-logs
```

---

## Dependency Updates

### Using `uv` for Dependency Management

The project uses `uv` as the Python package manager and resolver. All dependencies are declared in `pyproject.toml` and locked in `uv.lock`.

### Update Workflow

**1. Check for outdated packages:**

```bash
uv pip list --outdated
```

**2. Upgrade dependencies interactively or wholesale:**

```bash
# Interactive mode — review each update
uv sync --upgrade

# Non-interactive (accept all updates) — use cautiously in CI
uv sync --upgrade --no-interaction
```

**3. Regenerate lock file:**

```bash
uv lock
```

**4. Commit changes:**

```bash
git add pyproject.toml uv.lock
git commit -m "chore(deps): update dependencies via uv sync --upgrade"
```

### Pin Strategy

- Direct dependencies: flexible within major version (`package>=1.2,<2.0`)
- Transitive dependencies: pinned by `uv.lock` for reproducible builds
- Review `uv.lock` changes before merging to avoid supply-chain surprises

### Frequency

| Dependency Type | Update Cadence | Notes |
|-----------------|----------------|-------|
| Security fixes | **Immediately** | Apply via `uv sync --upgrade` as soon as CVE is disclosed |
| Minor/patch releases | Monthly (routine) | Scheduled in Monthly Maintenance |
| Major version upgrades | Quarterly | Require testing; bump version constraints |

---

## Database & Storage {#database--storage}

### Architecture Note

**There is no traditional database.** All persistent data is stored as files across three key directories:

| Directory | Purpose | Size Typical | Backup Priority |
|-----------|---------|--------------|-----------------|
| `~/.hermes/` | Hermes config, LLM cache, agent state | < 2 GB | **Critical** |
| `.cache/` | Downloaded models, intermediate data | 5–20 GB (models) | **High** |
| `output/` | Generated reports, figures, PDFs | Variable per project | **Medium** |

### Storage Health Checks

**Check filesystem integrity:**

```bash
# Verify no corrupted files (basic check — uses fsck if needed on unmounted volume)
# On macOS:
diskutil verifyVolume /Volumes/YourBackupDrive

# Check for disk errors in system logs
log show --predicate 'eventMessage contains "I/O error"' --last 7d
```

**Monitor growth trends:**

```bash
# Monthly: log directory sizes for trend analysis
du -sh ~/.hermes .cache output > docs/operations/audit/disk-usage-$(date +%Y-%m).txt
```

**Cleanup guidelines:**
- `~/.ollama/models/`: Keep only models you actively use. Remove obsolete models with `ollama rm <model>`.
- `output/figures/`: Archive old figures to cold storage; keep only current deliverables.
- `~/.hermes/chat_history/`: Periodically prune if storage constrained.

---

## Backup Strategy

### Backup Scope

| Source | Destination | Method | Frequency |
|--------|-------------|--------|-----------|
| `~/.hermes` | `backup:~/.hermes` | `rsync -a` | Daily (cron) |
| `.cache` | `backup:.cache` | `rsync -a --exclude='tmp/*'` | Weekly |
| `output` | `backup:output` | `rsync -a --delete` | After each major release |

### Backup Commands

**Daily backup script (`scripts/backup-daily.sh`):**

```bash
#!/usr/bin/env bash
set -euo pipefail

REMOTE="backup"
DATE=$(date +%Y-%m-%d)
LOG="/tmp/backup-$DATE.log"

echo "Starting daily backup ($DATE)" | tee "$LOG"

# Hermes config — critical
rsync -av --progress \
    ~/.hermes/ \
    $REMOTE:~/.hermes/ \
    2>&1 | tee -a "$LOG"

echo "Backup completed: $(date)" | tee -a "$LOG"
```

**Weekly backup (includes caches):**

```bash
rsync -av --exclude='tmp/*' \
    .cache/ \
    backup:.cache/ \
    2>&1 | tee -a /tmp/backup-weekly.log
```

**On-demand full backup:**

```bash
./scripts/backup-full.sh  # includes all three dirs with snapshots
```

### Retention & Rotation

Backups are retained according to:

| Age | Action |
|-----|--------|
| 0–7 days | Keep daily |
| 8–30 days | Keep weekly summaries |
| 31–365 days | Keep monthly snapshots |
| > 1 year | Archive to cold storage (offline HDD or S3 Glacier) |

**Prune old backups (on remote):**

```bash
# Keep last 30 days of daily backups
find /backups/daily -type f -mtime +30 -delete

# Keep last 12 monthly snapshots
find /backups/monthly -type f -mtime +365 -delete
```

### Verification

Run verification monthly (see [Runbook - Monthly Operations](#monthly-operations)).

---

## Scheduled Maintenance Calendar

| Frequency | Task | Owner | Runbook Reference |
|-----------|------|-------|-------------------|
| Daily | `./run.sh status` + audit log review | Dev on-call | [Daily](#daily-operations) |
| Daily | Health check script | CI / pre-commit | [Health Check](#health-check-script) |
| Weekly | `./run.sh all` full pipeline | Team lead | [Weekly](#weekly-operations) |
| Weekly | Gate duration monitoring | Perf engineer | [Weekly](#gate-duration-monitoring) |
| Weekly | Security scan (`uv pip audit`) | Security | [Weekly](#security-scan-review) |
| Monthly | Audit log rotation | Ops | [Log Rotation](#log-rotation) |
| Monthly | Dependency updates (`uv sync --upgrade`) | Dev team | [Dependency Updates](#dependency-updates) |
| Monthly | Backup verification + restore test | Ops | [Backup Verification](#backup-verification) |
| Quarterly | Disaster recovery drill | All hands | [Disaster Recovery Drill](#disaster-recovery-drill) |
| Yearly | Full architecture review | Architects | — |

---

## Maintenance Scripts Index

All maintenance scripts live in `scripts/` or `docs/operations/scripts/`:

| Script | Purpose | Frequency |
|--------|---------|-----------|
| `scripts/health-check.sh` | Quick system readiness check | Daily |
| `scripts/backup-daily.sh` | Daily `~/.hermes` backup | Daily (cron) |
| `scripts/backup-weekly.sh` | Weekly `.cache` backup | Weekly (cron) |
| `docs/operations/scripts/rotate-logs.sh` | Log rotation | Monthly (cron) |
| `scripts/restore-test.sh` | Validate backup restorability | Monthly |

---

## Daily Operations {#daily-operations}

For detailed procedures, see [Runbook - Daily Operations](../operations/runbook.md#daily-operations).

### Quick Reference

- Run `./run.sh status` to check system health
- Review audit logs in `projects/*/output/logs/`
- Check for ERROR or CRITICAL level entries

---

## Health Check Script {#health-check-script}

For detailed procedures and the full script, see [Runbook - Health Check Script](../operations/runbook.md#health-check-script).

### Quick Reference

```bash
./run.sh status && echo "OK" || echo "FAIL"
```

---

## Monthly Operations {#monthly-operations}

For detailed procedures, see [Runbook - Monthly Operations](../operations/runbook.md#monthly-operations).

### Quick Reference

- Audit log rotation (see [Log Rotation](#log-rotation))
- Dependency updates via `uv sync --upgrade`
- Backup verification and restore testing

---

*Last updated: 2026-04-27*
