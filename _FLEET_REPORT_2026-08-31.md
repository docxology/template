# Fleet Lane Report — Dr. PAI (template) — 2026-08-31

## Lane isolation context (important)

The canonical checkout (/Volumes/external_drive/Git/template, symlinked at
~/Documents/GitHub/template) had its git index repeatedly truncated and
rewritten by concurrent Hermes lanes during this window (observed
`git read-tree`/`git reset` repair loops from other sessions). To avoid
compounding that damage, this lane did all work in an isolated git worktree:

- Worktree: /Users/4d/Documents/GitHub/template-lane (admin dir under the
  shared .git; index repaired via commondir/HEAD restoration after the
  worktree add was interrupted by drive I/O)
- Branch: fleet/pai-template-20260830, reset to origin/main (c0d662cee)
- The main checkout was left exactly as found; the uncommitted work of other
  lanes (staged docs/manuscript expansion, 20fdf4180 export_bundle fix) was
  not touched, per the fleet HARD GUARD.

## Changes (committed on fleet/pai-template-20260830)

1. `cccf9844a` test(core): load-aware timeouts for Stage 01 CLI subprocess tests
   - Root cause: 7 CLI tests in tests/infra_tests/core/test_test_runner.py
     duplicated subprocess boilerplate with a 30s timeout; cold interpreter
     import of stage_01_test.py measures ~20-22s and exceeded 30s under load,
     producing order-dependent TimeoutExpired flakes (observed: suite run
     1806 passed / 1 failed; same test passed standalone).
   - Fix: single `_run_stage01()` helper with a 120s default timeout;
     assertions unchanged; tests remain real-subprocess (no mocks).

## Verification (all run in the isolated worktree with the repo venv)

- tests/infra_tests/core/ suite: 1806 passed pre-fix (1 load-flake failure),
  and the 7 touched tests: 7 passed post-fix (42.55s) — VERIFIED
- `ruff check` + `ruff format --check` on the changed file: clean — VERIFIED
- `scripts/audit/check_backlog.py --strict`: 22 stable IDs, 0 errors — VERIFIED
- `scripts/docgen/counts.py --check`: COUNTS.md OK (in sync) — VERIFIED
- `scripts/audit/check_template_drift.py --strict`: no drift — VERIFIED

## Not verified / blockers

- Full mypy and the full 9,700-test infrastructure gate: NOT VERIFIED —
  single runs take >15 min on this external-drive I/O profile and other
  lanes share the drive; targeted gates above were run instead.
- Push: attempt at end of report; network + drive conditions may extend it.
- The index churn on the main checkout is an operational hazard for any lane
  doing git work there concurrently — recommend staggering fleet lanes or
  giving each lane its own worktree (as done here).
