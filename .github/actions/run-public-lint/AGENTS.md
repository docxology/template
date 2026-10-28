# `run-public-lint` — agent notes

Single source of the public Ruff/type gates. See [README.md](README.md) for the
command table and caller inputs.

## Contract

- `public_scope ci-paths` is resolved exactly once per invocation, sequentially,
  before any tool starts. Preserve producer-failure propagation: a nonzero or
  malformed producer result must exit and must not leave an empty scope for the
  gates.
- Each gate runs as a background child with its own log under
  `$RUNNER_TEMP/public-lint-logs`; the script waits for all children and exits
  non-zero if any failed. Never convert a gate to fire-and-forget.
- Commands stay check-only (`ruff check`, `ruff format --check`, `mypy`). A gate
  that rewrote files would make the required check meaningless.
- `type-check: ratchet` selects `scripts/gates/mypy_ratchet.py` for the hardening
  lane; it is the same mypy run with the repository's zero-debt wrapper. Do not
  add a third mode.
- `safety-scan: true` executes the sibling `run-safety-scan/scan.sh` rather than
  copying Bandit or no-mocks commands here.

## Editing

- Run `actionlint` after edits, keep [README.md](README.md) accurate, and check
  both callers (`workflows/ci.yml`, `workflows/hardening.yml`) still pass the
  inputs they rely on.
