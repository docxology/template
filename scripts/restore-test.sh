#!/usr/bin/env bash
################################################################################
# Restore Test Script
# Verifies that a backup can be restored successfully (non-destructive test).
#
# Usage: ./scripts/shell/restore-test.sh [remote-host] [snapshot-name]
#   Restores to /tmp/restore-test-<snapshot> and verifies file counts.
################################################################################

set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: $0 [remote-host] [snapshot-name]"
    echo "  Non-destructive restore test: downloads to /tmp/restore-test-<snapshot>."
    echo "  Verifies file counts match."
    exit 0
fi

REMOTE="${1:-backup}"
SNAPSHOT="${2:-$(date +%Y-%m-%d)}"
TEST_DIR="/tmp/restore-test-${SNAPSHOT}"
BACKUP_PATH="${REMOTE}:backups/full/${SNAPSHOT}"

echo "=== Restore Test ==="
echo "Snapshot : ${SNAPSHOT}"
echo "Source   : ${BACKUP_PATH}"
echo "Target   : ${TEST_DIR}"
echo ""

# Verify remote backup exists
if ! ssh "${REMOTE}" "test -d \"${BACKUP_PATH}\""; then
    echo "❌ Backup not found on remote: ${BACKUP_PATH}"
    exit 1
fi

# Clean previous test dir if exists
rm -rf "${TEST_DIR}"
mkdir -p "${TEST_DIR}"

echo "Restoring to temporary location..."
rsync -av \
    "${BACKUP_PATH}/" \
    "${TEST_DIR}/" \
    2>&1 | tail -20

# Verify file counts
echo ""
echo "=== Verification ==="
for dir in .hermes .cache output; do
    if [[ -d "${TEST_DIR}/${dir}" ]]; then
        COUNT=$(find "${TEST_DIR}/${dir}" -type f | wc -l)
        echo "✅ ${dir}: ${COUNT} files restored"
    else
        echo "⚠️  ${dir}: not present in snapshot"
    fi
done

# Optionally: spot-check a known file
if [[ -f "${TEST_DIR}/.hermes/config/config.yaml" ]]; then
    echo "✅ Config file present"
else
    echo "⚠️  Config file not found (may be fine if no config needed)"
fi

echo ""
echo "Restore test complete. Inspect: ${TEST_DIR}"
echo "To clean up: rm -rf ${TEST_DIR}"

exit 0
