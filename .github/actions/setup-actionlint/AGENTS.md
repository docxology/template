# `setup-actionlint` — agent notes

Single source of the `actionlint` pin, installer verification, and run. See
[README.md](README.md) for the callers and constants.

## Contract

- `ACTIONLINT_REF` (release commit), `ACTIONLINT_VERSION` (rendered release), and
  `ACTIONLINT_SCRIPT_SHA256` (digest of `scripts/download-actionlint.bash`) are
  one pin. Bump them together; never fetch a moving branch or skip the digest.
- The script uses `sha256sum --check --status` and only then executes the
  installer, so a tampered or partial download fails before it runs.
- Both workflows call this action; do not re-inline the curl/sha256 block in a
  workflow, and do not add inputs that let a caller skip verification.
- `actionlint -color` runs over the whole repository workflow set from the
  checked-out workspace; keep the gate whole-repository rather than path-scoped.

## Editing

- Verify the digest against the release commit when bumping, then run the action
  (or `actionlint` locally) and keep the documentation pair current.
