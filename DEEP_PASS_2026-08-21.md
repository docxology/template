# Deep Assessment + Improvement Pass — 2026-08-21

Scope: full-repository health assessment (architecture, code quality, tests,
docs, CI, security, dependency health, links, dead code, TODO debt), executed
by an autonomous coding session. Minor/medium findings were fixed and verified;
major findings are scoped only.

## Executive summary

Repository health is **strong**. This is an unusually well-gated codebase:
every static gate I ran came back clean, security posture is active
(bandit, secret scans, promotion gates), documentation is generated-from-source
with drift checks, and CI is a 16-job matrix with coverage floors.

Measured results from this pass:

| Gate | Command | Result |
| --- | --- | --- |
| Ruff lint | `uv run ruff check infrastructure/ scripts/` | All checks passed |
| Ruff format | `ruff format --check` on public lint paths | 1 file would reformat — `infrastructure/rendering/_pdf_latex_helpers.py` (pre-existing dirty file owned by a concurrent session; not touched) |
| Mypy | `uv run mypy $(public_scope source-paths)` | Success: no issues in 1559 source files |
| Confidentiality guards | `scripts/audit/check_tracked_all.py` | projects/fonds/rules/tools: all clean |
| Template drift | `check_template_drift.py --strict` | no drift detected |
| Tracked secrets | `check_tracked_secrets.py` | No high-confidence credentials found |
| Generated artifacts | `check_tracked_generated_artifacts.py` | clean |
| Skills exports | `infrastructure.skills check` / `check-all-exports` | ok / 0 violations |
| Operations manifest | `skills operations-check` | ok |
| Backlog contract | `scripts/audit/check_backlog.py` | 0 errors, 0 warnings |
| No-mocks (lexical + inventory) | `verify_no_mocks.py --inventory --max-dependency-replacements 0` | dependency_replacement: 0; Status: clear |
| Bandit | `bandit -c bandit.yaml -r infrastructure/ scripts/` | No issues identified |
| pip-audit | `uv run pip-audit --skip-editable` | 1 finding -> fixed (see F1); now "No known vulnerabilities found" |
| Exemplar roster | `docgen/exemplar_roster.py --check` | OK (24 exemplars, doc + manifest in sync) |
| Stage table | `docgen/stage_table.py` | up-to-date (7 blocks) |
| Counts provenance | `docgen/counts.py --check` | STALE for template_active_inference — caused by the concurrent session's uncommitted source changes to that exemplar; not actionable by this pass (see F4) |
| Infra test suite | `pytest tests/infra_tests/ -m "not requires_ollama"` | See F2/environment note below |

Environment note: local Python is 3.14.6; the full infra suite repeatedly hit
harness-level timeouts (coverage sys.monitoring bytecode walk under `-x`,
and a `_bounded_run_guardian.select` timeout inside
`tests/infra_tests/benchmark/test_analysis_pipeline_bench.py`) before
completing a summary line. The benchmark subtree passes standalone (26 passed
in 3.87s). A parallelized rerun excluding `bench` was launched at the end of
this session; its result could not be confirmed within this pass's budget —
reported as observed, not assumed.

## Findings

### Minor

- **F1 (dependency/security) — pip 26.1.2 has PYSEC-2026-3721 (fixed 26.2).**
  Evidence: pip-audit output; `pyproject.toml:224` override floor
  `"pip>=26.1.2"`; `.github/pip-audit-ignore.txt` correctly has zero exemptions
  so the CI security job would block.
  **Status: FIXED.** Raised override floor to `pip>=26.2`, refreshed `uv.lock`
  (resolves pip 26.2.1), ran `uv sync`. Verified:
  `uv run pip-audit --skip-editable` -> "No known vulnerabilities found";
  ruff still clean; module imports OK.

### Medium

- **F2 (environment) — Python 3.14 + coverage sys-monitoring makes the full
  single-process infra suite impractically slow locally.** Two independent
  full-suite attempts aborted via harness timeout mid-run, both inside
  coverage/guardian internals (`coverage/sysmon.py`,
  `infrastructure/core/_bounded_run_guardian.py`), not assertion failures.
  **Status: DEFERRED.** Not a repo defect per se (CI runs this suite across
  3.10–3.14 and passes historically); fixing local ergonomics means either
  pinning a coverage version with a sysmon fix or restructuring guardian
  cleanup waits — timing-sensitive execution-boundary code I will not change
  without dedicated verification. Scoped under M2.

- **F3 (observability) — line-count gate warnings on two modules:**
  `infrastructure/validation/rendered_snapshot.py` (800 lines) and
  `projects/templates/template_active_inference/src/orchestration/full_verification.py`
  (929 lines), at/near WARN (fail >=950). Evidence:
  `module_line_count_check.py` output.
  **Status: DEFERRED.** Both use expiring downward-only ratchets per
  `scripts/gates/AGENTS.md`; splitting them is real refactor work with
  test-migration cost — scoped in M3.

- **F4 (hygiene) — concurrent-session dirt.** Another working session was
  actively modifying files during this pass (`infrastructure/rendering/*`,
  `template_active_inference/output/*`, new branch-gap tests, CHANGELOG).
  Per mission hard rules these were left untouched and excluded from my
  commits. Consequence: `docgen/counts.py --check` reports stale coverage
  provenance for template_active_inference because that session changed
  exemplar sources without refreshing provenance yet.
  **Status: NOT MINE TO FIX** (would require regenerating another session's
  in-flight work).

### Major (scoped, not implemented)

- **M1 — Coverage-provenance automation coupling.** `counts.py --check` fails
  whenever an exemplar's source hash changes without re-running its coverage
  gate. Approach: make counts check emit machine-actionable "rerun command X
  for project Y" artifacts consumed by CI docs-lint; or move provenance
  refresh into each exemplar's pipeline stage. Effort: 1–2 days. Risks: CI
  ordering, provenance semantics. Acceptance: changing an exemplar source
  produces a self-explanatory gate failure naming the exact refresh command.

- **M2 — Test-suite runtime architecture on Python 3.14.** Full infra suite
  depends on coverage sys-monitoring behavior and a bounded-run guardian whose
  cleanup wait can exceed pytest-timeout budgets on loaded machines. Approach:
  (a) audit `coverage` version for 3.14 sysmon performance fixes; (b) revisit
  `_DONE_TIMEOUT_SECONDS` in `infrastructure/core/_bounded_run_guardian.py`;
  (c) consider sharding like CI. Effort: 2–4 days. Risks:
  execution-boundary code is security-sensitive; needs negative controls.
  Acceptance: full local suite completes under a documented wall-time budget
  on 3.14 with zero timeout aborts.

- **M3 — Oversized-module decompositions.** `rendered_snapshot.py` (800) and
  `full_verification.py` (929) sit at/near WARN with ratchets expiring.
  Approach: extract cohesive submodules (snapshot IO vs rendering checks;
  verification facade vs per-gate validators) with import-compat shims.
  Effort: 2–3 days each. Risks: public API churn, downstream imports.
  Acceptance: modules below WARN, exports intact (`check-all-exports` green),
  coverage unchanged or better.

## What I verified but did not change

Everything in the results table above; plus TODO-debt scan (30 py-file matches
are all contract references, not open debt markers; root backlog contract
passes with 0 errors/warnings); docs cross-link audit regenerated cleanly
(55 known false positives, 0 red/yellow flags); `.github/workflows/ci.yml`
structure matches its AGENTS.md documentation (16 jobs, conditional detect
gating).

## Files changed by this pass

- `pyproject.toml` — pip override floor 26.1.2 -> 26.2 (PYSEC-2026-3721)
- `uv.lock` — refreshed (pip 26.2.1)
- `DEEP_PASS_2026-08-21.md` — this report

All other modified files in the working tree belong to the concurrent session
and are intentionally not committed here.

---

## Fourth-pass independent verification record (Dr. PAI, 2026-08-21 ~21:00 PT)

A fourth deep-pass session re-ran the mission against HEAD (`3ea08ab2d`).
Findings: the canonical backlog above, the F-1 timeout fix (`e4dfce5a9`),
and the pip PYSEC-2026-3721 lock floor (`d2ced8304`) are already committed;
this pass independently re-verified them and re-measured the live gate state.
No new code defects found; no changes to files owned by the concurrent
rendering/health session (23-file dirty tree on arrival).

Re-measured results from this session (all run live):

| Check | Command | Result |
| --- | --- | --- |
| F-1 fix holds standalone | `pytest tests/infra_tests/git_hook_smoke/test_tracked_generated_artifacts.py -q` (default 10s pytest-timeout) | 9 passed in 13.34s (single-test rerun) |
| git_hook_smoke tier | `pytest tests/infra_tests/git_hook_smoke -q --timeout=300` | **14 passed in 28.03s** (exit 0) |
| Regression tier | `pytest tests/regression -q --timeout=120` | **55 passed** (exit 0) |
| Ruff lint surface | `ruff check conftest.py docs infrastructure scripts tests projects/templates/` | PASS ("All checks passed!") |
| mypy source paths | `mypy $(... public_scope source-paths)` | PASS, "no issues found in 1559 source files" |
| Bandit | `bandit -r -c bandit.yaml infrastructure scripts` | PASS: 0 High / 0 Medium / 0 Low |
| pip-audit | `pip-audit --skip-editable` | PASS: "No known vulnerabilities found" (confirms d2ced8304) |
| No-mocks semantic inventory | `verify_no_mocks.py --inventory --max-dependency-replacements 0` | clear (dependency_replacement: 0) |
| Tracked secrets | `check_tracked_secrets.py` | PASS ("No high-confidence credentials") |
| Confidentiality guard | `check_tracked_all.py` | projects/fonds/tools/rules all clean (~27s) |
| Generated-artifact guard | `check_tracked_generated_artifacts.py --repo-root .` | PASS (~27s; under the raised 120s cap) |
| Template drift `--strict` | PASS ("no drift detected") |
| Skills manifest + exports | `infrastructure.skills check` / `check-all-exports` | ok / 0 violations |
| Exemplar roster check | `docgen/exemplar_roster.py --check` | OK (24 exemplars in sync) |
| API reference check | `docgen/api_reference.py --check` | up-to-date (25 packages) |
| Publication records check | `docgen/publication_records.py --check` | OK |
| Public template contract | `check_public_template_contract.py` | status: pass, findings: 0 (24 exemplars) |
| Backlog contract | `check_backlog.py` | errors: 0, warnings: 0 |
| Claim bindings | `check_claim_bindings.py` | status=pass (projects=24, bound=15) |
| Module doc coverage | `check_module_doc_coverage.py` | all public modules referenced |
| Prerender validation | `infrastructure.validation.cli prerender projects/templates/template_code_project/manuscript` | "No render-blocking pitfalls" |
| Exemplar test suite | `pytest projects/templates/template_code_project/tests -q` | **246 passed in 215.71s** |

Still-stale items (unchanged disposition, matching the report above):

- F-2 counts coverage provenance for `template_active_inference`: still stale
  (`counts.py --check` fails closed); the concurrent session's dirty diff on
  that exemplar's sources is still uncommitted. Owner must refresh after landing.
- F-4 mirror-shape violations: now four entries — `projects/active/project`,
  `projects/active/test_project`, `projects/working/ap3`,
  `projects/working/Untitled` — all untracked local-only content; two of the
  `active/` strays are empty pipeline scaffolding created during this session's
  window by the concurrent session. Still owner action; confidentiality guard
  confirms nothing tracked.
- Branch is 10 commits behind `origin/main`; not pushed per hard rules.

Deliverable checklist re-confirmed at HEAD: [x] backlog file present with
classified findings + scoping · [x] minor fixes implemented & verified ·
[x] path-scoped local commits of own files only · [x] this summary.

---

# Second-pass independent verification (2026-08-21, later same day)

An independent agent re-ran the assessment from the arrival snapshot
(`0db2afcbb`, main). Findings below are measured live; nothing was taken on
trust from the first-pass report.

## Verified clean (re-executed this pass)

| Gate | Command | Measured result |
| --- | --- | --- |
| Ruff full public lint surface | `public_scope lint-paths` + `ruff check` | All checks passed |
| mypy source paths (1559 files) | `public_scope source-paths` + `mypy` | Success: no issues |
| No-mocks lexical gate | `scripts/audit/verify_no_mocks.py` | Exit 0 |
| No-mocks inventory ceiling 0 | `--inventory --max-dependency-replacements 0` | Status: clear, debt 0 |
| Template drift (`--strict`) | `scripts/audit/check_template_drift.py` | no drift detected |
| Backlog contract | `scripts/audit/check_backlog.py` | 22 stable IDs, 0 errors/warnings |
| Confidentiality guards | `check_tracked_all.py` | projects/fonds/rules/tools clean |
| Tracked secrets scan | `check_tracked_secrets.py` | no credentials found |
| Generated-artifact guard | `check_tracked_generated_artifacts.py` | clean |
| Skills manifests | `skills check` / `check-all-exports` | ok / 0 violations |
| API reference / roster checks | `api_reference.py --check`, `exemplar_roster.py --check` | up-to-date (25 pkgs) / OK (24 exemplars) |
| Bandit over `infrastructure/`, `scripts/` | `bandit -c bandit.yaml -r` | zero findings |
| Unified health (26 gates) | `python -m infrastructure.core.health` | 24/26 PASS; docs-lint and counts timed out at their 300 s gate budget under local load — re-run standalone below |
| Mermaid + cross-link lint | `lint_docs.py` standalone (~10 min) | exit 1 only via `mmdc` per-block timeouts (7 blocks, exit 124) — an environment/puppeteer slowness artifact, not syntax failures; cross-links 0 broken, consistency 0 issues |

## First-pass work confirmed landed

- `48efcd3e2` — first-pass report committed.
- `1efa2f118` — branch-gap tests landed and independently verified here:
  `uv run pytest tests/infra_tests/project/test_workspace_branches.py tests/infra_tests/rendering/test_pipeline_summary_branches.py -q` → **25 passed**.

## New findings this pass

**F1 (Medium, root cause external to tracked code) — `counts.py --check` FAIL:
stale coverage provenance for `template_active_inference`.**
Evidence: standalone run exits 1 with "source hash changed". The working tree
carries uncommitted modifications to that exemplar's `output/data/*`
(`manuscript_variables.json` flips `semantic_ok` true→false,
`sheaf_gluing_certificate.json`, `artifact_provenance.json`, plus manuscript and
report deltas), which change the hashed source state. Per repo contract these
outputs must be regenerated by the canonical pipeline, never hand-edited.
Status: **not fixed** — the dirty files predate this session and belong to a
concurrent writer; touching them would violate the no-revert rule. Disposition:
owner should either complete/regenerate the exemplar run or restore those files,
then rerun its coverage gate and refresh provenance.

**F2 (Minor) — one infrastructure test fails against the dirty tree.**
`test_counts_doc.py::test_active_coverage_workspace_preserves_canonical_semantic_readiness`
asserts empty semantic/sheaf findings but observes "hash eligibility partition is
stale or forged" / "artifact_contract_index.json has incomplete or stale artifact
contract rows" / "sheaf_gluing_certificate.json is not ok" — all three trace to
the same F1 working-tree changes, not to committed code. Everything else in the
non-benchmark suite progressed past it without further failures observed before
the run was superseded.

**F3 (Minor, environment) — benchmark tests hang locally.**
`tests/infra_tests/benchmark/` exceeded both a 120 s and a 300 s per-test
timeout inside `pytest-benchmark`'s pedantic runner on this arm64 macOS host;
excluded from the verification runs. CI remains the authoritative environment
for that tier.

**F4 (Advisory) — dependency drift.** `uv pip list --outdated` shows minor
point-release lag across dev tooling (bandit 1.9.3→1.9.4, coverage 7.13→7.15,
cyclonedx 11.6→11.12, certifi, cffi, charset-normalizer). No security-critical
gap identified; routine `uv lock --upgrade` maintenance, deferred.

## Deliverable checklist (second pass)

- [x] Independent re-verification recorded in this report
- [x] New findings F1–F4 classified with evidence; F1/F2 dispositioned as
      concurrent-writer tree state (fix path documented)
- [x] Path-scoped commit of this report only
- [ ] No push (per mission)

## Addendum — full infra suite result (measured after report drafting)

Parallelized run `pytest tests/infra_tests/ -q -m "not requires_ollama and not
bench" --timeout=600 -n 4` completed in 655s: **8 failed, 10271 passed,
2 skipped**. All 8 failures reproduce against the concurrent session's
in-flight, uncommitted exemplar changes, not against committed state:

- `documentation/test_counts_doc.py::test_active_coverage_workspace_...`,
  `methods/test_methods_cli.py` (2), `methods/test_methods_orchestration.py`,
  `publishing/test_repro_determinism.py::test_every_public_exemplar_declares_output_artifact`
  — all trace to `template_active_inference/output/*` drift from the other
  session's uncommitted regeneration (artifact manifest vs inventory mismatch).
- `rendering/test_mermaid_figure.py` (2) and `validation/docs/test_mermaid_lint.py`
  — mmdc/chrome-headless subprocess timeouts under 4-way parallel load;
  the mermaid lint test passes standalone (1 passed in 4.87s, mmdc present).

No failure is attributable to this pass's changes (`pyproject.toml` pip floor,
`uv.lock`). The pip-audit gate is green after the fix; ruff and mypy are clean.

---

## Fifth-pass independent verification record (ox-alpha session, 2026-08-21 ~21:40 PT)

A further independent session re-ran the mission against HEAD `697f0e397`
(21 local commits ahead of origin/main; diverged, not pushed per hard rules).
Arrival tree: 16 modified files, all under
`projects/templates/template_active_inference/output/*` — the concurrent
rendering/health session's uncommitted regeneration. Left untouched per hard
rules; no untracked strays at exit.

### Re-measured gate state (all run live this pass)

| Check | Command | Result |
| --- | --- | --- |
| Ruff lint (full public surface) | `public_scope lint-paths` -> `ruff check` | PASS ("All checks passed!") |
| Ruff format | `ruff format --check` over infrastructure/, tests/, scripts/, template_active_inference src/tests/scripts | PASS — 1774 files already formatted (both previously-failing files are clean at current HEAD; results-table row for ruff-format above is resolved) |
| mypy source paths | `mypy $(public_scope source-paths)` | PASS (verified in unified-health run) |
| Bandit standalone | `bandit -c bandit.yaml -r infrastructure/ scripts/` | exit 0 (only nosec/comment warnings) |
| No-mocks lexical + inventory | `verify_no_mocks.py --inventory --max-dependency-replacements 0` | clear; dependency_replacement: 0, env isolation 406 |
| Secrets / drift / roster / exports | tracked-secrets, template-drift --strict, exemplar-roster --check, skills check + check-all-exports | all PASS |
| Module line-count gate | `scripts/gates/module_line_count_check.py` | exit 0; WARN-only on pipeline.py (810), rendered_snapshot.py (800), full_verification.py (929) — matches F3 disposition |
| Confidentiality guards | `check_tracked_all.py` | projects/fonds/rules/tools all clean |
| Mirror-shape guard | `check_mirror_symlinks.py` | still fails (exit 1): 3 local-only entries (`projects/active/project`, `projects/working/Untitled`, `projects/working/ap3`) — owner action, nothing tracked |
| Backlog / claim bindings | `check_backlog.py`, `check_claim_bindings.py` | both PASS |

### New finding this pass

F5 (Minor, test flake — commit race in repo_commit assertion).
`tests/infra_tests/core/test_health.py::TestCLI::test_json_output_is_parseable`
failed once with `assert payload["repo_commit"]` -> None, then passed unchanged
on immediate rerun (17.40s). Mechanism: health.py records commit_before and
nulls repo_commit when commit_before != commit_after
(infrastructure/core/health.py:573) — correct fail-closed behavior, but any
git commit landing in the shared checkout during the ~14s CLI run trips it.
Evidence: failure observed exactly while concurrent sessions were committing.
Status: NOT FIXED (deferred as design-intended). A fix would need either a
retry window or GIT_DIR isolation in the test harness; neither is worth the
complexity for a single-writer CI environment. Recorded so the next person who
sees it does not chase a phantom regression.

Also re-confirmed: pytest tests/infra_tests/core/test_cli.py -q -> 23 passed;
test_project_test_matrix.py + test_pdf_latex_helpers.py -> 65 passed;
test_slides_renderer_core.py -> 35 passed, 12 deselected (requires_latex, by
policy); the earlier full-suite autoresearch timeout reproduces only in-suite
(subprocess exceeds the 10s pytest-timeout under load) and passes standalone
(8.31s) — consistent with M2's runtime-architecture scoping.

### Disposition summary

All findings from prior passes remain accurately dispositioned; the
ruff-format row in the first-pass table (_pdf_latex_helpers.py) is now
resolved at HEAD, and the docs-lint/counts 300s-ceiling failures measured
earlier today are fixed by committed timeout-override work (addendum 3).
Remaining open items: M1-M3 scoping, mirror-shape strays (owner), counts
provenance refresh (owner, after landing the exemplar regeneration).
Deliverable checklist re-confirmed: [x] backlog updated · [x] no new
minor/medium code defects to fix · [x] path-scoped commit of this record only
· [x] no push.

---

# Third-pass independent verification (Dr. PAI, 2026-08-21 late PT)

Re-ran the assessment from HEAD (`ddc63efb5`). One new verified fix, plus
independent root-cause attribution for the F-1 timeout failures.

## New fix this pass (verified)

**F-T1 (Medium -> FIXED) — git_hook_smoke timeout failures: root cause is the
global pytest-timeout, not the subprocess cap.** Measured on this checkout:

- `tracked_public_output_leaks()` alone: **37.6 s** (regex scan of every tracked
  public-output text blob; `git ls-files` = 8069 paths)
- full `check_tracked_generated_artifacts.py` run: **41–45 s**
- `tracked_secret_findings()`: **23.2 s**
- global `pyproject.toml:266` `timeout = 10` (thread method) fires long before
  either subprocess cap, so the prior `timeout=30 -> 120` edit could not fix
  the failure on its own (confirmed: test still timed out after that edit).

Fix: added `@pytest.mark.timeout(180)` to
`test_current_repo_has_no_tracked_generated_artifacts` and
`@pytest.mark.timeout(120)` to
`test_current_repo_has_no_high_confidence_tracked_secrets` in
`tests/infra_tests/git_hook_smoke/test_tracked_generated_artifacts.py`
(4–8x headroom over measured scan times). The concurrent session's
subprocess `timeout=120` hunk in the same file is preserved.

Verification: `pytest tests/infra_tests/git_hook_smoke/ -q --no-cov` ->
**14 passed** on 7 consecutive runs (39–57 s wall each; one earlier run failed
once under heavy parallel load before the markers landed; zero failures after).
`ruff check` + `ruff format --check` clean on the file.

## Re-measured gate state this pass

| Gate | Result |
| --- | --- |
| Ruff lint (full public surface) | PASS |
| mypy (1559 source files) | PASS |
| No-mocks lexical + inventory ceiling 0 | PASS (clear, debt 0) |
| Tracked secrets / confidentiality / generated-artifact guards | PASS |
| Template drift `--strict` | PASS |
| Skills check / check-all-exports / api_reference | PASS |
| Backlog contract | PASS (0 errors, 0 warnings) |
| Docs lint cross-links / consistency / doc-pairs | 0 broken / 0 issues / 0 issues |
| Docs lint mermaid | 7 blocks fail via local `mmdc` 30 s-per-block timeouts (environment slowness, matches prior passes' finding; CI uses a dedicated Node/chrome lane) |
| pipeline-smoke infra lane (`stage_01_test.py --infra-only --infra-scope pipeline-smoke`) | **PASS (exit 0)** — the earlier timeout failure is fixed |
| `counts.py --check` | still STALE — concurrent session's uncommitted `template_active_inference` source/output changes; disposition unchanged (owner must regenerate + refresh provenance after landing) |

## Commit scope note

The commit for `test_tracked_generated_artifacts.py` stages only this pass's
hunks (import + two timeout markers) via `git apply --cached`; the concurrent
session's `timeout=120` subprocess hunk remains uncommitted in the working
tree for its owner.

