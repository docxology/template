#!/usr/bin/env bash
################################################################################
# Shared shell bootstrap for run.sh and secure_run.sh
#
# Provides sandbox env setup and uv detection/install helpers. Pipeline menu,
# argparse, and stage logic live in infrastructure.orchestration — not here.
################################################################################

setup_orchestration_sandbox_env() {
    export MPLCONFIGDIR="${TMPDIR:-/tmp}/matplotlib_cache"
    mkdir -p "$MPLCONFIGDIR"
    export UV_CACHE_DIR="${TMPDIR:-/tmp}/uv_cache"
    mkdir -p "$UV_CACHE_DIR"
}

print_uv_install_instructions() {
    local script_name="${1:-run.sh}"
    cat >&2 <<EOF
ERROR: uv is required to run ${script_name}.

Install uv (one of):
  curl -LsSf https://astral.sh/uv/install.sh | sh
  brew install uv
  pip install uv

Then re-run: ./${script_name}
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
        return 1
    fi

    [[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env"
    export PATH="$HOME/.local/bin:$PATH"

    command -v uv >/dev/null 2>&1
}
