#!/usr/bin/env bash
# Backward-compatible shim — canonical path: scripts/shell/bash_utils.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/shell/bash_utils.sh
source "$SCRIPT_DIR/shell/bash_utils.sh"
