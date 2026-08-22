# Deep Pass — Re-verification Addendum, 2026-08-21 (Dr. PAI session 2)

Second dispatch into `template` (branch `main`, local tip at start: `d2ced8304`).
The repo already carries five deep-pass commits from today (four sessions' reports plus
a pip lockfile security fix). This pass therefore re-verifies the open findings from my
earlier report (`DEEP_PASS_2026-08-21_dr-pai-session.md`) against current HEAD and
records the delta. No code changes were made by this session; all gates below were
executed fresh and measured.

## Contention note

The tree arrived with 7 dirty files and grew to ~21 during the session (rendering
helpers, `infrastructure/core/health.py`, CHANGELOG, pyproject/uv.lock, multiple test
files) — a concurrent session is actively working in this checkout. Per mission hard
rules I touched none of those files and committed nothing of theirs.

## Gate results this session (all measured)

| Gate | Result |
| --- | --- |
| Ruff (`public_scope lint-paths`, full public surface incl. all 24 exemplar trees) | PASS — "All checks passed!" |
| Mypy (`public_scope source-paths`) | PASS — "no issues found in 1559 source files" |
| No-mocks lexical + semantic inventory (`--inventory --max-dependency-replacements 0`) | PASS — dependency_replacement: 0 |
| Bandit (`bandit.yaml -r infrastructure scripts projects/templates`) | PASS — 12 findings, ALL Low severity/confidence (B105 false positives on classification dicts like `"SECRET": 2` in template_redacted_report, B107 on a test canary string, B110 guarded optional-dependency fallbacks); zero High/Medium |
| Tracked secrets scan (`check_tracked_secrets.py`) | PASS — "No high-confidence credentials found in tracked files." |
| Confidentiality guards (`check_tracked_all.py`) | PASS — projects/fonds/rules/tools all clean |
| Module line-count gate | PASS with 3 WARNs ≥800 lines (no fails ≥950): `infrastructure/validation/output/pipeline.py:810`, `infrastructure/validation/rendered_snapshot.py:800`, `template_active_inference/src/orchestration/full_verification.py:929` |
| Generated docs sync: `api_reference --check` (25 packages), `exemplar_roster --check` (24 exemplars), `publication_records --check` | PASS (in sync) |
| Docs lint non-mermaid lanes | PASS — cross-links 0 broken, consistency 0, doc-pairs 0 (268 mermaid blocks discovered) |
| Backlog contract (`check_backlog.py`) | PASS — 25 files, 22 stable IDs, 0 errors/warnings |
| STATUS freshness gate | PASS — max age 183 days |
| Skills exports (`infrastructure.skills check-all-exports`, `check`) | PASS — 0 violations |
| Template drift check | PASS — "no drift detected" |
| Focused pytest: `tests/infra_tests/rendering/test_pdf_latex_helpers.py` (concurrent session's new code) | PASS — 60 passed in 2.81 s |
| Focused pytest: `tests/infra_tests/git_hook_smoke/` | PASS — 14 passed in 19.78 s |
| Mermaid render lane (`lint_docs.py --mermaid-only`) | FAIL — 2 timeout-only failures (see F2 below) |
| Unified health (`infrastructure.core.health`) | NOT COMPLETABLE under contention — >20 min without finishing twice; concurrent session load. Remains scoped (J1 in earlier report). |

## Finding status updates

**F1 (Minor, pipeline-smoke secret-scan timeout) — CLOSED.** The concurrent session's fix
is now correct in final shape: single `@pytest.mark.timeout(120)` on the tracked-blob scan
test (`test_tracked_generated_artifacts.py:80`) and `timeout(240)` on the sibling index scan
(`:58`); my earlier residual nit about stacked decorators is resolved. Verified:
git_hook_smoke suite passes (14 passed, 19.78 s).

**F2 (Minor, mermaid timeouts) — PARTIALLY RESOLVED, still open.** On this quieter rerun,
only 2 of the earlier 8 blocks fail, both pure mmdc/puppeteer timeouts (exit 124),
not syntax errors:
- `docs/guides/literature-workflow-guide.md:10`
- `docs/guides/publishing-guide.md:503` (hit the run's total 300 s budget)

Status: deferred again — environment latency class. The `.github/*` blocks that failed
this morning now render fine, confirming machine-load sensitivity. Recommend re-running
`uv run python scripts/audit/lint_docs.py --mermaid-only` on an idle machine before
editing either diagram.

**M1 (Medium, mirror-shape violations) — still open, unchanged.**
`projects/active/project`, `projects/active/test_project` (real dirs),
`projects/working/Untitled` (regular file), `projects/working/ap3` (real dir).
None git-tracked; owner remediation via sidecar + `link-projects`.

**M2 (Medium, branch behind origin/main) — WORSENED, still deferred.**
Now 10 ahead / 10 behind relative to `origin/main` (local deep-pass commits vs remote
movement). Fast-forward is no longer possible without a merge/rebase; do it when the
tree is quiet and another session isn't holding dirty rendering files.

**M3 (Medium, dependency drift) — unchanged / deferred.**

**J1 (Major, full infra + unified-health lanes unverifiable under load) — still scoped
as written in `DEEP_PASS_2026-08-21_dr-pai-session.md`.**

## New observations (recorded, no action taken)

- `counts.py --check` reports STALE coverage provenance for `template_active_inference`
  ("source hash changed"). Expected while a session has uncommitted edits in that tree;
  regenerating coverage provenance mid-contention would produce a false snapshot.
  Deferred until the tree settles.
- Bandit's Low-severity B105 hits on `template_redacted_report` classification dicts are
  false positives (classification levels, not credentials). No config change made — CI
  runs `-ll` (medium+), so they never block.

## Addendum update: unified health completed on third attempt

A background `uv run python -m infrastructure.core.health --json` run launched during
this session completed after ~35 min (26 gates). Result: **23 PASS / 3 FAIL**, and all
three failures are attributable to the concurrent session's uncommitted work or machine
load — no defect in committed code:

- `ruff-format` — would reformat `infrastructure/core/health.py` and
  `tests/infra_tests/rendering/test_slides_renderer_core.py`; both are in the
  concurrent session's **dirty (uncommitted)** set.
- `docs-lint` — single mermaid timeout (`docs/architecture/two-layer-architecture.md:39`,
  mmdc exit 124 under load); same environment-latency class as F2.
- `counts` — STALE coverage provenance for `template_active_inference`; expected while
  uncommitted source edits change the tree hash (see observation above).

This partially closes J1: the unified-health lane is now measured end-to-end. Remaining
for J1 closure: rerun on a quiet tree (expect ruff-format/docs-lint/counts to flip green)
plus the full infra test lane and public project matrix.

## Deliverable checklist

- [x] This addendum records classified finding statuses with evidence
- [x] No fixes belonged to this session to implement: every remaining open item is either
      owned by an active concurrent session (dirty rendering/health files), requires an idle
      machine (mermaid, unified health, full infra lane), or requires owner action (mirror
      hygiene, pull/rebase)
- [x] Path-scoped commit of this file only; no push
