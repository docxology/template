#!/usr/bin/env bash
################################################################################
# Secure Run — Thin Shell Dispatcher
#
# Use explicitly prepared Python and steganography dependencies for the `secure`
# subcommand (`python -m infrastructure.orchestration secure`). All flags —
# including --deterministic — are owned by the Python argparse layer; this
# script only handles bootstrap and env-var parity with run.sh.
#
# Supported modes (forwarded verbatim to the Python orchestrator):
#
#   1) Full pipeline + steganography (one project)
#        ./secure_run.sh --project <name> [--mode core|live] [--skip-infra|--resume]
#
#   2) Steganography only — re-watermark existing PDFs, no re-render
#        ./secure_run.sh --steganography-only [--project <name>]
#        (omit --project to sweep every discovered project)
#
#   3) Kmyth preflight only — validate optional TPM sealing tools
#        ./secure_run.sh --validate-kmyth [--project <name>]
#
# Run `./secure_run.sh --help` for full flag reference and examples.
################################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=scripts/shell/shell_bootstrap.sh
source "$SCRIPT_DIR/scripts/shell/shell_bootstrap.sh"

setup_orchestration_sandbox_env
cd "$SCRIPT_DIR"

# Lean session workflows: parity with run.sh. Default on; honor an existing
# value if the caller already set one. `--no-lean-workflows` below overrides.
export FEP_LEAN_GAUSS_WORKFLOWS="${FEP_LEAN_GAUSS_WORKFLOWS:-1}"

# Friendly hint when invoked with no args. The Python layer will still emit
# the canonical error; this just helps first-time users see usage quickly.
if [[ $# -eq 0 ]]; then
    cat >&2 <<'EOF'
secure_run.sh: no arguments given.

Quick start:
  ./secure_run.sh --project <name>             # full pipeline + steganography
  ./secure_run.sh --steganography-only         # re-watermark every project
  ./secure_run.sh --validate-kmyth             # validate optional Kmyth/TPM tooling
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

# Forward remaining args to the Python secure subcommand. argparse owns
# --project, --steganography-only, --skip-infra, --mode, --resume,
# --deterministic, and --validate-kmyth; this script no longer parses them.
dispatch_prepared_root_python "$SCRIPT_DIR" secure ${FORWARD_ARGS[@]+"${FORWARD_ARGS[@]}"}
