# Deep Assessment & Improvement Pass — 2026-08-21

Dispatched Hermes agent pass on `template/` (commit 0db2afcbb, branch `main`).
Tree was dirty on arrival (rendering + template_active_inference provenance
files owned by another session); those were left untouched and excluded from
commits.

## Executive summary

Repository health is strong for a repo of this size (1,559 mypy-checked source
files, ~2,000 tracked docs, 24 public exemplars):

- Ruff clean on the full public lint surface; mypy clean (1,559 files).
- Tracked-secrets scan: no high-confidence credentials.
- Confidentiality guards (projects/fonds/rules/tools): all clean.
- Generated-artifact guard: clean. Template drift check: no drift.
- API reference, exemplar roster, status evidence, publication records,
  stage table: all in sync. `__all__` export audit: 0 violations.
- pip-audit: no known vulnerabilities; `uv lock --check`: consistent.
- Backlog contract check (`check_backlog.py`): 0 errors, 0 warnings.

The material findings are (1) two semantic no-mocks debt items that failed the
CI ceiling — **fixed**; (2) load-dependent test hangs in the full infrastructure
suite — scoped as Medium, not fixed (environment/load-dependent, passes
standalone).

## Verified gate results (measured this session)

| Gate | Result |
| --- | --- |
| `ruff check` (public lint paths) | All checks passed |
| `mypy` (public source paths) | Success: no issues in 1559 files |
| `verify_no_mocks.py --inventory --max-dependency-replacements 0` | dependency_replacement: 0, Status: clear (was 2) |
| `check_tracked_secrets.py` | No credentials found |
| `check_tracked_all.py` | projects/fonds/rules/tools: clean |
| `check_tracked_generated_artifacts.py` | Clean |
| `check_template_drift.py` | No drift |
| docgen checks (api_reference, exemplar_roster, status_evidence, publication_records, stage_table) | In sync / OK |
| `infrastructure.skills check`, `check-all-exports`, `check-contracts` | OK / 0 violations / contracts ok |
| `pip-audit` | No known vulnerabilities |
| `uv lock --check` | Resolved 189 packages, consistent |
| `audit_filepaths.py` | 55 link issues, all classified known exceptions (green), 0 red/yellow |
| Focused tests touched by fixes | 6 passed (workspace), 2 passed (artifact_finalization standalone), targeted autoresearch CLI test passed |

Full-suite runs under this machine's current load hit watchdog timeouts in
subprocess-heavy tests (see MEDIUM findings); the full coverage-bearing suite
could not be completed to a green exit within this session's budget.

## Findings

### Minor

**M1 — Semantic no-mocks debt: `monkeypatch.setattr(subprocess, "run", ...)`**
- Evidence: `tests/infra_tests/project/test_workspace_branches.py:22`
- Status: FIXED. Replaced with a real missing-binary invocation
  (`run_uv_command(["definitely-not-a-real-executable-..."])`) which raises
  `FileNotFoundError` through the real `subprocess.run` path. Verified:
  6/6 tests pass, inventory drops to 0 dependency replacements.

**M2 — Semantic no-mocks debt: `monkeypatch.setattr(workspace, "run_uv_command", ...)`**
- Evidence: `tests/infra_tests/project/test_workspace_branches.py:69`
- Status: FIXED. Test now runs real `uv sync` / `uv sync --upgrade` against an
  empty temp dir and asserts nonzero exit codes. Same verification as M1.

### Medium

**MD1 — Load-dependent hangs in full infrastructure pytest run**
- Evidence A: `tests/infra_tests/core/pipeline/test_artifact_finalization.py:118`
  → `executor.execute_full_pipeline()` stalls in
  `infrastructure/core/_bounded_run_guardian.py:133`
  (`_expect_status` waiting for guardian `_DONE`) when run inside the full
  suite; passes standalone in 7.05s (measured twice).
- Evidence B: `tests/infra_tests/autoresearch/test_autoresearch.py:904`
  subprocess wait stalls mid-suite; passes standalone in 8.67s.
- Both hang sites are bounded-subprocess cleanup/communication paths that are
  sensitive to scheduler pressure; the guardian's `_DONE_TIMEOUT_SECONDS = 45`
  is not reached because the outer pytest-timeout fires first with a stack dump.
- Status: DEFERRED (see Major scoping MD1 below — cross-cutting timing work).

**MD2 — `docs/_generated/COUNTS.md` stale + coverage provenance stale**
- Evidence: `scripts/docgen/counts.py --check` reports STALE;
  `--write` refuses transactionally: "stale coverage snapshot for
  template_active_inference: source hash changed".
- Root cause: pre-existing uncommitted provenance changes under
  `projects/templates/template_active_inference/output/data/` from another
  session changed the source hash out from under the snapshot.
- Status: DEFERRED — resolving it requires rerunning that project's coverage
  gate, which belongs to the owner of those dirty files.

**MD3 — Mermaid lint mmdc timeouts (3 blocks in `.github/README.md`)**
- Evidence: `scripts/audit/lint_docs.py --mermaid-only` output: blocks at
  `.github/README.md:534`, `:608`, `:917` fail with `exit 124: mmdc timed out
  after 30s`. Consistency and doc-pairs linters report 0 issues.
- Status: DEFERRED — timeouts are environment slowness (Chromium/puppeteer cold
  start under load), not demonstrated syntax errors. Re-run on an idle machine
  before treating any block as genuinely broken.

### Advisory (no action required)

- Line-count warnings: `infrastructure/validation/rendered_snapshot.py` (800),
  `projects/templates/template_active_inference/src/orchestration/full_verification.py`
  (929), plus several infra modules at 800–950 lines — all within the ratchet
  contract (WARN ≥800, FAIL ≥950), tracked by the existing downward-only ratchets.
- 29 TODO/FIXME markers in non-test infrastructure/scripts code — all appear in
  tracked backlog surfaces; no orphaned correctness TODOs spotted in sampling.

## Major (scoped, not implemented)

**MJ1 — Bounded-subprocess guardian robustness under scheduler pressure (MD1)**
- Approach: (a) make `_bounded_run_guardian.wait_for_cleanup()` degrade
  gracefully — treat guardian timeout as a logged warning plus forced
  `close()` rather than propagating a TimeoutError that kills unrelated suite
  progress; (b) add a dedicated stress test running N concurrent
  `run_bounded_subprocess` calls asserting no hang beyond bound+slack;
  (c) consider raising `_DONE_TIMEOUT_SECONDS` or making it env-tunable
  (`TEMPLATE_GUARDIAN_DONE_TIMEOUT`) so loaded CI machines can be accommodated.
- Effort: 1–2 days including stress testing on both macOS and Linux.
- Risks: weakening the guardian could mask real leaked-token conditions; the
  graceful-degradation path must still kill descendants on hard failure.
- Acceptance criteria: full `tests/infra_tests/` suite completes green on a
  loaded 4-worker machine; new stress test reproduces the prior hang condition
  and passes; no increase in semantic dependency-replacement debt.

**MJ2 — Full-suite wall-clock budget**
- The complete infrastructure lane exceeded 19 minutes before its first stall
  and did not reach completion within this session. Approach: split the suite
  into subprocess-heavy and pure lanes with separate xdist scopes (the
  `pytest_orchestration.py` machinery already supports scope-based
  distribution), then re-baseline CI timings.
- Effort: 0.5–1 day after MJ1. Risks: lane split changes coverage aggregation;
  must keep the union-gate math intact. Acceptance: CI full-lane job completes
  under its timeout with unchanged coverage floors.

## Files changed by this pass

- `tests/infra_tests/project/test_workspace_branches.py` (M1, M2 fix)
- `DEEP_PASS_2026-08-21.md` (this file)

No push performed; commits are path-scoped and local only.
