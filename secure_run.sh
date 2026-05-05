#!/usr/bin/env bash
################################################################################
# Secure Run — Thin Shell Dispatcher
#
# Bootstrap uv, sync steganography extras, then exec the Python `secure`
# subcommand (`python -m infrastructure.orchestration secure`). PDF
# hardening flows through that orchestration path — this script never calls
# ./run.sh.
################################################################################

set -euo pipefail

export MPLCONFIGDIR="${TMPDIR:-/tmp}/matplotlib_cache"
mkdir -p "$MPLCONFIGDIR"
export UV_CACHE_DIR="${TMPDIR:-/tmp}/uv_cache"
mkdir -p "$UV_CACHE_DIR"

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

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    if ensure_uv; then
        exec uv run python -m infrastructure.orchestration secure --help
    fi
    print_uv_install_instructions
    exit 1
fi

# Strip out --deterministic before forwarding (the orchestration argparse
# does not know about it). Setting STEGANOGRAPHY_DETERMINISTIC=1 makes
# `infrastructure.steganography.config.resolve_build_timestamp` pin the
# embedded build timestamp to `git log -1 --format=%cI`, so two
# consecutive secure_run.sh invocations produce byte-identical PDFs.
FORWARD_ARGS=()
for arg in "$@"; do
    case "$arg" in
        --deterministic)
            export STEGANOGRAPHY_DETERMINISTIC=1
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

# Forward remaining args to the Python secure subcommand.
exec uv run python -m infrastructure.orchestration secure ${FORWARD_ARGS[@]+"${FORWARD_ARGS[@]}"}
