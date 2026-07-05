#!/usr/bin/env bash
# scripts/invoke.sh — skill invocation entrypoint
# Usage:  bash scripts/invoke.sh "Your prompt here"
#         echo "Your prompt here" | bash scripts/invoke.sh
# Output: LLM response text on stdout
# Exit:   0 = success, 1 = LLM error, 2 = usage error
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_TEMPLATE="${SCRIPT_DIR}/prompt.md"

# ── Read prompt ───────────────────────────────────────────────────────────────
if [[ $# -ge 1 && -n "$1" ]]; then
  USER_INPUT="$1"
else
  USER_INPUT="$(cat)"
fi

if [[ -z "${USER_INPUT}" ]]; then
  echo "ERROR: invoke.sh requires a non-empty prompt (pass as \$1 or via stdin)." >&2
  exit 2
fi

# ── Load prompt template ──────────────────────────────────────────────────────
if [[ ! -f "${PROMPT_TEMPLATE}" ]]; then
  echo "ERROR: prompt template not found at ${PROMPT_TEMPLATE}" >&2
  exit 2
fi

SYSTEM_PROMPT="$(cat "${PROMPT_TEMPLATE}")"

# ── Substitute template variables ─────────────────────────────────────────────
# Replace {{USER_INPUT}} placeholder in the system prompt
SYSTEM_PROMPT="${SYSTEM_PROMPT//\{\{USER_INPUT\}\}/${USER_INPUT}}"

# ── Call LLM API ──────────────────────────────────────────────────────────────
# Requires: OPENAI_API_KEY env var, curl, jq
: "${OPENAI_API_KEY:?ERROR: OPENAI_API_KEY environment variable is not set}"

PAYLOAD="$(jq -n \
  --arg system "${SYSTEM_PROMPT}" \
  --arg user "${USER_INPUT}" \
  '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "system", "content": $system},
      {"role": "user",   "content": $user}
    ],
    "max_tokens": 1024
  }')"

RESPONSE="$(curl -sf https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}")"

# ── Extract and emit response text ────────────────────────────────────────────
echo "${RESPONSE}" | jq -r '.choices[0].message.content // empty'
