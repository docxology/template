#!/usr/bin/env bash
################################################################################
# Research Project Template — Thin Shell Dispatcher
#
# This file is intentionally tiny. ALL orchestration logic — menu rendering,
# pipeline coordination, project discovery, stage logging, argument parsing,
# --resume handling — lives in the Python package
# `infrastructure.orchestration`. This script's only responsibilities are:
#
#   1. Admit an explicitly prepared root Python interpreter.
#   2. Path resolution: cd to the repository root.
#   3. Supervise one native admission and forward the user's argv.
#
# The Python entry point handles --help, --pipeline, --mode, --resume,
# --project, --all-projects, the interactive menu, and everything else.
#
# Architecture: thin orchestrator pattern (see CLAUDE.md). Tests for the
# Python orchestrator live in tests/infra_tests/orchestration/.
################################################################################

set -euo pipefail

# Argv shaping array — declared before any sourced env hooks so `set -u` stays safe.
declare -a TRANSLATED

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=scripts/shell/shell_bootstrap.sh
source "$SCRIPT_DIR/scripts/shell/shell_bootstrap.sh"

setup_orchestration_sandbox_env
cd "$SCRIPT_DIR"

# OpenGauss (math-inc) Lean session workflows: default on; `--no-lean-workflows` or env overrides.
export FEP_LEAN_GAUSS_WORKFLOWS="${FEP_LEAN_GAUSS_WORKFLOWS:-1}"

# ──────────────────────────────────────────────────────────────────────────
# Argv shaping for orchestration CLI
# ──────────────────────────────────────────────────────────────────────────
#
# This shell forwards arguments to `python -m infrastructure.orchestration`,
# which uses argparse subcommands. Flat flags such as `--pipeline --mode core`
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
        --help|-h|--project|--mode|--skip-infra|--resume|--all-projects)
            TRANSLATED+=("$1")
            shift
            ;;
        --project=*|--mode=*|--skip-infra=*|--resume=*)
            TRANSLATED+=("$1")
            shift
            ;;
        *)
            TRANSLATED+=("$1")
            shift
            ;;
    esac
done

# One selected interpreter performs admission and the audited seed transition.
dispatch_prepared_root_python "$SCRIPT_DIR" ${TRANSLATED[@]+"${TRANSLATED[@]}"}
