#!/usr/bin/env bash
# check_formal_specs.sh
#
# Thin orchestrator for the OPTIONAL formal side-spec (ISC-35/36). Runs both
# real checks -- the Lean 4 build and the TLA+ TLC model check -- and exits
# non-zero if either fails. No business logic lives here; both specs are
# self-contained under formal/lean and formal/tla.
#
# Usage:
#   scripts/check_formal_specs.sh
#
# Requires:
#   - `lake` (and `lean`) on PATH, e.g. via elan: export PATH="$HOME/.elan/bin:$PATH"
#   - a Java runtime for TLC, e.g. /opt/homebrew/opt/openjdk@17/bin/java
#     (override with FORMAL_JAVA_BIN)
#
# `tla2tools.jar` is NOT committed to this repo (a multi-MB binary has no
# place in a strongly-typed *source* template) -- this script fetches it
# on first run from a specific, dated tlaplus GitHub release tag (never
# "latest" -- a moving download target is a supply-chain risk) and caches
# it under formal/tla/ (gitignored). The fetched bytes are verified
# against a hardcoded SHA-256 before TLC is ever invoked against them; a
# mismatch deletes the file and fails loudly rather than running an
# unverified jar.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORMAL_DIR="${SCRIPT_DIR}/../formal"
LEAN_DIR="${FORMAL_DIR}/lean"
TLA_DIR="${FORMAL_DIR}/tla"
JAVA_BIN="${FORMAL_JAVA_BIN:-java}"
TLA_JAR="${TLA_DIR}/tla2tools.jar"
# Pinned to the tlaplus/tlaplus v1.8.0 release tag (verified to exist via
# `curl -sI` before pinning) -- never "latest", which is a moving,
# unverifiable download target.
TLA_JAR_URL="https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar"
# Real SHA-256 of that exact release asset, computed via `shasum -a 256`
# against a fresh download on 2026-07-08. Any byte difference (corrupted
# fetch, compromised mirror, silently republished release asset) must
# fail the build, not run an unverified jar.
TLA_JAR_SHA256="9e27b5e19a69ae1f56aabf8403a6ed5598dbfa6e638908e5278ac39736c1543d"

status=0

echo "== Lean 4: lake build (${LEAN_DIR}) =="
if ! (cd "${LEAN_DIR}" && lake build); then
  echo "FAIL: Lean build failed" >&2
  status=1
else
  echo "PASS: Lean build succeeded"
fi

echo
echo "== TLA+: TLC model check (${TLA_DIR}) =="
if ! command -v "${JAVA_BIN}" >/dev/null 2>&1; then
  echo "FAIL: java binary '${JAVA_BIN}' not found on PATH (set FORMAL_JAVA_BIN)" >&2
  status=1
else
  if [ ! -f "${TLA_JAR}" ]; then
    echo "Fetching tla2tools.jar (pinned v1.8.0) from ${TLA_JAR_URL} ..."
    if ! curl -fL --retry 3 -o "${TLA_JAR}" "${TLA_JAR_URL}"; then
      echo "FAIL: could not download tla2tools.jar" >&2
      rm -f "${TLA_JAR}"
      status=1
    fi
  fi
  # Always verify the checksum -- whether the jar was just fetched or was
  # already cached from a previous run -- so a stale/corrupted/tampered
  # cache is caught here rather than silently trusted. On mismatch, remove
  # the file (never leave an unverified jar sitting around to be reused
  # by a later invocation) and fail loudly.
  if [ "${status}" -eq 0 ]; then
    if ! echo "${TLA_JAR_SHA256}  ${TLA_JAR}" | shasum -a 256 -c -; then
      echo "FAIL: tla2tools.jar checksum mismatch (expected ${TLA_JAR_SHA256}) -- removing untrusted file" >&2
      rm -f "${TLA_JAR}"
      status=1
    else
      echo "PASS: tla2tools.jar checksum verified"
    fi
  fi
  if [ "${status}" -eq 0 ]; then
    if ! (cd "${TLA_DIR}" && "${JAVA_BIN}" -jar tla2tools.jar -config AntProtocol.cfg AntProtocol.tla); then
      echo "FAIL: TLC model check failed (AntProtocol, ideal single-peer model)" >&2
      status=1
    else
      echo "PASS: TLC model check succeeded (AntProtocol, ideal single-peer model)"
    fi
  fi
  echo
  echo "== TLA+: TLC model check, fault-injected two-peer model (${TLA_DIR}) =="
  if [ "${status}" -eq 0 ]; then
    if ! (cd "${TLA_DIR}" && "${JAVA_BIN}" -jar tla2tools.jar -config AntProtocolFaulty.cfg AntProtocolFaulty.tla); then
      echo "FAIL: TLC model check failed (AntProtocolFaulty, drop/duplicate/corrupt model)" >&2
      status=1
    else
      echo "PASS: TLC model check succeeded (AntProtocolFaulty, drop/duplicate/corrupt model)"
    fi
  fi

  # Negative control (proof-of-detection): AntProtocolFaultyNegControl.tla is
  # DELIBERATELY BROKEN (see its own header) -- an unauthenticated ForgeHello
  # action violates NoFalseEstablishment's send-provenance guarantee, and TLC
  # is EXPECTED to report that violation. Without this check, "TLC found no
  # violation in AntProtocolFaulty.tla" would say nothing about whether
  # NoFalseEstablishment can detect the vulnerability class it advertises --
  # the same reasoning tests/mypy_fixtures/bad_*.py already apply to the mypy
  # oracle. Pass/fail is INVERTED here on purpose: a reported violation is
  # PASS, a clean "no error found" result is FAIL (the negative control would
  # itself be vacuous). TLC's own exit code is not used directly (it is
  # expected to be non-zero on a genuine violation); the captured output text
  # is what is actually checked, via `|| true` so `set -e` does not abort the
  # script on that expected non-zero exit.
  echo
  echo "== TLA+: TLC model check, NEGATIVE CONTROL / proof-of-detection (${TLA_DIR}) =="
  if [ "${status}" -eq 0 ]; then
    negctl_output="$(cd "${TLA_DIR}" && "${JAVA_BIN}" -jar tla2tools.jar -config AntProtocolFaultyNegControl.cfg AntProtocolFaultyNegControl.tla 2>&1)" || true
    echo "${negctl_output}"
    if echo "${negctl_output}" | grep -q "Invariant NoFalseEstablishment is violated"; then
      echo "PASS: TLC correctly detected the injected send-provenance violation (negative control is not vacuous)"
    else
      echo "FAIL: negative control did NOT report the expected violation -- NoFalseEstablishment may be vacuous" >&2
      status=1
    fi
  fi
fi

echo
if [ "${status}" -eq 0 ]; then
  echo "check_formal_specs.sh: both formal side-specs passed"
else
  echo "check_formal_specs.sh: at least one formal side-spec FAILED" >&2
fi

exit "${status}"
