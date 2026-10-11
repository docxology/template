#!/usr/bin/env bash
# Thin entrypoint for the bundled standard-library process supervisor.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${TEMPLATE_PYTHON:-python3}" -I "${SCRIPT_DIR}/../src/code_executor.py"
