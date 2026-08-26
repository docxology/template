# Project State Report — 2026-08-26 (session G)

Standing check-and-improve dispatch on the template monorepo (`main`, started ~11:20 PDT).
Canonical backlog per AGENTS.md is `TO-DO.md` (dispatch brief said `TODO.md`; that file
does not exist). This session contributed prose fixes to the negative-control hardening
row while three sibling sessions worked adjacent surfaces of the same row concurrently.

## State assessment at arrival

- Branch `main` (the brief's stated branch `codex/public-main-release-integrity` did not
  exist; `git status` reported main, clean, up to date — verified and proceeded on main).
- Baseline gates all green: `check_backlog.py --strict` (0 errors/warnings),
  `counts.py --check`, `pytest tests/infra_tests/documentation tests/infra_tests/publishing`
  (377+ passed; one transient failure in `test_counts_doc.py` passes standalone — known
  flaky-under-load class documented in AGENTS.md), `test_public_audit.py` 17 passed,
  drift strict clean, confidentiality guard clean, no-mocks lexical gate PASS.
- Advisory audit baseline this window: 58 → varying counts during the window because a
  sibling fleet was actively editing/committing the same docs (observed HEAD move through
  9 commits from unrelated shells mid-run).

## What this session did

1. Repaired one pre-existing corruption introduced by an earlier interrupted pass in
   root `AGENTS.md` (~line 1257–1260): duplicated/mangled sentences left interleaved by
   the prior session were restored to coherent prose.
2. Committed verified contributions under `DOC-NEGCTRL-HARDEN-MED-1`:
   - `d0b3d4ffa` — gold-refinement `src/AGENTS.md`: real negative control
     (`tests/test_pipeline_policy.py` invalid boolean → `ValueError`; gate closed without
     Ollama) plus active-inference `tests/AGENTS.md`: collect-only skip controls named
     from `tests/test_gate_support_contracts.py`, xdist constraint honestly bounded as
     convention-not-gate.
   - Prose fixes for sheaf/manuscript gates (sheaf negative controls referenced from
     `tests/gates/`, `test_track_consolidation_negative.py`), autoresearch stage-gate
     validation (`AUTORESEARCH.STAGE_UNKNOWN` evidence), gold-refinement assay
     zero-row semantics, data-descriptor provenance rows — some landed jointly with the
     sibling finalize commit `be2050ff9`.
3. Verified outcome for the shared row: final acceptance command shows **0**
   `gate-negative-control` findings (baseline 58); the row was subsequently closed in
   `TO-DO.md` by sibling commit `5a265deb4`. Controls added are real fixtures/tests I read
   before naming them — no fabricated citations; claims lacking any control got honest
   bounding language instead.

## Concurrency protocol observed

Files actively dirty under another session (e.g. `infrastructure/publishing/executable_bundle.py`,
`infrastructure/rendering/dockerfile_gen.py`, coverage snapshot) were never touched.
Commits were path-scoped; no pushes, no resets/stash/clean beyond `git reset` of my own
staged paths after pre-commit hook rollback side-effects. My own staged files only.

## Remaining work

- `EXECUTABLE-BUNDLE-MAJ-1/-2`: open; sibling session holds live WIP on the bundle/diff
  surface plus its test file. Owed next pass: offline-container verification receipt
  (`--network none`) proving either vendored `infrastructure/` or a fail-closed
  unavailable-dependency receipt (exit code 86), not a bare `ModuleNotFoundError`.
- `CLEAN-CHECKOUT-MAJ-1`, `ARCHIVAL-TRACKER-MIN-1`, `SECURITY-OWNERSHIP-1`,
  `SECURITY-PRIVATE-PROMOTION-1`: unchanged, blocked-external (hosted runners,
  administrator receipts, credentials) — not actionable locally by design.
- Housekeeping: dated session reports (this file included) are transient per repo
  convention and may be deleted by the settling pass.
