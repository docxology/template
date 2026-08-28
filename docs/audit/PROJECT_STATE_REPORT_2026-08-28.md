# Project State Report — 2026-08-28 (fleet deep-work session)

## Assessment

| Gate | Result |
| --- | --- |
| `check_backlog.py --strict` | PASS (25 files, 22 stable IDs, 0 errors/warnings) |
| `check_claim_bindings.py --json` | PASS |
| `check_public_template_contract.py --strict` | PASS (24 exemplars, 0 findings) |
| `check_template_drift.py --strict` | PASS (no drift) |
| `check_tracked_all.py` | PASS (projects/fonds/rules/tools clean) |
| `check_tracked_generated_artifacts.py` | PASS |
| `check_tracked_secrets.py` | PASS |
| `counts.py --check` | PASS |
| Ruff (public lint surface) | PASS |
| mypy (source paths, 1570 files) | PASS |
<!-- Dated historical receipt from this session's runs; live counts are
     authoritative in docs/_generated/COUNTS.md. -->
<!-- noqa: drift-counts -->
| `tests/infra_tests/documentation/ + publishing/` | 1183 passed, 3 deselected |
<!-- noqa: drift-counts -->
| `tests/regression/` | 55 passed |
<!-- noqa: drift-counts -->
| `projects/templates/template_template/tests/` | 147 passed (coverage floor met) |
| `infrastructure.core.health` | PASS 26/26 gates |

## Findings and fixes

1. **Real defect (fixed): unpruned tree walk in `template_template` introspection.**
   `build_infrastructure_report` filtered `_is_excluded_path` *after* a full
   `repo_root.rglob("*.py")`, so excluded subtrees (`.venv`, `node_modules`,
   `output`, lifecycle mirrors) were fully traversed on an external-drive
   checkout: measured 30.9 s / 71,826 entries unpruned vs 1.3 s pruned. The
   unpruned walk exceeded the regression tier's 30 s test policies, making
   `tests/regression/projects/template_template` flake under fleet load.
   Fix: `_iter_matching_files` prunes `_EXCLUDED_DIRS` during traversal and
   skips directory symlinks (matching `pathlib.rglob` semantics). Counts
   verified identical before/after (2947 py / 1036 test files). Regression
   tier now completes in ~2 s. Commit `24b8c80f8`.

2. **Generated provenance refreshed** after (1): `coverage_snapshot.json`
   source hash + source commit via `counts.py --refresh-coverage-provenance
   --write`. Commit `9ae1f2777`.

3. **Verified non-defect:** recent `fix(methods)` commit `e79daf028` correctly
   imports `_artifact_manifest_from_payload` from `_plan_validation` after the
   orchestration split; methods AGENTS.md module table matches the split.

## Environment notes (not repo defects)

- Host was shared with ~25 sibling pytest processes (fleet dispatch) during
  baseline runs; the docs+publishing and regression slices initially failed
  only inside deliberately-tight in-repo time policies (30 s subprocess policy
  in `test_counts_doc.py`, asserted as contract at lines 252/260). Both pass
  cleanly when re-run; no test or policy was loosened.
- A stale zero-byte `.git/index.lock` (crash leftover, 0 bytes, no holder via
  `lsof`) was removed before committing, per maintenance skill protocol.
- The health registry's own 30 s `git status` subprocess timed out under load
  on first attempt; PASS on re-run.

## Backlog

Remaining root rows are all `completed` or `blocked-external`
(CLEAN-CHECKOUT-MAJ-1, ARCHIVAL-TRACKER-MIN-1, SECURITY-OWNERSHIP-1,
SECURITY-PRIVATE-PROMOTION-1) — each requires an owner/platform receipt that
a local checkout cannot establish. No new rows opened.

## Push

- Commits: `24b8c80f8`, `9ae1f2777` (both authored this session)
- `git rev-parse HEAD` == `git ls-remote origin main` == `9ae1f2777`
- Hosted CI: not watched (local-only session; see `.github/AGENTS.md` for
  remote reproduction).
