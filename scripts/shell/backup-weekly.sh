#!/usr/bin/env bash
################################################################################
# Weekly Backup Script
# Backs up the .cache directory (excluding transient tmp files).
# Intended to be run weekly via cron.
#
# Usage: ./scripts/backup-weekly.sh [remote-host]
################################################################################

set -euo pipefail

REMOTE="${1:-backup}"
DATE=$(date +%Y-%U)  # Year-Week number
LOG="/tmp/backup-weekly-${DATE}.log"

echo "Starting weekly cache backup to ${REMOTE}: week ${DATE}" | tee "${LOG}"

# Verify source exists
if [[ ! -d ".cache" ]]; then
    echo "⚠️  No .cache directory to backup — skipping" | tee -a "${LOG}"
    exit 0
fi

# rsync excluding temporary and volatile subdirectories
rsync -av --compress --progress \
    --exclude='tmp/*' \
    --exclude='downloads/tmp/*' \
    .cache/ \
    "${REMOTE}:.cache/" \
    2>&1 | tee -a "${LOG}"

SYNC_EXIT=${PIPESTATUS[0]}
if [[ ${SYNC_EXIT} -eq 0 ]]; then
    echo "✅ Weekly cache backup completed: $(date)" | tee -a "${LOG}"
    exit 0
else
    echo "❌ Backup failed with exit code ${SYNC_EXIT}" | tee -a "${LOG}"
    exit ${SYNC_EXIT}
fi
