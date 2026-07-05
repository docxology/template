#!/usr/bin/env bash
# scripts/validate.sh — code_executor environment validation
# Usage:  bash scripts/validate.sh
# Output: human-readable report; exit 0 = ready, exit 1 = not ready
set -euo pipefail

PASS=0
FAIL=0

check() {
  local label="$1"
  local cmd="$2"
  if eval "${cmd}" &>/dev/null; then
    echo "  [OK]  ${label}"
    PASS=$((PASS + 1))
  else
    echo "  [FAIL] ${label}"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== code_executor — environment validation ==="
echo ""
echo "Runtime checks:"
check "bash ≥ 3.2"      '[[ "${BASH_VERSINFO[0]}" -ge 3 ]]'
check "python3 present"  'command -v python3'
check "jq present"       'command -v jq'
check "timeout present"  'command -v timeout'

echo ""
echo "Manifest checks:"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${SCRIPT_DIR}/../tools.yaml"
check "tools.yaml exists"                  '[[ -f "${MANIFEST}" ]]'
check "tools.yaml has type field"          'grep -q "^type:" "${MANIFEST}"'
check "tools.yaml has entrypoints field"   'grep -q "^entrypoints:" "${MANIFEST}"'
check "run.sh is executable"               '[[ -x "${SCRIPT_DIR}/run.sh" ]]'

echo ""
echo "Results: ${PASS} passed, ${FAIL} failed."
[[ "${FAIL}" -eq 0 ]]
