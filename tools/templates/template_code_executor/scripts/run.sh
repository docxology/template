#!/usr/bin/env bash
# scripts/run.sh — code_executor entrypoint
# Usage:  echo '{"code": "print(42)", "language": "python"}' | bash scripts/run.sh
# Output: JSON { "exit_code": int, "stdout": string, "stderr": string }
set -euo pipefail

# ── Read input ───────────────────────────────────────────────────────────────
INPUT="$(cat)"
if [[ -z "${INPUT}" ]]; then
  echo '{"exit_code": 2, "stdout": "", "stderr": "run.sh: no input provided on stdin"}' >&2
  exit 1
fi

# ── Parse fields (requires jq) ────────────────────────────────────────────────
CODE="$(echo "${INPUT}" | jq -r '.code // empty')"
LANGUAGE="$(echo "${INPUT}" | jq -r '.language // "python"')"
TIMEOUT="$(echo "${INPUT}" | jq -r '.timeout_s // 30')"

if [[ -z "${CODE}" ]]; then
  echo '{"exit_code": 2, "stdout": "", "stderr": "run.sh: missing .code field in input JSON"}' >&2
  exit 1
fi

# ── Execute ───────────────────────────────────────────────────────────────────
TMPFILE="$(mktemp /tmp/code_executor_XXXXXX)"
echo "${CODE}" > "${TMPFILE}"

STDOUT_FILE="$(mktemp)"
STDERR_FILE="$(mktemp)"
EXIT_CODE=0

case "${LANGUAGE}" in
  python|python3)
    timeout "${TIMEOUT}" python3 "${TMPFILE}" >"${STDOUT_FILE}" 2>"${STDERR_FILE}" || EXIT_CODE=$?
    ;;
  bash|sh)
    timeout "${TIMEOUT}" bash "${TMPFILE}" >"${STDOUT_FILE}" 2>"${STDERR_FILE}" || EXIT_CODE=$?
    ;;
  *)
    echo "run.sh: unsupported language '${LANGUAGE}'" >"${STDERR_FILE}"
    EXIT_CODE=1
    ;;
esac

# ── Emit JSON result ──────────────────────────────────────────────────────────
STDOUT_CONTENT="$(cat "${STDOUT_FILE}")"
STDERR_CONTENT="$(cat "${STDERR_FILE}")"

# Clean up
rm -f "${TMPFILE}" "${STDOUT_FILE}" "${STDERR_FILE}"

jq -n \
  --argjson exit_code "${EXIT_CODE}" \
  --arg stdout "${STDOUT_CONTENT}" \
  --arg stderr "${STDERR_CONTENT}" \
  '{"exit_code": $exit_code, "stdout": $stdout, "stderr": $stderr}'
