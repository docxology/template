#!/usr/bin/env bash
# scripts/predict.sh — model inference entrypoint
# Usage:  echo '{"hours_studied": 6.5}' | bash scripts/predict.sh
# Output: JSON { "prediction": float, "feature_name": string, "target_name": string }
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEIGHTS="${SCRIPT_DIR}/../model_weights.json"

if [[ ! -f "${WEIGHTS}" ]]; then
  echo '{"error": "model_weights.json not found"}' >&2
  exit 2
fi

INPUT="$(cat)"
if [[ -z "${INPUT}" ]]; then
  echo '{"error": "predict.sh: no input provided on stdin"}' >&2
  exit 1
fi

python3 - "${WEIGHTS}" "${INPUT}" <<'PYEOF'
import json
import sys

weights_path, raw_input = sys.argv[1], sys.argv[2]

with open(weights_path, encoding="utf-8") as f:
    weights = json.load(f)

try:
    payload = json.loads(raw_input)
except json.JSONDecodeError as exc:
    print(json.dumps({"error": f"invalid JSON on stdin: {exc}"}))
    sys.exit(1)

feature_name = weights["feature_name"]
value = payload.get(feature_name)
if value is None or not isinstance(value, (int, float)):
    print(json.dumps({"error": f"expected numeric field '{feature_name}' in input JSON"}))
    sys.exit(1)

prediction = weights["intercept"] + weights["coefficient"] * value

print(json.dumps({
    "prediction": round(prediction, 4),
    "feature_name": feature_name,
    "target_name": weights["target_name"],
}))
PYEOF
