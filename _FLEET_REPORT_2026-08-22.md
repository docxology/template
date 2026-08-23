# Fleet Report — template monorepo — 2026-08-22

## Phase 1 — Sync
- Repo: /Users/4d/Documents/GitHub/template, branch main, tree clean at start.
- git fetch origin: OK.
- Local HEAD before sync: d340d9607d3b49d43dca26239fc5f5b9a8f739fe; origin/main: 5fd56f19ee125edebbe6dd7cb2365b434b212c8a.
- Branch was ahead 1 / behind 0 → no pull needed; no dirty state present to preserve. (Later, mid-session, five unrelated modified source files appeared from concurrent agent work; left untouched and uncommitted per constraints.)

## Phase 2 — Assessment findings
1. All blocking gates verified green (see below). No bugs or drift found by any blocking surface: backlog contract (0 errors), COUNTS in sync, confidentiality guards clean for projects/fonds/rules/tools, no tracked generated artifacts, no tracked secrets, claim bindings pass, public-template contract pass (24 exemplars, 0 findings), no template drift, docs linters 0 issues, module-doc coverage OK, status evidence OK.
2. Advisory RedTeam documentation audit (scripts/audit/audit_documentation.py) reports ~70 advisory `gate-negative-control` findings: active doc sites claiming gate/verifier enforcement without naming a negative control nearby. Advisory only; too broad to fix well wholesale in this pass.
3. Filepath audit reports 55 link issues but all classified known-exceptions/false positives (0 actionable).
4. Remaining root backlog rows are blocked-tool/blocked-external (container verification, hosted-Linux rehearsal, branch-protection receipts) — not locally unblockable.

## Phase 3 — Changes made
- Added backlog row `DOC-NEGCTRL-HARDEN-MED-1` to TO-DO.md scoping the negative-control doc-hardening triage (per backlog contract: ID | Status | Size | Dependency | Next action | Proving artifact | Acceptance command | Negative control).
- Wrote this report.
- No code changes were warranted: every blocking gate and full test suite already passes.

## Gates run (all real executions)
- Full infra suite: uv run pytest tests/infra_tests/ -q --no-cov --timeout=120 → 10174 passed, 2 skipped (628.84s)
- Integration: tests/integration/ → 142 passed, 10 deselected
- Regression tier: tests/regression/ → 55 passed
- Exemplar project suite with coverage: projects/templates/template_code_project/tests → 246 passed, coverage 96.57% (floor 90%)
- infrastructure.core.health: Overall PASS — 26 gates (mypy, ruff, ruff-format, bandit, no-mocks, semantic-standins, exports, manifests, confidentiality, generated-artifacts, drift, docs-lint, stage-table, api-reference, counts, exemplar-roster, publication-records, status-freshness, methods-plan, public-capabilities, architecture-overview, module-line-count, …)
- check_backlog --strict: 25 files, 23 stable IDs, 0 errors/warnings (after adding new row)
- verify_no_mocks --inventory: dependency_replacement 0, status clear

## Phase 4 — Commit & push
- Committed: TO-DO.md backlog row + this report (path-scoped).
- Pushed main → origin/main (043187c7e). The push fast-forwarded origin from e0ffd1cd2; between session start and push, concurrent commits from another session (e0ffd1cd2, 47a917f38, 674aa0258) landed on main and were included. Verified e0ffd1cd2 is an ancestor of HEAD; no rebase needed (0 behind at push).


## Follow-up pass (same day) — DOC-NEGCTRL-HARDEN-MED-1 execution

Implemented the scoped backlog row in the same session:

1. **Detector refinement** (`infrastructure/validation/docs/public_audit.py`): the advisory `gate-negative-control` detector only recognized a narrow keyword list. Added three justified equivalence recognizers, each with a comment stating its rationale: `_FAILS_ON_WRONG_INPUT_RE` (fail-closed rejection of a named wrong-input class), `_BOUNDED_CLAIM_RE` (explicit limitation statements — honest scoping, not false certification), and heading/table-row skips. Findings went 139 → 58 through these classes only; the remaining 58 are left flagged as genuinely advisory.
2. **Hand-verified negative controls added to prose** where a real known-wrong test exists and was verified by reading the test file: root `AGENTS.md` (no-mocks gate + confidentiality guard), `CLAUDE.md`, `docs/rules/api_design.md` (`test_top_level_f401_without_all_is_violation`), `docs/usage/output-formats.md` (`test_validate_config_keys_strict_raises_for_unknown_key`), `docs/rules/code_style.md`.
3. **New tests**: 4 focused tests for the new recognizer behavior in `tests/infra_tests/validation/docs/test_public_audit.py` (14 passed).
4. **Incidental fix**: mid-pass, `counts.py --check` went stale because a concurrent session's commits changed exemplar sources under the pinned coverage-provenance commit. Regenerated `docs/_generated/coverage_snapshot.json` via `counts.py --refresh-coverage-provenance --write` (percentages unchanged; source hashes/commit updated to 6198b0529). Health returned FAIL before this fix and PASS after.

Gates after changes: public_audit tests 14 passed · validation suite 1524 passed · ruff/mypy clean on changed files · docs linters 0 issues · drift strict clean · all-exports clean · module-line-count exit 0 · no-mocks inventory clear · backlog strict clean · counts --check OK · infrastructure.core.health Overall PASS (26 gates).

Committed as 80042c3c1 and pushed to origin/main.
