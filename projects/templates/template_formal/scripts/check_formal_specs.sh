#!/usr/bin/env bash
# Canonical thin wrapper: exact pins, bounded groups, source custody, real TLC control.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
exec "${FORMAL_PYTHON_BIN:-python3}" -I "${PROJECT_ROOT}/src/template_formal/_tool_launcher.py" --project-root "${PROJECT_ROOT}" "$@"
