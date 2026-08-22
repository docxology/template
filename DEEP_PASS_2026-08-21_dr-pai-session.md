# DEEP PASS — 2026-08-21 (Dr. PAI session)

Note: a parallel agent session published its own `DEEP_PASS_2026-08-21.md` at the same
time; both reports are retained. That session's report is canonical at the un-suffixed path.

Autonomous assessment + improvement pass on `template` (branch `main`, HEAD `0db2afcbb`).
Executed under contention: another agent session was actively working in this checkout
(rendering helpers + provenance JSON dirty at arrival; later also editing
`tests/infra_tests/git_hook_smoke/test_tracked_generated_artifacts.py` and running a large
pytest fleet, load average 227). Per mission rules I did not touch their files or commits,
and I avoided CPU-heavy verification runs that would corrupt both sessions' measurements.

## Executive summary

Repository health is **strong**. Every enforced gate I could run passed cleanly:

| Gate | Result |
| --- | --- |
| Ruff (`public_scope lint-paths`) | PASS ("All checks passed!") |
| Mypy (`public_scope source-paths`) | PASS — "no issues found in 1559 source files" |
| Bandit (`bandit.yaml`, `-r infrastructure scripts`) | PASS — zero findings |
| No-mocks lexical gate (1189 files, 25 roots) | PASS |
| Tracked secrets scan (all blobs) | PASS — 0 findings (measured 17.5 s runtime) |
| Confidentiality guards (`check_tracked_all.py`) | PASS — projects/fonds/rules/tools all clean |
| Generated-artifact index guard | PASS |
| Template drift (`--strict`) | PASS — "no drift detected" |
| Docs lint: cross-links / consistency / doc-pairs | 0 broken / 0 issues / 0 issues (268 mermaid blocks discovered) |
| Backlog contract (`check_backlog.py`) | PASS — 25 files, 22 stable IDs, 0 errors |
| Test collection (`tests/infra_tests`) | 10,280 collected / 51 deselected, 0 collection errors |
| Pipeline-smoke suite (stage_01) | FAIL -> root-caused (see F1); fix applied by concurrent session |

No security findings, no dead-code clusters beyond the repo's own tracked TODO system, no
broken cross-links, no fabricated counts. The one reproducible test defect is a timeout
budget issue, not a correctness bug.

## Findings

### Minor

**F1 — Pipeline-smoke secret-scan test exceeds global 10s pytest timeout**
Evidence: `tests/infra_tests/git_hook_smoke/test_tracked_generated_artifacts.py:76-79` calls
`tracked_secret_findings(repo_root)` (`infrastructure/project/git_guards.py:438`), which scans
every tracked blob; measured **17.5 s** cold on this checkout vs the repo-wide
`timeout = 10` in `pyproject.toml:266`. Reproduced twice as the sole cause of
`stage_01_test.py --infra-only --infra-scope pipeline-smoke` failing (`exit=1`,
"Infrastructure: 1 failure(s) exceeds tolerance (max: 0)"). The test itself passes
standalone when given budget.
Status: **fixed by concurrent session** (their uncommitted edit adds
`@pytest.mark.timeout(120)` on this test and raises the sibling subprocess cap to 120 s).
I independently diagnosed and measured the root cause before seeing their edit, and
confirmed their fix is the right shape. Residual nit for that session: two stacked
`@pytest.mark.timeout(...)` decorators remain on
`test_current_repo_has_no_tracked_generated_artifacts` (`180` then `150`) — keep one.

**F2 — Mermaid render timeouts in `.github/AGENTS.md` / `.github/README.md`**
Evidence: `scripts/audit/lint_docs.py` reports 8 blocks failing with mmdc `exit 124`
(per-block 30 s timeout; e.g. `.github/README.md:199,342,360,422,442,534,608`,
`.github/AGENTS.md:24`). All failures are timeouts, not syntax errors — they rendered
under CI previously and the machine was at load 227 during measurement.
Status: **deferred** — environment latency, not content defects; re-run
`uv run python scripts/audit/lint_docs.py --mermaid-only` on an idle machine before
changing any diagram.

### Medium

**M1 — Local-only mirror-shape violations fail `check_mirror_symlinks.py`**
Evidence: `projects/active/project` (real directory), `projects/working/ap3` (real
directory), `projects/working/Untitled` (regular file). These are workspace-hygiene items,
not repo content — none are git-tracked (confidentiality guard passes).
Status: **deferred (owner action required)** — remediation is exactly what the guard
prints: move each into the private sidecar and run
`uv run python -m infrastructure.orchestration link-projects`. Not mine to relocate
under the don't-touch-pre-existing-work rule; flagged for Daniel.

**M2 — Branch is 10 commits behind `origin/main` (fast-forwardable)**
Evidence: `git status` shows behind 10; remote tip `b092764d2`. Includes rendering
hardenings (`0fd774d37`) that overlap the concurrent session's dirty files.
Status: **deferred** — pulling would entangle another session's uncommitted work;
fast-forward when the tree is quiet.

**M3 — Environment dependency drift: 56 outdated packages** (`uv pip list --outdated`),
e.g. `jax 0.9.2->0.11.1`, `coverage 7.13.2->7.15.4`, `bandit 1.9.3->1.9.4`.
Status: **deferred** — lockfile-managed upgrades deserve their own gated pass
(`uv lock --upgrade` + full suite), not a contested deep pass.

### Major (scoped, not implemented)

**J1 — Full infrastructure gate + unified health gate could not complete under load**

The coverage-bearing lane (`stage_01_test.py --infra-only --infra-scope full`, ~10.3k tests)
and `infrastructure.core.health` (serial mode ran >33 min without finishing; a rerun was
SIGTERM-killed at exit 143) were not completable while a second session saturated the
machine (load avg 227-291). No evidence of a repo defect — every statically checkable gate
passed — but the deep-pass claim stops at collection + static gates for these lanes.

Scope plan:
- Approach: on a quiet tree, run `uv run python -m infrastructure.core.health --workers 1`
  to completion, then `stage_01_test.py --infra-only --infra-scope full`, then the public
  project matrix per `.github/workflows/ci.yml`. Record measured durations into
  `docs/_generated/COUNTS.md` inputs.
- Effort: ~2-4 h wall clock, mostly unattended.
- Risks: macOS coverage worker ceiling (>2 workers fails early by design);
  Ollama-dependent stages skip cleanly; any red here likely surfaces the same flaky-timeout
  class as F1 — fix budgets, not tests.
- Acceptance criteria: health JSON report exit 0; full infra lane green with coverage >=60%;
  public readiness matrix all PASS/SKIP-with-marker.

## Verification record

Commands actually executed this pass (measured outputs above): ruff via public_scope,
mypy via public_scope, bandit, verify_no_mocks, check_tracked_secrets (+direct
`tracked_secret_findings` timing), check_tracked_all, check_tracked_generated_artifacts,
check_mirror_symlinks, lint_docs, check_backlog, check_template_drift --strict,
stage_00_setup, stage_01_test pipeline-smoke x3, pytest collection of tests/infra_tests,
focused pytest of the F1 module, `uv pip list --outdated`.

## Deliverable checklist

- [x] `DEEP_PASS_2026-08-21_dr-pai-session.md` (this file)
- [x] Minor/medium findings fixed or explicitly deferred with reasons (F1 fixed via
      concurrent session's verified edit; nothing else met the bar to change under contention)
- [x] Path-scoped local commit of my own files only (this report); no push
- [x] Final summary printed to terminal


---

# Addendum — third-pass independent verification (same day)

A further dispatch re-verified the repo independently while both earlier reports' content
was on disk. New work and confirmations below; all measurements live this session.

## Fixed

**F1(new) — Known pip vulnerability PYSEC-2026-3721** — `uv run pip-audit` flagged
`pip 26.1.2` (fix >=26.2); `uv.lock` pinned exactly 26.1.2. Fix: `uv lock --upgrade-package pip`
-> 26.2.1 + `uv sync`. Verified: `pip --version` reports 26.2.1 in the project venv; re-run of
`uv run pip-audit` exits **0 with zero known vulnerabilities** (remaining row is only the
unavoidable skip for the local non-PyPI workspace package). Committed: `uv.lock` only.

## Gates re-verified this pass

| Gate | Result |
| --- | --- |
| Ruff check (public lint surface) | PASS |
| ruff format --check | clean except 2 files belonging to a foreign uncommitted feature (left untouched) |
| Mypy (`source-paths`, 1559 files) | PASS |
| verify_no_mocks lexical + `--inventory --max-dependency-replacements 0` | clear (0 replacements) |
| LLM deterministic suite (`-m "not requires_ollama"`) | **1226 passed**, 51 deselected |
| `template_code_project` suite | **246 passed** |
| Bandit (`bandit.yaml -qr infrastructure scripts`) | 0 findings, exit 0 |
| Tracked-secrets / confidentiality / generated-artifact guards | all clean |
| Backlog contract / template drift / active_projects --check / api_reference --check | all PASS/up-to-date |
| Docs lint cross-links/consistency/doc-pairs | 0 broken / 0 issues |
| Mermaid renders | 7 blocks exit-124 timeout locally under load (matches F2 above); environment flake, CI lane provisions pinned mmdc+chrome |
| Prerender validation (`template_code_project/manuscript`) | clean |

## Dispositions

- counts.py STALE coverage provenance for `template_active_inference`: consequence of the
  concurrent session's dirty tree, not committed HEAD; belongs to that feature's landing.
- Mirror-shape violations (M1) and 10-commits-behind (M2): unchanged, still deferred.
- Prior reports' findings independently confirmed where overlapping; no contradictions found.

---

# Addendum 2 — fourth-pass verification (same session, later)

Re-verified after the concurrent session landed its fixes as commits
(`e2a01aaad`…`d2ced8304`). All measurements below are live this pass.

## New fix implemented and verified this pass

**F3 — unified-health `docs-lint` gate times out at the shared 300s ceiling**
Evidence: `uv run python -m infrastructure.core.health --workers 1` reported
"docs-lint — gate timed out after 300s"; a direct `scripts/audit/lint_docs.py`
run needed >336s (268 Mermaid blocks rendered through headless-Chrome
subprocesses). `counts` already had an override (`1800s`); `docs-lint` did not.
Fix: added `"docs-lint": 900.0` to `_GATE_TIMEOUT_OVERRIDES`
(infrastructure/core/health.py:119) and wired per-gate resolution into both
serial and pooled execution paths, plus a `TestGateTimeoutResolution` suite in
tests/infra_tests/core/test_health.py. Verified: ruff check + format clean;
mypy clean on health.py; focused pytest `TestGateTimeoutResolution` **5 passed**;
full `test_health.py` module **26 passed** (137s).

## Gates re-confirmed green this pass

| Gate | Result |
| --- | --- |
| Ruff (public lint surface) | PASS |
| Mypy (source-paths, 1559 files) | PASS |
| Bandit | 0 issues |
| verify_no_mocks lexical + inventory (0 dep replacements) | clear |
| git_hook_smoke suite | **14 passed** (28.8s) after concurrent session's timeout budgets |
| exemplar_roster / api_reference / skills check / check-all-exports / stage_table idempotence | all PASS |
| Backlog contract | PASS (25 files, 22 stable IDs, 0 errors) |

## Still open

- STALE coverage provenance for `template_active_inference` (`counts --check`
  exit 1): tracked output JSONs remain dirty from the concurrent rendering
  feature; provenance refresh belongs to that work's landing, not this pass.
- F2 (Mermaid render timeouts), M1 (mirror-shape violations),
  M2 (branch behind origin/main), M3 (dependency drift): unchanged dispositions
  above.
- J1 full-infra-lane completion remains scoped, not run under contention.

## Commit

- `e03ddb9e7` deep-pass: raise docs-lint unified-health gate ceiling… (only
  infrastructure/core/health.py + tests/infra_tests/core/test_health.py; verified via
  `git show --stat HEAD`)
