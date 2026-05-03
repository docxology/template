#!/usr/bin/env bash
################################################################################
# Daily Backup Script
# Backs up critical Hermes configuration and state (~/.hermes).
# Intended to be run daily via cron.
#
# Usage: ./scripts/backup-daily.sh [remote-host]
#   remote-host defaults to 'backup' (must be SSH-configurable)
################################################################################

set -euo pipefail

REMOTE="${1:-backup}"
DATE=$(date +%Y-%m-%d)
LOG="/tmp/backup-${DATE}.log"

echo "Starting daily backup to ${REMOTE}:${DATE}" | tee "${LOG}"

# Verify source exists
if [[ ! -d "${HOME}/.hermes" ]]; then
    echo "❌ Source directory missing: ${HOME}/.hermes" | tee -a "${LOG}"
    exit 1
fi

# Perform rsync with compression and progress
rsync -av --compress --progress \
    "${HOME}/.hermes/" \
    "${REMOTE}:~/.hermes/" \
    2>&1 | tee -a "${LOG}"

# Log summary
SYNC_EXIT=${PIPESTATUS[0]}
if [[ ${SYNC_EXIT} -eq 0 ]]; then
    echo "✅ Backup completed successfully: $(date)" | tee -a "${LOG}"
    exit 0
else
    echo "❌ Backup failed with exit code ${SYNC_EXIT}" | tee -a "${LOG}"
    exit ${SYNC_EXIT}
fi
