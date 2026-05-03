#!/usr/bin/env bash
################################################################################
# Audit Log Rotation Script
# Rotates and compresses logs older than 30 days.
# Part of monthly maintenance procedures.
################################################################################

set -euo pipefail

LOG_DIR="${HOME}/.hermes/logs"
ARCHIVE_DIR="${LOG_DIR}/archive"
DAYS_THRESHOLD=30
PROJECT_LOG_DAYS=90

mkdir -p "${ARCHIVE_DIR}"

echo "=== Log Rotation ==="
echo "Rotating logs older than ${DAYS_THRESHOLD} days in ${LOG_DIR}"

# Rotate Hermes agent logs
if [[ -d "${LOG_DIR}" ]]; then
    find "${LOG_DIR}" -name "*.log" -type f -mtime +${DAYS_THRESHOLD} -print0 | while IFS= read -r -d '' file; do
        echo "Compressing: ${file}"
        gzip "${file}"
        mv "${file}.gz" "${ARCHIVE_DIR}/"
    done
    echo "✅ Hermes logs rotated"
else
    echo "⚠️  Log directory not found: ${LOG_DIR}"
fi

# Rotate project pipeline logs (delete old ones)
echo "Cleaning project logs older than ${PROJECT_LOG_DAYS} days"
find . -path "*/output/logs/*.log" -type f -mtime +${PROJECT_LOG_DAYS} -print0 | while IFS= read -r -d '' file; do
    echo "Deleting: ${file}"
    rm -f "${file}"
done
echo "✅ Project logs cleaned"

# Report disk savings
echo ""
echo "=== Disk Usage After Rotation ==="
du -sh "${LOG_DIR}" . 2>/dev/null | head -2

echo ""
echo "Rotation complete."
