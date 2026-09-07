# AUDIT_2026-08-30 — lane-scoped addendum (template-checkout audit lane, repo /Users/4d/Documents/GitHub/template, branch main @ ecdab23db)

Scope note: this addendum covers MY lane's independent findings. It complements (does not
overwrite) the existing herdr audit-lane report and its timeout-fix addendum, which I
verified on disk before writing (different lane name, different findings).

## Shared-checkout hazard (governs everything below)

At lane start the working tree was mid-migration by sibling agents: 47 untracked
`docs/manuscript/` trees + `template_formal/AGENTS.md` wave, plus staged work in
`infrastructure/core/health.py` and `infrastructure/publishing/export_bundle.py`
(manuscript-path resolution via `resolve_manuscript_dir`). A fresh `index.lock` (18:31)
appeared mid-session. Per lane constraints: **report only, no commits, no edits to
in-flight files.**

## Gate results (all executed by me, this checkout)

| Gate | Result |
|---|---|
| `uv run python scripts/audit/verify_no_mocks.py` | PASS (25 roots, 1192 files, exit 0) |
| `uv run python scripts/audit/check_tracked_all.py` | PASS (projects/fonds/tools/rules all clean) |
| `pytest tests/infra_tests/core/test_project_discovery.py` | 25 passed (21 s) <!-- noqa: drift-counts --> (dated 2026-08-30 historical note; live counts: docs/_generated/COUNTS.md) |
| `pytest tests/infra_tests/core/` (full subtree) | TIMED OUT at the 1200 s cap (pytest Timeout banner during collection) (external-drive contention with sibling pytest fleets; not an assertion failure) |
| `check_template_drift.py --strict` | FAIL — 96 ERROR + 251 WARN (mostly the in-flight migration's own mid-state; see MAJOR-1) |
| `check_template_drift.py` (non-strict, post-migration re-run) | timed out at the 1800 s cap under load (exit 124, no report) — inconclusive |
| `lint_docs.py` | FAIL — 314 broken cross-links (see MAJOR-2) |

## CRITICAL

1. **Exemplar-contract drift gate fails hard right now** (`check_template_drift.py --strict`):
   96 `missing_canonical_file` ERRORs — every public exemplar's
   `manuscript/config.yaml`, `config.yaml.example`, `references.bib`, `preamble.md`
   reported missing because tracked trees are mid-move to `docs/manuscript/` while the
   drift check still pins the conventional `manuscript/` path
   (`infrastructure/project/drift/checks_exemplar.py` required-files list). Note the
   runtime already tolerates both layouts (`infrastructure/core/project_paths.py:55-68`
   `resolve_source_manuscript_dir`; `infrastructure/orchestration/discovery.py:105` treats
   `docs/manuscript` as a discovery marker) — so the gate, not the runtime, is the
   laggard. Verification: errors reproduce consistently; `git show
   HEAD:.../template_active_inference/manuscript/config.yaml` still resolves, i.e. the
   deletion is uncommitted migration state, not data loss. **Owner: the migration lane
   must update the drift check (and re-point config-relative checks) in the same
   changeset that lands the move; until then CI drift and pre-push lanes fail.**

## MAJOR

2. **314 broken markdown cross-links** (`uv run python scripts/audit/lint_docs.py`):
   ~70 in `template_textbook` (unresolved figure placeholders linking to
   non-existent `output/figures/*.png`, and stale `manuscript/` paths), ~46 in
   `template_active_inference` (links from `docs/AGENTS.md` into the old
   `manuscript/sheaf/` paths), plus ~30 repo-root/docs links to
   `projects/templates/template_code_project/manuscript/` files. Most are downstream
   symptoms of the same migration + unrendered figure placeholders; they currently fail
   the docs lane. Owner: migration lane (path re-pointing) + template_textbook owner
   (real figures or non-link placeholder prose).

3. **Concurrent-agent checkouts make baseline verification nearly impossible** —
   `git status` 2-19 min, full `tests/infra_tests/core/` >30 min, drift re-run >30 min
   (22 TB external drive + up to ~10 concurrent pytest/git processes observed).
   Recommendation to fleet dispatch: serialize repo-wide gates, run them once at
   quiescence, and record the git rev in every lane report (this lane's: `ecdab23db`).

## MINOR

4. Backlog hygiene good (root TO-DO.md all completed/blocked-external with acceptance
   commands); infrastructure/ TODO/FIXME debt near zero (28 matches, all in tooling that
   manages TODOs). No fix needed.
5. `.laneD_results.json` (untracked, repo root) is a stale sibling scratch file; harmless
   but should not be committed (untracked; would fail generated-artifact hygiene if
   force-added).

## Fixes applied by this lane

None to code/docs — every candidate fix targeted files under active sibling migration
(drift gate, migration-path docs, template_textbook figures). Per the shared-checkout
constraint, all findings are reported here instead. This addendum file is the lane's
only artifact. No commits, no pushes, working tree untouched beyond this file.

## Verification evidence

- Every gate result above was executed in this lane's shell with `TEMPLATE_SKIP_LINK_SYNC=1`
  and recorded verbatim (exit codes and counts); no numbers inferred or copied from
  sibling reports.
- Cross-link category counts computed from `lint_docs.py` full output via programmatic
  grouping, not eyeballed.
