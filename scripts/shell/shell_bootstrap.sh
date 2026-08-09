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
  curl -fsSL https://astral.sh/uv/0.12.0/install.sh -o uv-install.sh
  echo 'b67e385074fddc9b99cd152b838fd91046d9fbc261b2c45f448a983ad23b8764  uv-install.sh' | shasum -a 256 -c -
  sh uv-install.sh && rm uv-install.sh
  brew install uv
  pip install uv

Then re-run: ./${script_name}
EOF
}

# Pin the installer to a specific uv release rather than the floating endpoint,
# matching the repo's pin-everything posture (a floating remote script piped to
# a shell can change under you between runs).
# Override with `UV_INSTALL_VERSION=<x.y.z>` and the matching
# `UV_INSTALL_SHA256=<sha256>` when a newer uv is required.
UV_INSTALL_VERSION="${UV_INSTALL_VERSION:-0.12.0}"
UV_INSTALL_SHA256="${UV_INSTALL_SHA256:-}"

ensure_uv() {
    if command -v uv >/dev/null 2>&1 && uv --version >/dev/null 2>&1; then
        return 0
    fi

    if [[ "$UV_INSTALL_VERSION" == "0.12.0" && -z "$UV_INSTALL_SHA256" ]]; then
        UV_INSTALL_SHA256="b67e385074fddc9b99cd152b838fd91046d9fbc261b2c45f448a983ad23b8764"
    elif [[ -z "$UV_INSTALL_SHA256" ]]; then
        echo "Cannot verify uv ${UV_INSTALL_VERSION}: set UV_INSTALL_SHA256 to the official installer digest." >&2
        return 1
    fi

    local installer_url="https://astral.sh/uv/${UV_INSTALL_VERSION}/install.sh"
    local installer_file
    installer_file="$(mktemp "${TMPDIR:-/tmp}/uv-install.XXXXXX")" || return 1
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$installer_url" -o "$installer_file" || { rm -f "$installer_file"; return 1; }
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$installer_file" "$installer_url" || { rm -f "$installer_file"; return 1; }
    else
        rm -f "$installer_file"
        return 1
    fi

    local actual_sha256
    if command -v shasum >/dev/null 2>&1; then
        actual_sha256="$(shasum -a 256 "$installer_file" | awk '{print $1}')"
    elif command -v sha256sum >/dev/null 2>&1; then
        actual_sha256="$(sha256sum "$installer_file" | awk '{print $1}')"
    else
        rm -f "$installer_file"
        return 1
    fi
    if [[ "$actual_sha256" != "$UV_INSTALL_SHA256" ]]; then
        rm -f "$installer_file"
        return 1
    fi
    sh "$installer_file" || { rm -f "$installer_file"; return 1; }
    rm -f "$installer_file"

    [[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env"
    export PATH="$HOME/.local/bin:$PATH"

    command -v uv >/dev/null 2>&1
}
