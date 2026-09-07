#!/usr/bin/env bash
# scripts/validate.sh — validator entrypoint
# Usage:  bash scripts/validate.sh [path/to/input.json]
#         echo '{"name":"x"}' | bash scripts/validate.sh
# Output: human-readable report; exit 0 = valid, exit 1 = invalid, exit 2 = usage/engine error
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA="${SCRIPT_DIR}/schema.json"

if [[ ! -f "${SCHEMA}" ]]; then
  echo "ERROR: schema.json not found at ${SCHEMA}" >&2
  exit 2
fi

# ── Resolve a Python that can run the jsonschema validator ──────────────────
# Prefer the repository's own virtualenv (which installs `jsonschema` via
# `uv sync`), falling back to any python3 on PATH. Up four levels from
# tools/templates/<name>/scripts lands at the repository root.
REPO_VENV_PY="$(cd "${SCRIPT_DIR}" && cd ../../../.. && pwd)/.venv/bin/python"
PYTHON_BIN=""
for candidate in "${REPO_VENV_PY}" "$(command -v python3 || true)"; do
  if [[ -n "${candidate}" && -x "${candidate}" ]] && "${candidate}" -c "import jsonschema" >/dev/null 2>&1; then
    PYTHON_BIN="${candidate}"
    break
  fi
  if [[ -n "${candidate}" && -x "${candidate}" ]] && [[ -z "${PYTHON_BIN}" ]]; then
    PYTHON_BIN="${candidate}"
  fi
done

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "ERROR: no python3 interpreter found on PATH" >&2
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
# Fail CLOSED: if jsonschema is unavailable we must NOT silently fall back to a
# JSON-syntax-only check that exits 0 — a schema-invalid document would pass.
# A validation gate that degrades to "existence of a JSON blob" is worse than
# no gate at all, so we error out and ask the operator to install deps.
"${PYTHON_BIN}" - "${SCHEMA}" "${INPUT_FILE}" <<'PYEOF'
import json
import sys

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema package is not installed; cannot enforce schema.", file=sys.stderr)
    print("Install it with: uv sync  (or pip install jsonschema)", file=sys.stderr)
    sys.exit(2)

schema_path, input_path = sys.argv[1], sys.argv[2]

with open(schema_path) as sf:
    schema = json.load(sf)

with open(input_path) as df:
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
