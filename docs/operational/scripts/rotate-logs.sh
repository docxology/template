#!/usr/bin/env bash
# rotate-logs.sh — Rotate and compress old Hermes + project pipeline logs.
#
# Run from repo root:
#   bash docs/operational/scripts/rotate-logs.sh

set -euo pipefail

# --- Configuration ---
HERMES_LOG_DIR="$HOME/.hermes/logs"
PROJECT_LOG_DIR="projects/*/output/logs"
DAYS_HERMES=30
DAYS_PROJECT=90
ARCHIVE_DIR="${HERMES_LOG_DIR}/archive"
# --- End Configuration ---

echo "=== Log Rotation ==="

# Ensure archive directory exists
mkdir -p "$ARCHIVE_DIR"

# Rotate Hermes logs
if [ -d "$HERMES_LOG_DIR" ]; then
    echo "Rotating Hermes logs (>$DAYS_HERMES days)..."
    find "$HERMES_LOG_DIR" -name "*.log" -type f -mtime +$DAYS_HERMES -exec sh -c '
        for f; do
            gzip "$f"
            mv "${f}.gz" "$ARCHIVE_DIR/"
            echo "  Rotated: $(basename "$f")"
        done
    ' sh {} +
    echo "Done. Archived logs in: $ARCHIVE_DIR"
else
    echo "Hermes log directory not found at $HERMES_LOG_DIR (Hermes may not be installed)"
fi

# Rotate project pipeline logs
if [ -d "projects" ]; then
    echo ""
    echo "Rotating project logs (>$DAYS_PROJECT days)..."
    find . -path "*/output/logs/*.log" -type f -mtime +$DAYS_PROJECT -delete
    echo "Done. Old project logs removed."
else
    echo "No projects/ directory found. Skipping project log rotation."
fi

echo ""
echo "=== Log rotation complete ==="