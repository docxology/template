#!/usr/bin/env bash
# The single definition of the safety scan: Bandit at MEDIUM+ severity against
# the configured allow-list, plus the lexical no-mocks policy gate.
#
# Two callers reuse this file:
#   * .github/actions/run-safety-scan/action.yml — its own composite step.
#   * .github/actions/run-public-lint/action.yml with `safety-scan: true` — the
#     ci.yml lint job runs Ruff, the type gate, and this scan in one parallel
#     wave instead of paying their runtimes serially.
#
# Each command keeps its own log, an explicit `wait`, and an aggregated exit
# status, so a backgrounded failure can never disappear.
set -euo pipefail

log_directory="${RUNNER_TEMP:-${TMPDIR:-/tmp}}/safety-scan-logs"
rm -rf -- "$log_directory"
mkdir -p "$log_directory"

case "${NO_MOCKS:-true}" in
  true | false) ;;
  *)
    echo "no-mocks must be the exact string true or false" >&2
    exit 2
    ;;
esac

read -r -a bandit_targets <<<"${BANDIT_TARGETS:-infrastructure scripts projects}"
if [[ ${#bandit_targets[@]} -eq 0 ]]; then
  echo "the safety scan requires at least one Bandit target" >&2
  exit 2
fi

names=()
pids=()

start() {
  local name="$1"
  shift
  names+=("$name")
  ( "$@" ) >"$log_directory/$name.log" 2>&1 &
  pids+=("$!")
}

start bandit uv run bandit -c bandit.yaml -r -ll "${bandit_targets[@]}"
if [[ "${NO_MOCKS:-true}" == true ]]; then
  start no-mocks uv run python scripts/audit/verify_no_mocks.py
fi

status=0
for index in "${!pids[@]}"; do
  name="${names[$index]}"
  if wait "${pids[$index]}"; then
    printf 'PASS %s\n' "$name"
  else
    printf 'FAIL %s\n' "$name"
    status=1
  fi
  printf -- '--- %s ---\n' "$name"
  cat "$log_directory/$name.log"
done
exit "$status"
