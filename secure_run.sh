#!/usr/bin/env bash
################################################################################
# Secure Run — Thin Shell Dispatcher
#
# Bootstrap uv, sync steganography extras, then exec the Python `secure`
# subcommand (`python -m infrastructure.orchestration secure`). All flags —
# including --deterministic — are owned by the Python argparse layer; this
# script only handles bootstrap and env-var parity with run.sh.
#
# Supported modes (forwarded verbatim to the Python orchestrator):
#
#   1) Full pipeline + steganography (one project)
#        ./secure_run.sh --project <name> [--core-only|--skip-infra|--resume]
#
#   2) Steganography only — re-watermark existing PDFs, no re-render
#        ./secure_run.sh --steganography-only [--project <name>]
#        (omit --project to sweep every discovered project)
#
# Run `./secure_run.sh --help` for full flag reference and examples.
################################################################################

set -euo pipefail

# Bypass macOS sandbox restrictions on ~/.matplotlib and ~/.cache/uv.
export MPLCONFIGDIR="${TMPDIR:-/tmp}/matplotlib_cache"
mkdir -p "$MPLCONFIGDIR"
export UV_CACHE_DIR="${TMPDIR:-/tmp}/uv_cache"
mkdir -p "$UV_CACHE_DIR"

# Lean session workflows: parity with run.sh. Default on; honor an existing
# value if the caller already set one. `--no-lean-workflows` below overrides.
export FEP_LEAN_GAUSS_WORKFLOWS="${FEP_LEAN_GAUSS_WORKFLOWS:-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_uv_install_instructions() {
    cat >&2 <<'EOF'
ERROR: uv is required to run secure_run.sh.

Install uv (one of):
  curl -LsSf https://astral.sh/uv/install.sh | sh
  brew install uv
  pip install uv
EOF
}

ensure_uv() {
    if command -v uv >/dev/null 2>&1 && uv --version >/dev/null 2>&1; then
        return 0
    fi
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh || return 1
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh || return 1
    else
        print_uv_install_instructions
        return 1
    fi
    [[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env"
    export PATH="$HOME/.local/bin:$PATH"
    command -v uv >/dev/null 2>&1
}

# Fast path: forward --help directly so users discover flags without paying
# for `uv sync --group steganography`.
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    if ensure_uv; then
        exec uv run python -m infrastructure.orchestration secure --help
    fi
    print_uv_install_instructions
    exit 1
fi

# Friendly hint when invoked with no args. The Python layer will still emit
# the canonical error; this just helps first-time users see usage quickly.
if [[ $# -eq 0 ]]; then
    cat >&2 <<'EOF'
secure_run.sh: no arguments given.

Quick start:
  ./secure_run.sh --project <name>             # full pipeline + steganography
  ./secure_run.sh --steganography-only         # re-watermark every project
  ./secure_run.sh --help                       # all flags and examples
EOF
    exit 2
fi

# Translate the run.sh-style `--no-lean-workflows` toggle to an env var so it
# propagates into the steganography-enabled secure pipeline. This is not
# consumed by argparse — we strip it from forwarded argv.
FORWARD_ARGS=()
for arg in "$@"; do
    case "$arg" in
        --no-lean-workflows)
            export FEP_LEAN_GAUSS_WORKFLOWS=0
            ;;
        *)
            FORWARD_ARGS+=("$arg")
            ;;
    esac
done

if ! ensure_uv; then
    print_uv_install_instructions
    exit 1
fi

# Ensure steganography deps are present before we exec into Python.
uv sync --group steganography || {
    echo "ERROR: 'uv sync --group steganography' failed" >&2
    exit 1
}

# Forward remaining args to the Python secure subcommand. argparse owns
# --project, --steganography-only, --skip-infra, --core-only, --resume,
# and --deterministic; this script no longer parses them.
exec uv run python -m infrastructure.orchestration secure ${FORWARD_ARGS[@]+"${FORWARD_ARGS[@]}"}
