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

# Pin the installer to a specific uv release rather than the floating
# `https://astral.sh/uv/install.sh`, matching the repo's pin-everything posture
# (a floating remote script piped to a shell can change under you between runs).
# Override with `UV_INSTALL_VERSION=<x.y.z>` when a newer uv is required.
UV_INSTALL_VERSION="${UV_INSTALL_VERSION:-0.11.25}"

ensure_uv() {
    if command -v uv >/dev/null 2>&1 && uv --version >/dev/null 2>&1; then
        return 0
    fi

    local installer_url="https://astral.sh/uv/${UV_INSTALL_VERSION}/install.sh"
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf "$installer_url" | sh || return 1
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- "$installer_url" | sh || return 1
    else
        return 1
    fi

    [[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env"
    export PATH="$HOME/.local/bin:$PATH"

    command -v uv >/dev/null 2>&1
}
