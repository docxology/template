#!/usr/bin/env bash
# scripts/validate.sh — model input/environment validation
# Usage:  bash scripts/validate.sh                       # environment check only
#         echo '{"hours_studied": 6.5}' | bash scripts/validate.sh   # validate a real payload
# Output: human-readable validation report; exit 0 = valid, exit 1 = invalid
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEIGHTS="${SCRIPT_DIR}/../model_weights.json"

if [[ ! -f "${WEIGHTS}" ]]; then
  echo "ERROR: model_weights.json not found at ${WEIGHTS}"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found on PATH"
  exit 1
fi

python3 -c "import json; json.load(open('${WEIGHTS}'))" || {
  echo "ERROR: model_weights.json is not valid JSON"
  exit 1
}

# If stdin has content, validate it as a real payload against the model's
# declared feature contract rather than only checking the environment.
if [[ ! -t 0 ]]; then
  INPUT="$(cat)"
  if [[ -n "${INPUT}" ]]; then
    python3 - "${WEIGHTS}" "${INPUT}" <<'PYEOF'
import json
import sys

weights_path, raw_input = sys.argv[1], sys.argv[2]
weights = json.load(open(weights_path, encoding="utf-8"))
feature_name = weights["feature_name"]

try:
    payload = json.loads(raw_input)
except json.JSONDecodeError as exc:
    print(f"INVALID — payload is not valid JSON: {exc}")
    sys.exit(1)

if not isinstance(payload, dict):
    print("INVALID — payload must be a JSON object")
    sys.exit(1)

value = payload.get(feature_name)
if value is None:
    print(f"INVALID — missing required field '{feature_name}'")
    sys.exit(1)
if not isinstance(value, (int, float)) or isinstance(value, bool):
    print(f"INVALID — field '{feature_name}' must be numeric, got {type(value).__name__}")
    sys.exit(1)

print(f"VALID — payload conforms to the model's feature contract ('{feature_name}' is numeric).")
PYEOF
    exit $?
  fi
fi

echo "VALID — environment ready (model_weights.json present and parseable, python3 available)."
