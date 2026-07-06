#!/usr/bin/env bash
# Backward-compatible shim — canonical path: scripts/shell/shell_bootstrap.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/shell/shell_bootstrap.sh
source "$SCRIPT_DIR/shell/shell_bootstrap.sh"
