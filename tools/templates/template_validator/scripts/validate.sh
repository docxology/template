#!/usr/bin/env bash
# scripts/validate.sh — validator entrypoint
# Usage:  bash scripts/validate.sh [path/to/input.json]
#         echo '{"name":"x"}' | bash scripts/validate.sh
# Output: human-readable report; exit 0 = valid, exit 1 = invalid, exit 2 = usage error
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA="${SCRIPT_DIR}/schema.json"

if [[ ! -f "${SCHEMA}" ]]; then
  echo "ERROR: schema.json not found at ${SCHEMA}" >&2
  exit 2
fi

# ── Read input ────────────────────────────────────────────────────────────────
if [[ $# -ge 1 && -f "$1" ]]; then
  INPUT_FILE="$1"
else
  TMP="$(mktemp)"
  cat > "${TMP}"
  INPUT_FILE="${TMP}"
  trap 'rm -f "${TMP}"' EXIT
fi

if [[ ! -s "${INPUT_FILE}" ]]; then
  echo "ERROR: empty or missing input." >&2
  exit 2
fi

# ── Validate with Python jsonschema ──────────────────────────────────────────
python3 - <<PYEOF
import json, sys

try:
    import jsonschema
except ImportError:
    # Fallback: basic JSON parse only
    with open("${INPUT_FILE}") as f:
        try:
            json.load(f)
            print("WARNING: jsonschema not installed; only JSON syntax was checked.")
            sys.exit(0)
        except json.JSONDecodeError as e:
            print(f"INVALID JSON: {e}")
            sys.exit(1)

with open("${SCHEMA}") as sf:
    schema = json.load(sf)

with open("${INPUT_FILE}") as df:
    try:
        data = json.load(df)
    except json.JSONDecodeError as e:
        print(f"INVALID JSON: {e}")
        sys.exit(1)

validator = jsonschema.Draft7Validator(schema)
errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))

if errors:
    print(f"INVALID — {len(errors)} error(s):")
    for err in errors:
        path = " > ".join(str(p) for p in err.absolute_path) or "(root)"
        print(f"  [{path}] {err.message}")
    sys.exit(1)
else:
    print("VALID — input conforms to schema.")
    sys.exit(0)
PYEOF
