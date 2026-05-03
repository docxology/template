#!/usr/bin/env bash
################################################################################
# Research Project Template — Thin Shell Dispatcher
#
# This file is intentionally tiny. ALL orchestration logic — menu rendering,
# pipeline coordination, project discovery, stage logging, argument parsing,
# --resume handling — lives in the Python package
# `infrastructure.orchestration`. This script's only responsibilities are:
#
#   1. Bootstrap: locate `uv` (auto-install if missing) and the repo .venv.
#   2. Path resolution: cd to the repository root.
#   3. Exec the Python orchestrator with the user's argv.
#
# The Python entry point handles --help, --pipeline, --core-only, --resume,
# --project, --all-projects, the interactive menu, and everything else.
#
# Architecture: thin orchestrator pattern (see CLAUDE.md). Tests for the
# Python orchestrator live in tests/infra_tests/orchestration/.
################################################################################

set -euo pipefail

# Argv shaping array — declared before any sourced env hooks so `set -u` stays safe.
declare -a TRANSLATED

# Bypass macOS sandbox restrictions on ~/.matplotlib and ~/.cache/uv.
export MPLCONFIGDIR="${TMPDIR:-/tmp}/matplotlib_cache"
mkdir -p "$MPLCONFIGDIR"
export UV_CACHE_DIR="${TMPDIR:-/tmp}/uv_cache"
mkdir -p "$UV_CACHE_DIR"

# OpenGauss (math-inc) Lean session workflows: default on; `--no-lean-workflows` or env overrides.
export FEP_LEAN_GAUSS_WORKFLOWS="${FEP_LEAN_GAUSS_WORKFLOWS:-1}"

# Resolve repo root from this script's location and cd in.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ──────────────────────────────────────────────────────────────────────────
# uv detection / bootstrap
# ──────────────────────────────────────────────────────────────────────────

print_uv_install_instructions() {
    cat >&2 <<'EOF'
ERROR: uv is required to run this pipeline.

Install uv (one of):
  curl -LsSf https://astral.sh/uv/install.sh | sh
  brew install uv
  pip install uv

Then re-run: ./run.sh
EOF
}

ensure_uv() {
    if command -v uv >/dev/null 2>&1 && uv --version >/dev/null 2>&1; then
        return 0
    fi

    # Auto-install uv via Astral's official installer when absent.
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh || return 1
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh || return 1
    else
        print_uv_install_instructions
        return 1
    fi

    # Source the installer's PATH additions.
    [[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env"
    export PATH="$HOME/.local/bin:$PATH"

    command -v uv >/dev/null 2>&1
}

# Detect non-interactive / pipeline invocation early to drive `uv sync`.
PIPELINE_MODE=0
for arg in "$@"; do
    case "$arg" in
        --pipeline|--all-projects|--infra-tests|--project-tests|--render-pdf|--reviews|--translations|pipeline|multi|secure)
            PIPELINE_MODE=1
            break
            ;;
    esac
done

if ! ensure_uv; then
    print_uv_install_instructions
    exit 1
fi

# When the invocation looks pipeline-capable, create .venv deps with `uv sync` if missing.
if [[ "$PIPELINE_MODE" == "1" && ! -f "$SCRIPT_DIR/.venv/bin/python3" ]]; then
    uv sync || { echo "ERROR: 'uv sync' failed" >&2; exit 1; }
fi

# ──────────────────────────────────────────────────────────────────────────
# Argv shaping for orchestration CLI
# ──────────────────────────────────────────────────────────────────────────
#
# This shell forwards arguments to `python -m infrastructure.orchestration`,
# which uses argparse subcommands. Flat flags such as `--pipeline --core-only`
# are expanded here by prepending `pipeline` or `secure` when `--pipeline` /
# `--secure-run` appear so the Python process receives argv it already understands.

TRANSLATED=() # Clear before building argv.
SAW_PIPELINE=0
SAW_ALL_PROJECTS=0
SAW_SECURE=0

# First pass: detect mode triggers.
for arg in "$@"; do
    case "$arg" in
        --pipeline) SAW_PIPELINE=1 ;;
        --all-projects) SAW_ALL_PROJECTS=1 ;;
        --secure-run) SAW_SECURE=1 ;;
    esac
done

# Choose subcommand based on flags.
if [[ "$SAW_SECURE" == "1" ]]; then
    TRANSLATED+=("secure")
elif [[ "$SAW_PIPELINE" == "1" || "$SAW_ALL_PROJECTS" == "1" ]]; then
    TRANSLATED+=("pipeline")
fi

# Second pass: forward known flags, dropping triggers.
while [[ $# -gt 0 ]]; do
    case "$1" in
        --pipeline|--secure-run)
            shift
            ;;
        --no-lean-workflows)
            export FEP_LEAN_GAUSS_WORKFLOWS=0
            shift
            ;;
        --help|-h|--project|--core-only|--skip-infra|--skip-llm|--resume|--all-projects)
            TRANSLATED+=("$1")
            shift
            ;;
        --project=*|--core-only=*|--skip-infra=*|--resume=*)
            TRANSLATED+=("$1")
            shift
            ;;
        *)
            TRANSLATED+=("$1")
            shift
            ;;
    esac
done

# Exec the Python orchestrator. Use exec so signals propagate cleanly.
if ((${#TRANSLATED[@]} > 0)); then
    exec uv run python -m infrastructure.orchestration "${TRANSLATED[@]}"
else
    exec uv run python -m infrastructure.orchestration
fi
