#!/usr/bin/env bash
################################################################################
# Full Backup Script
# Backs up all critical directories: ~/.hermes, .cache, output
# Used for major milestones or pre-upgrade snapshots.
#
# Usage: ./scripts/shell/backup-full.sh [remote-host] [snapshot-name]
#   snapshot-name defaults to YYYY-MM-DD
################################################################################

set -euo pipefail

REMOTE="${1:-backup}"
SNAPSHOT="${2:-$(date +%Y-%m-%d)}"
LOG="/tmp/backup-full-${SNAPSHOT}.log"
BACKUP_ROOT="${REMOTE}:backups/full/${SNAPSHOT}"

echo "=== Full Backup ===" | tee "${LOG}"
echo "Snapshot : ${SNAPSHOT}" | tee -a "${LOG}"
echo "Target   : ${BACKUP_ROOT}" | tee -a "${LOG}"
echo ""

# Create remote snapshot directory
ssh "${REMOTE}" "mkdir -p \"${BACKUP_ROOT}\""

# Backup each directory with timestamped logs
for dir in "$HOME/.hermes" .cache output; do
    if [[ -d "${dir}" ]]; then
        echo "Backing up ${dir} → ${BACKUP_ROOT}/" | tee -a "${LOG}"
        rsync -av --compress --progress \
            "${dir}/" \
            "${BACKUP_ROOT}/${dir}/" \
            2>&1 | tee -a "${LOG}"
    else
        echo "⚠️  Skipping ${dir} (not found)" | tee -a "${LOG}"
    fi
done

echo ""
echo "✅ Full backup ${SNAPSHOT} completed: $(date)" | tee -a "${LOG}"
echo "To restore: ./scripts/shell/restore-test.sh ${REMOTE} ${SNAPSHOT}"

exit 0
