# REVIEW LOG — 2026-08-31 (agent-ergonomics fleet pass)

Lane: agent-erg fleet, repo `template`, branch `main`, in sync with `origin/main` at start.
Pre-existing dirty tree at dispatch: 140 paths (mostly uncommitted deletions under
`projects/templates/template_autopoiesis/output/` plus an untracked `_FLEET_REPORT_2026-08-30.md`,
later removed by a concurrent sibling). All treated as pre-existing; none touched.

## Cold-start audit (Phase 1)

Attempted as a cold agent, using only the entry docs:

- (a) Current status — PASS. `START_HERE.md` "Choose your path" routes to
  `STATUS.md` (per-subsystem verification ledger, last updated 2026-08-09) and
  `TO-DO.md` (backlog with acceptance contracts). Both are real, current files.
- (b) What to do next — PASS. `TO-DO.md` is the declared single authoritative
  backlog; `START_HERE.md` links it in two places.
- (c) Primary verification command — PASS. `START_HERE.md` Step 4 gives the exact
  command and expected success signals (exit 0, PDF path, coverage floors).

Score: 3/3 before changes. This repo already implements the orientation ladder well.

## Findings

- MINOR 1 — Stale wall-clock claim: `START_HERE.md:158` (and
  `docs/guides/startup-and-setup.md:117`) say the core pipeline takes "2-5 minutes".
  Measured evidence in this repo's own 2026-08-30 audit records
  (`docs/audit/AUDIT_2026-08-30*.md`) shows 44+ minutes on this external-drive
  checkout under load. Fixed START_HERE.md wording to state the quiet-machine
  figure with the slow-drive caveat; the guide was left (same fix applies; noted
  in TO-DO.md as ERG-WALLCLOCK-MED-1).
- MINOR 2 — Transient lane audit reports at repo root: four `AUDIT_2026-08-30*.md`
  files sat at the root at dispatch (transient fleet artifacts). During this
  session a concurrent sibling moved them into `docs/audit/` with an explanatory
  note in `docs/audit/AGENTS.md` — the correct resolution. Nothing to do beyond
  recording it; no entry doc links them as current guidance (verified by grep).
- MINOR 3 — Link sweep: 3,567 relative links checked across `docs/**/*.md` plus
  all root entry docs. Root entry docs: 0 broken. `docs/`: ~135 regex hits, all
  false positives (illustrative Pandoc `![caption](path)` examples in usage/style
  guides, and `docs/prompts/_skill-eval/` harness fixtures which the repo's own
  linter deliberately excludes). No real broken links found. No fix needed.
- MINOR 4 — 19 untracked `sidecar_*.py/.json/.txt/.out/.jsonl` scratch scripts at
  root (one-off sidecar-migration helpers, some hard-coding absolute paths).
  Transient artifacts, not documentation; out of safe scope to delete in a
  shared dirty tree (cannot verify no sibling lane is using them). Recorded in
  TO-DO.md as ERG-SIDECAR-SCRATCH-MIN-1 for the owner.

## Scope decisions

- No duplicated fact-class found without a canonical home: status -> STATUS.md,
  backlog -> TO-DO.md, counts -> docs/_generated/COUNTS.md, roster ->
  docs/_generated/active_projects.md. Entry docs link rather than copy.
- Link-checker helper not added: the repo already has `scripts/audit/lint_docs.py`
  as the executable truth for links; a second checker would violate least-resource.

## Changes by this lane

- `START_HERE.md` — wall-clock claim corrected.
- `REVIEW_LOG_2026-08-31.md` — this file.
- `TO-DO.md` — two appended backlog rows (see Phase 2 section below).

## Verification

- `git status --porcelain -- START_HERE.md TO-DO.md REVIEW_LOG_2026-08-31.md`
  checked before path-scoped add — only these three files staged.
- Link re-check re-run on START_HERE.md after edit: 0 broken.
- Fast gate: not run in full (pipeline-smoke measured 28-44 min on this checkout;
  exceeds lane budget). See fleet report for the honest gate statement.
# Agent-Ergonomics Pass — 2026-08-31 (fleet lane)

Preflight: branch main; 140 pre-existing dirty files (treated as pre-existing); fetch running in background (slow external drive, 180s+).

## Phase 1 — cold-start audit (entry docs only)

(a) Current project status: PASS. START_HERE.md → STATUS.md ledger (last updated 2026-08-09, per-row verification commands + receipts). README.md links STATUS.md in positioning block.
(b) What to do next: PASS AFTER sibling edit found mid-flight (uncommitted START_HERE.md orientation block + TO-DO.md row DOC-ENTRY-ORIENT-MIN-1 already present from a concurrent lane; verified on disk, adopted not duplicated). TO-DO.md is the single backlog with acceptance contracts.
(c) Primary verification command: PASS. START_HERE.md Steps 4-5 give the canonical pipeline command + expected outputs; STATUS.md rows give per-subsystem verification commands.

## Findings

- MINOR: README.md lacked STATUS.md/TO-DO.md links outside the positioning prose — README line 726 already links TO-DO.md ("Check the backlog"); STATUS.md linked at line 49. Verdict: adequate; no edit made (least-resource).
- MEDIUM: 4 untracked AUDIT_2026-08-30*.md files at repo root conflict with docs/audit/AGENTS.md placement policy ("do not place at repository root"). Not linked from any entry doc (verified). Scoped as TO-DO row AGENT-ERG-AUDIT-FILES-MED-1; NOT moved by me — they are other lanes' untracked artifacts, moving them would collide with active writers (shared-checkout discipline).
- Verified-non-issue: drift lane's reported dead links (template_code_project/template_prose_project docs/manuscript/AGENTS.md → rendering_pipeline.md/troubleshooting.md anchors) RESOLVE against the current tree (targets + anchor slugs verified programmatically). The drift report predates the manuscript-path migration landing.
- Entry-doc link targets verified on disk: docs/guides/startup-and-setup.md, docs/prompts/startup/SKILL.md, docs/repurposing-architectures.md, docs/operational/build/dependency-management.md, docs/prompts/COMPOSITION.md, docs/prompts/MODE_REGISTRY.md, docs/_generated/* — all exist.

## Phase 3 implementation

- TO-DO.md: added AGENT-ERG-ORIENT-LADDER-MIN-1 (completed) and AGENT-ERG-AUDIT-FILES-MED-1 (open) rows per the file's contract.
- No edits to README/AGENTS/CLAUDE needed: orientation ladder already present and verified.
- Generated docs untouched (generator-owned per docs/_generated/AGENTS.md).

## Deferred

- Archiving the 4 root audit files: owner-lane artifacts, untracked, active-writer risk (shared checkout). Scoped instead.
- Full doc-surface link lint (`scripts/audit/lint_docs.py`) on whole repo: exceeds drive-timeout budget this lane (past full-tree runs measured 400-8000s); targeted checks used instead.

## Second lane pass - 2026-08-31 (closure sweep)

- Cold-start re-audit: (a) status PASS via START_HERE.md orientation block -> STATUS.md; (b) next-actions PASS via TO-DO.md pointer; (c) verification PASS via Steps 4-5. All three orientation tasks succeed from the entry doc alone.
- Concurrent-lane note: a sibling lane consolidated START_HERE.md's duplicated orientation blocks during this pass; this lane verified the consolidated form (single 'Current state' block + 'What to do next' block, no overlap) and did not re-edit that file.
- Fixed: TO-DO.md ERG-ENTRY-DOCS-2026-08-31 row was a stray bullet above the backlog table intro; moved into the actual table with acceptance contract intact.
- Acceptance command verified: `grep -c STATUS.md START_HERE.md AGENTS.md docs/documentation-index.md` -> 2/1/1.
- Link check on START_HERE.md/TO-DO.md targets: all 9 checked relative targets exist on disk (STATUS.md, TO-DO.md, docs/_generated/COUNTS.md, docs/_generated/active_projects.md, docs/guides/startup-and-setup.md, docs/prompts/startup/SKILL.md, docs/operational/build/dependency-management.md, docs/guides/getting-started.md, docs/operational/troubleshooting/README.md).
- git fetch origin: not completed (exceeded 300s on this volume); remote parity unverified this session - check with `git status -sb` after a quiet fetch.

## Third lane pass - 2026-08-31 (closure of remaining fleet rows)

Preflight: branch main; 144 pre-existing dirty paths at dispatch (prior lanes'
edits plus sidecar scratch), all treated as pre-existing. `git fetch origin`
not re-attempted this pass (measured >180s on this volume earlier today).

- Cold-start re-audit from entry docs: (a) status PASS (START_HERE 'Current
  state' block -> STATUS.md), (b) next actions PASS (TO-DO.md pointer), (c)
  verification PASS (START_HERE Steps 4-5). Still 3/3.
- ERG-WALLCLOCK-MED-1 closed: docs/guides/startup-and-setup.md:117 now states
  the quiet-machine figure with the 2026-08-30 measured 44+ min
  external-drive/concurrent-load caveat (citing docs/audit/AUDIT_2026-08-30.md).
- AGENT-ERG-AUDIT-FILES-MED-1 closed: root AUDIT_2026-08-30*.md files were
  moved to docs/audit/ by an earlier lane; acceptance command re-run this
  session (`ls AUDIT_2026-08-30*.md` -> none-at-root) and TO-DO.md row updated
  to completed with the verified note.
- ERG-SIDECAR-SCRATCH-MIN-1 left open: the 19 root sidecar_* scratch files
  remain; deletion stays with the owner lane per shared-checkout discipline.
- Link check on the edited guide: target docs/audit/AUDIT_2026-08-30.md exists
  on disk; no other links touched. No entry docs changed this pass.
- Fast gate: not run (pipeline-smoke measured 28-44 min on this checkout;
  exceeds lane budget). Honest statement, not a gate pass.
