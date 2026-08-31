# Review Log — agent-ergonomics pass, 2026-08-31 (fleet lane: template)

## Phase 0 — Preflight
- Branch: `main`; remote: github.com/docxology/template (origin). Dirty files at dispatch: 140 (pre-existing, treated as read-only).
- `git fetch origin` timed out at 300s on the external drive — not retried; push attempted directly at Phase 4.
- Inventory: entry docs README.md / AGENTS.md / CLAUDE.md / .cursorrules; status = STATUS.md (verification ledger); backlog = TO-DO.md (stable-ID contract); generated facts in docs/_generated/.

## Phase 1 — Cold-start audit
Orientation ladder (docs only): (a) status PASS via README->STATUS.md; (b) next actions PASS via README->TO-DO.md; (c) verification PASS via TO-DO.md "Verification order".
Link check (scripted, relative links in README/AGENTS/CLAUDE/TO-DO/STATUS): 0 broken.
Gates run: check_backlog --strict OK (22 IDs); status_evidence --check OK; counts.py --check FAIL (stale coverage provenance — known recurring post-measurement staleness, cf. commits 1dd67aee8/15045e302).
Findings: Minor — STATUS.md/TO-DO.md not one hop from README quickstart (signpost placement). No duplicated fact-classes without canonical home. No transient reports linked from tracked docs.

## Phase 2 — Backlog scoping
TO-DO.md rows added: AGENT-ERG-README-SIGNPOST-MIN-1 (Minor); AGENT-ERG-COUNTS-PROVENANCE-MED-1 (Medium).

## Phase 3 — Implementation
- README.md: "Current state & next actions" signpost linking STATUS.md + TO-DO.md.
- TO-DO.md: two new rows.
- counts.py --refresh-coverage-provenance --write attempted; killed at 420s tool timeout mid-write, truncating .git/index. Recovery below.

## Incident log — git index corruption & recovery (2026-08-31 12:38–12:50 PDT)
- .git/index truncated to 0 bytes by the process kill during index write on the external drive.
- Recovery: fresh index built on local disk via GIT_INDEX_FILE=/tmp/tpl_idx git read-tree HEAD (1,117,887 bytes, validated by git write-tree), copied to .git/index. Working tree untouched.
- Standing limitation reproduced: full-tree git status/diff on this volume stalls >300s (matches daf-dirty-watch cron finding). Targeted single-path git ops used instead.

## Phase 4 — Verify & close
- See fleet report for commit/push outcome and post-edit link check.

## Lane addendum — START_HERE.md lane (2026-08-31 ~12:30-13:00)
- START_HERE.md: added "Agent orientation ladder" (what this is / current state via STATUS.md / next via TO-DO.md / verify via CLAUDE.md + docs/AGENTS.md). Cited gates verified live: `scripts/docgen/status_evidence.py --check` OK; `scripts/audit/check_backlog.py --strict` OK (29 IDs).
- TO-DO.md rows: DOC-STARTHERE-LINT-TIMEOUT-MED-1 (closed same session by sibling lane's `--paths` lint mode; scoped lint verified green on README/START_HERE/TO-DO: 0 broken links, exit 0), DOC-ROOT-SCRATCH-HYGIENE-MIN-1 (open — needs owner confirmation before archiving root sidecar_*/AUDIT scratch).
- Incident: .git/index zeroed 12:38 by a sibling lane's killed counts.py run; all git ops failed until sibling rebuilt index 12:52. No worktree files damaged; edits recovered intact.
- Scope disclosure: commits path-limited to START_HERE.md, TO-DO.md, REVIEW_LOG_2026-08-31.md only.

## Fourth lane pass - 2026-08-31 (scoped docs-lint mode; closes DOC-STARTHERE-LINT-TIMEOUT-MED-1)

Preflight: branch main, in sync with origin/main; 8,184 pre-existing dirty paths
(sibling lanes' work on a shared checkout) — all treated as pre-existing; only
path-scoped files below were staged.

- Cold-start re-audit from entry docs: (a) status PASS (START_HERE 'Current
  state' block -> STATUS.md ledger), (b) next actions PASS (TO-DO.md pointer +
  open rows carry acceptance contracts), (c) verification PASS (START_HERE
  Steps 4-5; STATUS.md per-row commands). Still 3/3.
- Implemented DOC-STARTHERE-LINT-TIMEOUT-MED-1 (previously open, Medium):
  `--paths` scoped mode for the docs lint. `doc_roots()` /
  `run_docs_lint()` / `run_mermaid_lint()` / `run_links_lint()` accept an
  optional repo-relative path scope; missing or repo-escaping entries fail
  loudly (no silent scope shrink). CLI: `uv run python scripts/audit/lint_docs.py
  --paths README.md START_HERE.md docs/ --links-only --json`.
- Verified this session: scoped run over the three root entry docs completed in
  seconds with exit 0 and 0 broken links (full-repo lint previously exceeded
  420 s on this external-drive checkout). Negative controls verified live:
  missing path and `../`-escape both error with an explicit message.
- Tests: 5 new real-filesystem tests in
  `tests/infra_tests/validation/docs/test_lint_runner.py` (scope limiting,
  missing-path rejection, escape rejection, scoped broken-link detection, scoped
  clean pass). No mocks. Ruff check+format clean on all three edited files.
- TO-DO.md: DOC-STARTHERE-LINT-TIMEOUT-MED-1 flipped to completed with the new
  acceptance command.
- mypy on the edited module: not completed this pass (uv/mypy on this volume
  exceeded lane budget); CI type-check will cover it. Honest statement.
