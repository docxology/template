# Check-and-Improve Lane Report — DOC-NEGCTRL Verification Slice (late pass)

Session date: 2026-08-26. This is one of several concurrent agent lanes working
the same backlog item; the canonical aggregate report remains
[`PROJECT_STATE_REPORT_2026-08-26.md`](PROJECT_STATE_REPORT_2026-08-26.md).

## State assessment

All verification-order gates were run against this checkout:

| Gate | Result |
| --- | --- |
| `check_backlog.py --strict` | pass (0 errors/warnings) |
| `docgen/counts.py --check` | OK |
| `check_claim_bindings.py` | pass (bound=15, n/a=9) |
| `check_public_template_contract.py --strict` | pass |
| `check_template_drift.py --strict` | no drift |
| `check_tracked_all.py` / tracked-artifacts / secrets | clean |
| `tests/regression/` | 55 passed |
| `tests/infra_tests/documentation/` | 360 passed, 1 failed |

The single documentation-suite failure
(`test_active_coverage_workspace_preserves_canonical_semantic_readiness`)
was traced to transient tree mutation from an interrupted pytest run in this
same session window (unrestored fixture writes left "Sensitivity complete:
False" in a sheaf certificate); it passes cleanly once restored
(`1 passed`). Root cause was a foreground-test timeout killing teardown, a
known hazard documented in `template_active_inference/tests/AGENTS.md`.

## What this lane did

- Reproduced, diagnosed, and cleared one self-inflicted contaminated-tree state
  via `git checkout --` of specific mutated paths only (never `reset/stash/clean`);
  verified the affected readiness probe passes afterward.
- Independently re-ran `audit_documentation.py` gate-negative-control triage
  mid-flight while parallel fleet sessions committed parts 1–4 of
  `DOC-NEGCTRL-HARDEN-MED-1`. This lane found 31 findings on the then-clean
  tree, confirmed several exemplar sites still lacked named negative controls,
  and applied prose fixes to 10 sites before the fleet's later parts superseded
  or reconciled them (commit `4f2b583b4` explicitly untangled a splice produced
  by two overlapping lanes).
- Final verified result shared with the fleet: **gate-negative-control
  finding count 0**, and the row is now removed from `TO-DO.md`.

## What remains (per current `TO-DO.md`)

- `EXECUTABLE-BUNDLE-MAJ-1`: full offline-container verification receipt.
- Blocked-external rows (`CLEAN-CHECKOUT-MAJ-1`, `ARCHIVAL-TRACKER-MIN-1`,
  `SECURITY-OWNERSHIP-1`, `SECURITY-PRIVATE-PROMOTION-1`) need authority or
  provider receipts outside local scope.
