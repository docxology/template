# Operations Runbook

This runbook defines standard operating procedures for maintaining the Research Project Template infrastructure.

## Table of Contents

- [Daily Operations](#daily-operations)
- [Weekly Operations](#weekly-operations)
- [Monthly Operations](#monthly-operations)
- [Incident Response](#incident-response)
- [Health Check Script](#health-check-script)

---

## Daily Operations

### System Status Check

Run the pipeline help to confirm `uv`/Python resolve and the orchestrator CLI loads, or run the standalone health check for a fuller readiness signal:

```bash
./run.sh --help        # argparse usage: pipeline/multi/secure/menu/list-projects/link-projects/schema
bash scripts/shell/health-check.sh   # Python, uv, Ollama, disk space, repo structure — see Health Check Script below
```

**Expected output (`--help`):** argparse usage text listing the subcommands above; a non-zero exit or traceback means `uv`/Python/the orchestrator package is broken.
**Expected output (`health-check.sh`):** a `✅`/`⚠️`/`❌` line per check (Python, uv, Ollama, disk space, Docker, repo structure), ending `=== All checks passed ===` on success.

If Ollama is not running, start it:

```bash
ollama serve
```

### Audit Log Review

Check the daily audit logs for errors, warnings, and unusual activity. Audit logs are located in two places:

1. **Pipeline logs** — project-specific output:
   ```
   projects/*/output/logs/
   ```

2. **Hermes agent logs** (if applicable):
   ```
   ~/.hermes/logs/
   ```

**Review checklist:**
- [ ] No ERROR or CRITICAL level entries in the last 24h
- [ ] All pipeline stages completed successfully
- [ ] No repeated failures for the same project
- [ ] Disk space is stable (not rapidly decreasing)

**Quick audit review command:**

```bash
# Check for errors across all project logs from today
find projects/*/output/logs -name "*.log" -exec grep -l "ERROR\|CRITICAL" {} \; | head -20
```

---

## Weekly Operations

### Full Pipeline Run

Execute the complete pipeline across all active projects:

```bash
./run.sh --all-projects --pipeline
```

This runs:
- Infrastructure tests
- All project tests
- Analysis
- PDF rendering
- Validation

Monitor the progress and address any failures immediately. Flagged projects will appear in the console output with `❌` markers.

### Gate Duration Monitoring

Check the gate duration metrics to ensure stages are completing within acceptable time bounds. Stage gates are declared in `infrastructure/core/pipeline/pipeline.yaml` (parsed by `infrastructure/core/pipeline/dag.py`); standalone gate scripts live under `scripts/gates/`.

**Check gate timing:**

```bash
# Look for timing data in the latest logs
find projects/*/output/logs -name "*.json" -exec grep -l "\"gate\"" {} \; | xargs jq '.gate' 2>/dev/null | head -30
```

**Acceptable thresholds:**
- Stage 1 (Tests): < 60s
- Stage 2 (Analysis): < 300s
- Stage 3 (Render): < 120s
- Stage 4 (Validate): < 30s

If any gate exceeds 150% of its threshold, investigate:
- Is the project doing excessive work?
- Are dependencies up to date?
- Is there a resource bottleneck (CPU, memory, disk)?

### Security Scan Review

Run security scans and review findings:

```bash
# Run dependency vulnerability scan
uv sync --quiet && uv pip list | cut -d' ' -f1 | xargs uv pip audit 2>&1 | tee /tmp/security_scan.txt

# If you have trivy installed, scan the Docker image
trivy image template:latest 2>&1 | tee -a /tmp/security_scan.txt
```

**Review checklist:**
- [ ] No HIGH or CRITICAL vulnerabilities in dependencies
- [ ] Docker image has no critical OS package vulnerabilities
- [ ] No secrets or credentials exposed in repo (git secrets scan)

---

## Monthly Operations

### Audit Log Rotation

Rotate out old audit logs to prevent disk fill. Logs older than 30 days are archived and compressed.

**Rotation script:**

```bash
#!/usr/bin/env bash
# docs/operational/scripts/rotate-logs.sh

LOG_DIR="$HOME/.hermes/logs"
ARCHIVE_DIR="$LOG_DIR/archive"
DAYS_THRESHOLD=30

mkdir -p "$ARCHIVE_DIR"

# Find and compress logs older than 30 days
find "$LOG_DIR" -name "*.log" -type f -mtime +$DAYS_THRESHOLD -exec sh -c '
  for f; do
    gzip "$f"
    mv "${f}.gz" "$ARCHIVE_DIR/"
  done
' sh {} +

# Also rotate project logs
find . -path "*/output/logs/*.log" -type f -mtime +$DAYS_THRESHOLD -delete
```

Run the rotation:

```bash
./docs/operational/scripts/rotate-logs.sh
```

### Backup Verification

Verify that backups are current and restorable. The backup strategy uses `rsync` to mirror critical directories.

**Backup locations:**
- Source: `~/.hermes`, `.cache/`, `output/`
- Destination: defined in backup configuration (e.g., external drive or remote server)

**Verification steps:**

```bash
# 1. Check backup freshness
rsync -avun ~/.hermes/ backup:~/.hermes/ 2>&1 | grep -E "^deleting|^\.\/" | tail -5
echo "Last backup modification:"
find backup -type f -printf '%T+ %p\n' | sort -r | head -1
```

```bash
# 2. Spot-check file integrity
diff -r ~/.hermes backup:~/.hermes 2>&1 | head -20
```

```bash
# 3. Test restore of a small sample (non-disruptive)
mkdir -p /tmp/restore-test
rsync -a backup:~/.hermes/config/ /tmp/restore-test/
echo "Restore test successful: $(ls /tmp/restore-test | wc -l) files recovered"
```

**Acceptance criteria:**
- Backup age < 24h (or per your SLA)
- No files missing (diff reports 0 differences)
- Restore test recovers expected files

### Disaster Recovery Drill

Conduct a tabletop or partial recovery drill monthly to ensure procedures work.

**Drill scenario:**
- Simulate loss of `~/.hermes`
- Restore from backup to a test directory
- Start critical services (Hermes, Ollama)
- Run a smoke test: `./run.sh --project test_project --pipeline`

**Drill checklist:**
- [ ] Backup restoration completed in < 15 minutes
- [ ] All services start cleanly
- [ ] Smoke test passes
- [ ] Document any issues and update this runbook

---

## Incident Response

### Hermes Not Responding

**Symptom:** Hermes agent is unresponsive, timeouts, or returns errors.

Hermes is an external agent-skill-discovery tool this repo integrates with (see
`.agents/skills/` per template, CLAUDE.md's "Discoverable per-template skills"
section) — this repo does not ship a `template` CLI or a bundled Hermes
doctor/restart command. Diagnose and restart Hermes using its own
documentation/CLI; the steps below are limited to what this repo can inspect.

**Remediation:**

```bash
# 1. Check Hermes process status
ps aux | grep -i hermes | grep -v grep

# 2. Check Hermes' own logs (path depends on your Hermes install)
tail -50 ~/.hermes/logs/hermes.log

# 3. Restart Hermes per its own documentation, then re-verify this repo's
#    pipeline is unaffected (Hermes is not required for ./run.sh):
./run.sh --help
```

**Recovery flow:**

```mermaid
flowchart TD
    A[Hermes Unresponsive] --> B[Check process + Hermes logs]
    B --> C{Issue Identified?}
    C -->|Config Error| D[Fix Hermes configuration]
    C -->|Stale Process| E[Kill and restart via Hermes' own tooling]
    C -->|Network Issue| F[Check Network/API]
    D --> G[Restart Hermes]
    E --> G
    F --> G
    G --> H[Verify this repo is unaffected: ./run.sh --help]
    H --> I[Resolved]
```

### Port Conflicts

**Symptom:** Service fails to start due to port already in use (e.g., “Address already in use”).

**Diagnosis:**

```bash
# Identify process using the conflicting port (example: compose maps 8000:8000)
lsof -i :8000
```

**Remediation:**

```bash
# Option 1: Stop the conflicting process
kill <PID>

# Option 2: Change the port mapping in infrastructure/docker/docker-compose.yml
# Then restart from infrastructure/docker/: docker compose --profile dev up -d
```

For Docker port conflicts:

```bash
# Stop compose stacks using the project file
docker compose -f infrastructure/docker/docker-compose.yml down
docker stop $(docker ps -q --filter "publish=8000") 2>/dev/null || true
```

### Disk Full

**Symptom:** Write failures, pipeline crashes, or `No space left on device` errors.

**Immediate actions:**

```bash
# 1. Identify large directories
du -sh ~/.hermes .cache output projects/*/output 2>/dev/null | sort -rh | head -10

# 2. Clean temporary/cache files
rm -rf .cache/tmp/* .cache/downloads/*
find output -name "*.tmp" -delete

# 3. Remove old Docker artifacts
docker system prune -af --volumes

# 4. Archive and delete old logs (not yet rotated)
find . -name "*.log" -size +10M -exec gzip {} \;
```

**Prevention:** Ensure log rotation is active (see Monthly operations).

### High Gate Latency

**Symptom:** One or more pipeline stages take significantly longer than baseline.

**Diagnosis:**

```bash
# Check gate timing from recent runs
find projects -name "*.json" -exec grep -l "\"duration\"" {} \; | xargs jq -r '.stage + ": " + (.duration|tostring) + "s"' 2>/dev/null | sort -u
```

**Common causes & fixes:**

| Cause | Investigation | Fix |
|-------|---------------|-----|
| Large input data | Check project `data/` directory size | Archive unused datasets |
| Memory pressure | `htop` → swap usage | Close other apps; increase RAM |
| Slow disk I/O | `iostat` 1 5 | Move caches to SSD |
| Stale dependencies | Compare `uv.lock` age | Run `uv sync --upgrade` |
| Network timeout | Check `OLLAMA_HOST` reachable | Fix network; use local model |

**Escalation:** If latency persists > 2× baseline for 3 consecutive runs, create an incident ticket.

### LLM Provider Outage

**Symptom:** LLM-dependent stages (review, translation) fail with connection errors.

**Diagnosis:**

```bash
# Check Ollama status
ollama list
curl -s http://localhost:11434/api/tags | jq .models 2>/dev/null || echo "Ollama unreachable"
```

**Remediation:**

```bash
# Restart Ollama service
pkill ollama
ollama serve &
```

**Workaround:** Skip LLM stages and run the core pipeline instead (no other
env var disables LLM stages — `--core-only` is the supported switch):

```bash
./run.sh --core-only --project <name> --pipeline
```

Note: `FEP_LEAN_GAUSS_WORKFLOWS` (set in `run.sh`) controls the OpenGauss/Lean
session workflows, not LLM review/translation — do not use it as an LLM
on/off switch.

---

## Health Check Script

A one-liner to quickly verify system readiness:

```bash
./run.sh --help && echo "✅ OK" || echo "❌ FAIL"
```

Or as a standalone check script `scripts/shell/health-check.sh`:

```bash
#!/usr/bin/env bash
# Quick health check for CI/CD or cron

set -euo pipefail

echo "=== Health Check ==="

# 1. Python environment
python -c "import sys; print(f'Python {sys.version}')" 2>/dev/null || { echo "❌ Python missing"; exit 1; }

# 2. uv package manager
uv --version >/dev/null 2>&1 || { echo "❌ uv not found"; exit 1; }

# 3. Ollama (optional but warn)
if ! command -v ollama &>/dev/null; then
    echo "⚠️  Ollama not installed (needed for LLM stages)"
else
    echo "✅ Ollama present"
fi

# 4. Disk space (warn if < 5GB free on working dir)
FREE=$(df . | tail -1 | awk '{print $4}')
if [ "$FREE" -lt 5242880 ]; then
    echo "⚠️  Low disk space: $((FREE/1024/1024)) GB remaining"
fi

# 5. Docker (if using containerized Template)
docker --version >/dev/null 2>&1 && echo "✅ Docker available" || echo "⚠️  Docker not available"

# 6. Verify repo structure
for dir in infrastructure projects docs; do
    [ -d "$dir" ] || { echo "❌ Missing $dir"; exit 1; }
done
echo "✅ Repository structure valid"

echo "=== All checks passed ==="
```

Make it executable:

```bash
chmod +x scripts/shell/health-check.sh
```

Integrate into CI or run manually before starting work:

```bash
./scripts/shell/health-check.sh
```

---

*Last updated: 2026-04-27*
