#!/usr/bin/env bash
# Backward-compatible shim — canonical path: scripts/shell/ci_local.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/shell/ci_local.sh" "$@"
