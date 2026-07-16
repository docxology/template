#!/usr/bin/env bash
# Local CI reproduction — defense against GitHub Actions free-tier compression.
# See docs/maintenance/ci-local.md for the full guide.
#
# Strategy:
#   1. If `act` (nektos/act) is available + Docker is running, use it to run the
#      actual workflow YAML locally.
#   2. Otherwise, run an explicit fail-closed subset of direct CI commands.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

USAGE=$(cat <<'EOF'
Usage: scripts/shell/ci_local.sh [OPTIONS]

Reproduce CI locally to validate changes before pushing.

OPTIONS:
  -j, --job JOB        Run only the named job (forwarded to act)
      --list           List all available jobs and exit
      --dryrun         Show what would execute without running (forwarded to act)
      --no-act         Skip act even if available; use direct-command fallback
  -h, --help           Show this help

Examples:
  scripts/shell/ci_local.sh                       # Run full default workflow
  scripts/shell/ci_local.sh -j lint               # Run only the lint job
  scripts/shell/ci_local.sh -j test-infra         # Run an act workflow job
  scripts/shell/ci_local.sh --dryrun              # Show plan without running
  scripts/shell/ci_local.sh --no-act              # Force direct-command fallback

Direct-command fallback lanes (when act is unavailable):
  - lint             CI lint/type/export/generated/confidentiality/module gates
  - health           blocking static health registry
  - verify-no-mocks  lexical + zero semantic dependency-replacement policy
  - security         Bandit MEDIUM+ on the tracked public scope
  - tests            canonical template project test stage
  - precommit        all pre-commit and pre-push hooks via uv
  - confid           scripts/audit/check_tracked_all.py

The fallback is intentionally described as a subset: workflow matrices,
service containers, dependency auditing, and platform-specific jobs require act
or GitHub Actions. Unsupported fallback job names fail instead of succeeding
without running anything.
EOF
)

USE_ACT=1
JOB=""
DRY_RUN=0
LIST_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -j|--job)
      JOB="$2"
      shift 2
      ;;
    --list)
      LIST_ONLY=1
      shift
      ;;
    --dryrun|--dry-run)
      DRY_RUN=1
      shift
      ;;
    --no-act)
      USE_ACT=0
      shift
      ;;
    -h|--help)
      echo "$USAGE"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "$USAGE" >&2
      exit 2
      ;;
  esac
done

# Detect act availability
HAS_ACT=0
if [[ "$USE_ACT" -eq 1 ]] && command -v act >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    HAS_ACT=1
  else
    echo "[ci_local] act is installed but Docker is not running — falling back to direct commands." >&2
  fi
fi

# Path A: use act
if [[ "$HAS_ACT" -eq 1 ]]; then
  echo "[ci_local] Repository root: $REPO_ROOT"
  echo "[ci_local] Running via act (Docker)"
  ACT_ARGS=()

  # Avoid mutating the checkout merely by inspecting CI. A user-owned .actrc
  # still takes precedence; otherwise pass stable runner mappings explicitly.
  if [[ ! -f "$REPO_ROOT/.actrc" ]]; then
    ACT_ARGS+=("-P" "ubuntu-latest=catthehacker/ubuntu:act-latest")
    ACT_ARGS+=("-P" "ubuntu-22.04=catthehacker/ubuntu:act-22.04")
    ACT_ARGS+=("-P" "ubuntu-20.04=catthehacker/ubuntu:act-20.04")
  fi

  if [[ "$LIST_ONLY" -eq 1 ]]; then
    ACT_ARGS+=("--list")
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    ACT_ARGS+=("--dryrun")
  fi
  if [[ -n "$JOB" ]]; then
    ACT_ARGS+=("-j" "$JOB")
  fi

  exec act "${ACT_ARGS[@]}"
fi

# Path B: direct-command fallback
echo "[ci_local] Repository root: $REPO_ROOT"

if [[ "$LIST_ONLY" -eq 1 ]]; then
  cat <<'EOF'
Direct-command fallback lanes (act not available):
  - lint
  - health
  - verify-no-mocks
  - security
  - tests
  - precommit
  - confid
EOF
  exit 0
fi

if [[ -n "$JOB" ]]; then
  case "$JOB" in
    lint|health|verify-no-mocks|security|tests|precommit|confid) ;;
    *)
      echo "[ci_local] Unsupported direct-command fallback lane: $JOB" >&2
      echo "[ci_local] Use --list to see supported lanes, or run with act for workflow job IDs." >&2
      exit 2
      ;;
  esac
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  if [[ -n "$JOB" ]]; then
    echo "[ci_local] DRYRUN — would run direct-command fallback lane: $JOB"
  else
    echo "[ci_local] DRYRUN — would run direct-command fallback lanes: lint, health, verify-no-mocks, security, tests, precommit, confid"
  fi
  exit 0
fi

echo "[ci_local] act unavailable — running direct-command fallback"
echo

if [[ -z "$JOB" || "$JOB" == "lint" ]]; then
  echo "[ci_local] === CI lint job ==="
  read -r -a PUBLIC_CI_SOURCE_PATHS <<<"$(uv run python -m infrastructure.project.public_scope source-paths)"
  read -r -a PUBLIC_CI_LINT_PATHS <<<"$(uv run python -m infrastructure.project.public_scope lint-paths)"
  uv run ruff check "${PUBLIC_CI_LINT_PATHS[@]}"
  uv run ruff format --check "${PUBLIC_CI_LINT_PATHS[@]}"
  uv run python scripts/gates/mypy_ratchet.py "${PUBLIC_CI_SOURCE_PATHS[@]}"
  uv run python -m infrastructure.skills check-all-exports
  uv run python -m infrastructure.skills operations-check
  uv run python scripts/audit/check_tracked_generated_artifacts.py
  uv run python scripts/audit/check_tracked_all.py
  uv run python scripts/gates/module_line_count_check.py
fi

if [[ -z "$JOB" || "$JOB" == "health" ]]; then
  echo "[ci_local] === Blocking static health registry ==="
  uv run python -m infrastructure.core.health
fi

if [[ -z "$JOB" || "$JOB" == "verify-no-mocks" ]]; then
  echo "[ci_local] === No-mocks and semantic stand-in policy ==="
  uv run python scripts/audit/verify_no_mocks.py
  uv run python scripts/audit/verify_no_mocks.py --inventory --max-dependency-replacements 0
fi

if [[ -z "$JOB" || "$JOB" == "security" ]]; then
  echo "[ci_local] === Bandit MEDIUM+ (public scope; dependency audit remains act-only) ==="
  read -r -a PUBLIC_PROJECTS <<<"$(uv run python -m infrastructure.project.public_scope project-names)"
  SECURITY_TARGETS=(infrastructure/ scripts/)
  for project in "${PUBLIC_PROJECTS[@]}"; do
    SECURITY_TARGETS+=("projects/$project/")
  done
  uv run bandit -c bandit.yaml -r -ll "${SECURITY_TARGETS[@]}"
fi

if [[ -z "$JOB" || "$JOB" == "tests" ]]; then
  echo "[ci_local] === Canonical project test stage (matrix remains act-only) ==="
  PROJECT="${TEMPLATE_CI_PROJECT:-templates/template_code_project}"
  uv run python scripts/pipeline/stage_01_test.py --project "$PROJECT"
fi

if [[ -z "$JOB" || "$JOB" == "precommit" ]]; then
  echo "[ci_local] === Pre-commit (all stages) ==="
  uv run pre-commit run --all-files
  uv run pre-commit run --hook-stage pre-push --all-files
fi

if [[ -z "$JOB" || "$JOB" == "confid" ]]; then
  echo "[ci_local] === Confidentiality check ==="
  uv run python scripts/audit/check_tracked_all.py
fi

echo
echo "[ci_local] All requested direct-command checks passed."
