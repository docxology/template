#!/usr/bin/env bash
# Local CI reproduction — defense against GitHub Actions free-tier compression.
# See docs/maintenance/ci-local.md for the full guide.
#
# Strategy:
#   1. If `act` (nektos/act) is available + Docker is running, use it to run the
#      actual workflow YAML locally.
#   2. Otherwise, fall back to a pure-Python reproduction of the major CI checks.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

USAGE=$(cat <<'EOF'
Usage: scripts/shell/ci_local.sh [OPTIONS]

Reproduce CI locally to validate changes before pushing.

OPTIONS:
  -j, --job JOB        Run only the named job (forwarded to act)
      --list           List all available jobs and exit
      --dryrun         Show what would execute without running (forwarded to act)
      --no-act         Skip act even if available; use pure-Python fallback
  -h, --help           Show this help

Examples:
  scripts/shell/ci_local.sh                       # Run full default workflow
  scripts/shell/ci_local.sh -j lint               # Run only the lint job
  scripts/shell/ci_local.sh -j tests-ubuntu-py311 # Run only one matrix entry
  scripts/shell/ci_local.sh --dryrun              # Show plan without running
  scripts/shell/ci_local.sh --no-act              # Force pure-Python fallback

Pure-Python fallback (when act unavailable) runs:
  - ruff check + format
  - mypy (strict on public CI source scope)
  - bandit security scan
  - infra + project pytest with coverage gates
  - pre-commit hooks (all stages, including pre-push)
  - confidentiality check (scripts/audit/check_tracked_projects.py)
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
    echo "[ci_local] act is installed but Docker is not running — falling back to pure-Python reproduction." >&2
  fi
fi

# Ensure .actrc exists with sensible defaults if act is available
if [[ "$HAS_ACT" -eq 1 ]] && [[ ! -f "$REPO_ROOT/.actrc" ]]; then
  cat >"$REPO_ROOT/.actrc" <<'ACTRC'
# Use medium-sized Linux runner images (closer to GH Actions ubuntu-latest)
-P ubuntu-latest=catthehacker/ubuntu:act-latest
-P ubuntu-22.04=catthehacker/ubuntu:act-22.04
-P ubuntu-20.04=catthehacker/ubuntu:act-20.04
ACTRC
  echo "[ci_local] Created default .actrc"
fi

# Path A: use act
if [[ "$HAS_ACT" -eq 1 ]]; then
  echo "[ci_local] Running via act (Docker)"
  ACT_ARGS=()

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

# Path B: pure-Python fallback
if [[ "$LIST_ONLY" -eq 1 ]]; then
  cat <<'EOF'
Pure-Python fallback available steps (act not available):
  - lint        (ruff check + format)
  - typecheck   (mypy strict)
  - security    (bandit)
  - tests       (infra + project pytest with coverage)
  - precommit   (all pre-commit stages including pre-push)
  - confid      (scripts/audit/check_tracked_projects.py)
EOF
  exit 0
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[ci_local] DRYRUN — would run pure-Python fallback (lint, typecheck, security, tests, precommit, confid)"
  exit 0
fi

echo "[ci_local] act unavailable — running pure-Python fallback"
echo

if [[ -z "$JOB" || "$JOB" == "lint" || "$JOB" == "typecheck" ]]; then
  read -r -a PUBLIC_CI_SOURCE_PATHS <<<"$(uv run python -m infrastructure.project.public_scope source-paths)"
  read -r -a PUBLIC_CI_LINT_PATHS <<<"$(uv run python -m infrastructure.project.public_scope lint-paths)"
fi

if [[ -z "$JOB" || "$JOB" == "lint" ]]; then
  echo "[ci_local] === Lint (ruff check + format) ==="
  uvx ruff check --fix "${PUBLIC_CI_LINT_PATHS[@]}"
  uvx ruff format "${PUBLIC_CI_LINT_PATHS[@]}"
fi

if [[ -z "$JOB" || "$JOB" == "typecheck" ]]; then
  echo "[ci_local] === Type check (mypy) ==="
  uv run mypy "${PUBLIC_CI_SOURCE_PATHS[@]}"
fi

if [[ -z "$JOB" || "$JOB" == "security" ]]; then
  echo "[ci_local] === Security scan (bandit) ==="
  uv run bandit -c bandit.yaml -r -ll infrastructure/ scripts/ projects/
fi

if [[ -z "$JOB" || "$JOB" == "tests" ]]; then
  echo "[ci_local] === Tests (infra + project) ==="
  # Try template_code_project first; user can override via $TEMPLATE_CI_PROJECT
  PROJECT="${TEMPLATE_CI_PROJECT:-template_code_project}"
  uv run python scripts/pipeline/stage_01_test.py --project "$PROJECT"
fi

if [[ -z "$JOB" || "$JOB" == "precommit" ]]; then
  echo "[ci_local] === Pre-commit (all stages) ==="
  if command -v pre-commit >/dev/null 2>&1; then
    pre-commit run --all-files
    pre-commit run --hook-stage pre-push --all-files
  else
    echo "[ci_local] pre-commit not installed; skip. Install: uv pip install pre-commit"
  fi
fi

if [[ -z "$JOB" || "$JOB" == "confid" ]]; then
  echo "[ci_local] === Confidentiality check ==="
  uv run python scripts/audit/check_tracked_projects.py
fi

echo
echo "[ci_local] All requested checks complete."
