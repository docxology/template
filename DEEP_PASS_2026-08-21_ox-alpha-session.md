# Deep Pass — 2026-08-21 (ox-alpha session)

Independent deep assessment + improvement pass on this repository, executed per
`~/HermesWorkspace/instituteos_deep_pass/brief.md`. This session ran
concurrently with several sibling deep-pass sessions in the same checkout;
pre-existing and sibling-modified files were left uncommitted per the hard rules.

## Executive summary

Repository health is high. Every enforced gate this session could run passed:

| Gate | Result |
| --- | --- |
| Ruff on `public_scope lint-paths` | PASS ("All checks passed") |
| mypy on `public_scope source-paths` (1559 files) | PASS, no issues |
| No-mocks lexical gate (1189 files) | PASS |
| No-mocks semantic inventory (`--max-dependency-replacements 0`) | clear, dependency_replacement 0, total 406 |
| Tracked-resources guard (projects/fonds/rules/tools) + tracked-secrets scan | clean; no credentials |
| Template drift `--strict` | no drift |
| Skills check / check-all-exports / operations manifest | OK, 0 `__all__` violations |
| Docs mermaid lint (268 blocks) | all pass after provisioning pinned chrome-headless-shell |
| `docgen/counts.py --check`, `exemplar_roster --check`, `api_reference --check`, `status_evidence --check` | OK after refresh |
| Autoresearch infra tests | 43 passed in 9.6s |
| LLM deterministic suite (`-m "not requires_ollama"`) | 1226 passed, 51 deselected in 110.6s |
| template_code_project gate | 246 passed, coverage 96.57% (>= 90 floor) |

No security findings. The one measured defect fixed via this session is below.

## Findings

### Minor

1. **Stale generated fact: `docs/_generated/COUNTS.md` test-collection counts** —
   evidence: `uv run python scripts/docgen/counts.py --check` reported
   `STALE: docs/_generated/COUNTS.md differs from a fresh render`
   (project-scope collected count had drifted 599 -> 605).
   **Status: FIXED.** Refreshed via the canonical producer
   (`scripts/docgen/counts.py --write`); `--check` then reported OK.
   Verification: `git diff` showed exactly the two count lines changed.
   Note: the refresh was subsequently committed by a concurrent sibling deep-pass
   commit `cbc7a4679` together with that session's runbook note; this session
   makes no duplicate commit for it.

2. **Mermaid lint environment fragility** — first `lint_docs.py --mermaid-only`
   run failed with mmdc exit-124 timeouts because the puppeteer-pinned browser
   was not provisioned for this checkout's node_modules lane.
   **Status: FIXED (environment).** Ran `npx puppeteer browsers install
   chrome-headless-shell`; full mermaid lint then passed over 268 blocks. This
   is already documented in `infrastructure/validation/docs/AGENTS.md`, so no
   code change made.

3. **Apparent nondeterminism in `verify_no_mocks --inventory`** — one early run
   reported `dependency_replacement: 2 / advisory_debt`; five consecutive re-runs
   plus `--details` runs all report `dependency_replacement: 0 / Status: clear`.
   Investigation: scanner is fully deterministic (sorted uses, fixed roots,
   sorted AST walk); sys.argv redirects are correctly classified as environment
   isolation since commit `afa254ee5`. The anomalous reading coincided with
   concurrent sibling edits to public test files inside the same checkout and is
   not reproducible on a quiet tree. **Status: NO FIX REQUIRED** (no defect in
   the tool); noted here so future readers do not chase it.

### Deferred (with reasons)

4. **Full `tests/infra_tests/` suite cannot complete in this environment under
   wall-clock budget** — repeated runs hang/timeout inside long-latency real
   subprocess tests (autoresearch CLI subprocess chain when the whole suite runs
   in one process; rendering suite's `mmdc`-based `test_mermaid_figure` cases
   take 90s+ under load). Standalone slices pass: autoresearch 43 passed in
   9.6s, LLM deterministic subset 1226 passed, rendering non-CLI slice
   1150 passed / 2 skipped with one flake
   (`test_split_long_slide_frames_isolates_verbatim_and_lstlisting`) that passes
   in isolation and matches an uncommitted sibling edit to
   `_slides_framebreaks.py` — not this session's change, so left alone.
   Deferred: raising per-test timeout ceilings repo-wide is a policy change
   owned by the pipeline maintainers and risks masking real hangs; sibling
   commit `eb1612b05` is already addressing specific stale timeouts.

5. **Pre-existing/sibling-dirty working tree** — arrival dirty set
   (`infrastructure/rendering/{_pdf_latex_helpers,_slides_framebreaks,slides_renderer}.py`,
   `tests/infra_tests/rendering/test_pdf_latex_helpers.py`,
   `projects/templates/template_active_inference/output/**`) plus docs files
   regenerated mid-session by concurrent peers were neither touched nor
   committed by this session, per the hard rules.

## Major scoping

None identified by this session. The architecture, gates, confidentiality
guards, secrets hygiene, and documentation contract are consistent and enforced.
The known large-surface items (full-suite wall-time on Python 3.14 coverage
runs; per-test timeout policy) are scoped above as deferred Minor/Medium-class
work rather than architectural efforts.

## What this session verified but did not change

- Confidentiality invariant: `check_tracked_all.py` clean across all four pools.
- Secrets: `check_tracked_secrets.py` clean.
- Generated-doc gates: stage table in sync (7/7 blocks), API reference current
  (25 packages), exemplar roster synced (24), status evidence OK.
- Line-count gate: warnings only at the documented ratchet thresholds
  (`rendered_snapshot.py` 800, `full_verification.py` 929); no failures.

## Deliverable checklist

- [x] This report at repo root with classified findings + verification evidence
- [x] One Minor fix implemented and verified via the producer's own `--check`
      gate (committed upstream by sibling commit `cbc7a4679`; no duplicate)
- [x] Environment repair (chrome-headless-shell) enabling the docs lint lane
- [x] Path-scoped local commit of only this report file; no push
