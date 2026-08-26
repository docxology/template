# Project State Report — 2026-08-26 (session 6 of the concurrent dispatches)

> Filename suffixed `session6`: at least five other concurrent dispatch
> sessions were active on this checkout today (`PROJECT_STATE_REPORT_2026-08-26*.md`,
> and live commits labeled DOC-NEGCTRL-HARDEN-MED-1 parts 1-3b). This session
> avoided every file another session held dirty or was visibly iterating on.

## State assessment

Verification order executed per `TO-DO.md`:

| Gate | Result |
| --- | --- |
| `pytest tests/regression/` | PASS - 55 passed |
| `check_backlog.py --strict` | PASS - 25 files / 24 stable IDs / 0 errors |
| `docgen/counts.py --check` | FAIL (pre-existing) - stale coverage provenance for `template_active_inference` (source hash changed; needs its 6,900s coverage re-run) |
| `check_claim_bindings.py --json` | PASS |
| `check_public_template_contract.py --strict` | PASS - 0 findings |
| `check_template_drift.py --strict` | PASS - no drift |
| `check_tracked_all.py` | PASS |
| `check_tracked_generated_artifacts.py` | PASS |
| `check_tracked_secrets.py` | PASS |
| `tests/infra_tests/validation/docs/` | 137 pass, 1 flake: `test_mermaid_lint.py::test_validate_blocks_passes_valid_diagram` timed out under load, PASSED in isolation (documented mmdc/Chrome environment sensitivity, not a regression) |

## What this session did

1. **Detector hardening - `DOC-NEGCTRL-HARDEN-MED-1`, recognizer slice**
   (`infrastructure/validation/docs/public_audit.py`, commit `008b0f0d0`):
   `_FAILS_ON_WRONG_INPUT_RE` now recognizes "the index gate fails" and
   "halt(s) and report(s) when" phrasings - both are rejection-of-known-wrong-
   input evidence that was being flagged as unbacked. Two positive tests added;
   module tests 15->17, all passing; ruff/mypy clean.
2. **Reproduced `EXECUTABLE-BUNDLE-MAJ-2` with a fresh receipt** (Docker
   `template-bundle-verify:2026-08-26` built from today's regenerated bundle,
   image id `414fe21d2037`):
   `docker run --rm --network none <image> uv run pytest /workspace/source/tests`
   fails collecting `src.benchmark_support` with `ModuleNotFoundError: No
   module named 'infrastructure'`. Confirms the backlog diagnosis on a current
   build. Contract decision remains open (vendor `infrastructure/` vs
   fail-closed compose services); implementation left unstarted because
   another concurrent session held dirty edits in
   `infrastructure/publishing/executable_bundle.py` and
   `infrastructure/rendering/dockerfile_gen.py`.
3. Ran the bounded deterministic verification order above and triaged all
   failures.

## Concurrent-session observation

Peer sessions landed prose negative-control fixes for most of the original
58 gate-negative-control findings (commits `83ce1acfd`, `62827eef8`,
`db0851419`, `d0b3d4ffa`). After my recognizer change plus their first two
prose commits the count reached 0; later probes showed ~28 residual while
their parts 3+ were still in flight. Triage of remaining sites should resume
from a quiescent tree.

## What remains

- `EXECUTABLE-BUNDLE-MAJ-2`: choose and implement the payload contract;
  acceptance = offline container run passes or exits with an explicit
  unavailable-dependency receipt.
- `EXECUTABLE-BUNDLE-MAJ-1`: attach the full offline verification receipt
  once MAJ-2 resolves.
- Stale `template_active_inference` coverage provenance blocking
  `counts.py --check` (expensive project-owned re-run).
- Residual gate-negative-control advisory findings after the peer sessions
  edits settle (were 58 at baseline; per-surface fixes, no bulk edits).
- Blocked-external rows unchanged: CLEAN-CHECKOUT-MAJ-1,
  ARCHIVAL-TRACKER-MIN-1, SECURITY-OWNERSHIP-1, SECURITY-PRIVATE-PROMOTION-1.

## Git discipline

This session made no direct pushes, resets, stashes, or CI/release edits.
Its two commits (detector + tests) are present in HEAD as `008b0f0d0`.
