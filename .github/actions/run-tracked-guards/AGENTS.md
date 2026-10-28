# `run-tracked-guards` — agent notes

Single source of the tracked-tree guards. See [README.md](README.md) for the
command table.

## Contract

- Exactly three commands, in order: `check_tracked_all.py`,
  `check_tracked_secrets.py`, `check_tracked_generated_artifacts.py`. Both
  workflows rely on this set; a fourth check that only one lane needs stays in
  that lane.
- The guards stay sequential and blocking. Do not background them into the
  `run-public-lint` wave: their failures name the offending paths and must not
  interleave.
- `set -euo pipefail` stays explicit so a missing script is a failure, not a
  silent pass.

## Editing

- Run `actionlint` after edits, keep [README.md](README.md) accurate, and verify
  both callers still resolve the action after checkout.
