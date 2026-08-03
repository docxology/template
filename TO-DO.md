# Repo TO-DO - upcoming cross-cutting work

> **Design ethos:** modular, intelligent, functional, logged, tested, and
> documented. Real methods only; never mocks or fakes. Every release ships with
> green tests and accurate docs.

This file contains only future work for the template repository as a whole.
Completed work belongs in [`CHANGELOG.md`](CHANGELOG.md); generated facts belong
to their generators; project-specific future work remains in each public
exemplar's local `TODO.md`. The root backlog is intentionally named
`TO-DO.md`.

## Current baseline

- Public scope is generated from `infrastructure.project.public_scope` and
  currently contains 24 canonical exemplars. Consult
  [`docs/_generated/active_projects.md`](docs/_generated/active_projects.md)
  rather than copying the roster here.
- The deterministic advanced-literature release lane has been repaired and
  regenerated from source. Its fixture phase replay is now part of the normal
  project analysis sequence; live retrieval remains an explicit opt-in path.
- Generated checks for counts, coverage provenance, exemplar roster, and
  publication records were refreshed on 2026-07-30.
- The bounded public matrix was rerun across all 24 canonical exemplars on
  2026-07-30. Twenty-three lanes passed their declared project floors; the
  `template_active_inference` lane ran 683 tests with 1 skipped and 51
  deselected, but measured 89.35% against its 90% floor. The combined matrix
  coverage was 94.47%.
- The receipt module is shipped (`infrastructure/core/public_matrix_receipt.py`);
  a full matrix run with `--receipt` is the remaining step.
- Configured mypy passes with zero errors across 1,476 source files; the
  public-scope ratchet remains a separate gate.
- Roadmap, status, contribution-map, regression-testing, and threat-model
  surfaces were reconciled against the current generated facts and active IDs;
  historical changelog entries remain unchanged.
- The root release boundary is explicit: package/tag `3.6.0`/`v3.6.0` is the
  last root release, the current checkout remains `[Unreleased]`, and the
  separately published standalone `v1.0.1` release is not treated as root
  changelog parity. See [`docs/maintenance/release-boundary.md`](docs/maintenance/release-boundary.md).
- The external GitHub branch-protection requirement for the `Regression Tier`
  check remains an administrator-owned acceptance item; repository files alone
  cannot prove that setting. The branch-protection checklist is now documented
  at [`docs/security/branch-protection-checklist.md`](docs/security/branch-protection-checklist.md).
- The health sweep now has a bounded four-worker implementation with a serial
  diagnostic mode; the final-tree benchmark reduced wall time from 104.45s
  serial to 70.02s parallel for the same 22 gates. A clean-checkout benchmark
  remains the final acceptance evidence.
- Publication, LLM-boundary, hostile-render, and provenance-metadata controls
  are now shipped and covered by offline negative tests; ownership and private-
  sidecar promotion governance follow-ups remain externally dependent.
- Python 3.10 remains the declared floor through the 3.6.x minor line; Python
  3.13 now has an infrastructure readiness lane. The breaking-release rule is
  recorded in [`docs/maintenance/python-runtime-support.md`](docs/maintenance/python-runtime-support.md).
- All four root backlog items (`SECURITY-OWNERSHIP-1`,
  `SECURITY-PRIVATE-PROMOTION-1`, `COVERAGE-BASELINE-1`, `CI-ERGONOMICS-1`)
  have their repository-side deliverables shipped as of 2026-07-24. Only
  external administrator/operator action remains for the two security items;
  the coverage and CI-ergonomics items are fully complete.

## Completed cross-cutting work (2026-07-31)

The following items from the prior Mahakala adversarial review and all-exemplar
audit have been shipped. Each item's acceptance evidence exists on disk and has
been verified.

| ID | Problem and scope | Acceptance evidence |
| --- | --- | --- |
| `PUBLIC-MATRIX-1` | Public matrix receipt module with fail-closed output-drift detection; post-coverage output isolation; CLI arg; real-subprocess negative controls. 90% floor pending gate rebuild. | `public_matrix_receipt.py` shipped; 23/24 lanes pass; test output-churn controls verified. |
| `RENDERED-PROVENANCE-1` | Rendered provenance: stage/source/config/output fingerprints plus strict rendered publication validation. Atomic confined writes via `secure_write.py`. Snapshots walk source/config/output with symlink confinement and Git-cache filtering. Wired into Stage 04 validation, publication audit (`check_rendered_provenance`), and CI preflight. | 32 rendered provenance tests + 47 artifact-finalization/web-renderer tests pass. Rendered strict audit returns zero review-required findings on canonical exemplars. |
| `CONFIG-FAIL-CLOSED-1` | Placeholder-token and unconsumed-markdown checkers in publication audit, wired into SOURCE/RENDERED_CHECKERS. | `{{TOKEN}}`, `${token}`, stale chapters, unconsumed Markdown fail release command. |
| `SECRET-SCAN-1` | Index-blob scanner: reads exact A/C/M/R blobs from Git index; verified-gitlink handling; fail-closed unreadable-blob behavior; pre-commit/manual hook; tracked pre-push defense; rotation handoff. | Real-Git partial-stage controls pass in both directions; findings contain only path, line, and kind. |
| `PUBLIC-CAPABILITY-PARITY-1` | Versioned 24-project capability manifest; 48 exact CI lanes; normalized unique package identity; full-minor Python checks; confined hydration smoke; declared-feature probes. | `test_public_capabilities.py` — 34 tests pass in 98s. |
| `MODULARITY-1` | Module line-count compliance: `checks_publication.py` split 932→748 via `checks_publication_validators.py`. | `module_line_count_check.py` reports zero advisory warnings; API and behavior tests green. |
| `SECURE-RUN-1` | Subprocess executor boundary with secret stripping, root confinement, and process-group cleanup for project hooks and analysis scripts. | `infrastructure/core/execution_boundary.py`: `run_bounded_subprocess` (fresh process group, `killpg` on timeout so no orphaned descendants), `build_bounded_env` (credential stripping), `validate_hook_root` (root confinement), `classify_lifecycle_link`. Wired into `setup_hook.run_project_setup_hook` and `pipeline.hooks.run_stage_hooks` and `analysis_pipeline.run_analysis_script`. 14 boundary + 4 setup_hook + existing pipeline/analysis tests pass; hostile hook cannot read credentials or outlive a timed-out run. |
| `PROJECT-EXECUTION-BOUNDARY-1` | Centralized lifecycle-link classification and project-hook execution with explicit traversal, symlink, secret, egress, and hook-root policy. | `execution_boundary.classify_lifecycle_link` + `validate_hook_root` negative controls (traversal, symlink escape, hook-root) pass; `secret_env` allow-list honored; egress_check refuses launch in negative control. |

## Open cross-cutting work (2026-07-31)

The following items remain open. Shipped fixes are recorded in the completed
section above and in [`CHANGELOG.md`](CHANGELOG.md); project-local improvements
remain in each canonical exemplar's `TODO.md`.

| ID | Priority | Problem and impact | Smallest next step | Acceptance evidence | Status / Scope |
| --- | --- | --- | --- | --- | --- |
| `RELEASE-METADATA-1` | Medium | DOI/GitHub metadata freshness, installer pinning, live branch protection not fully provable by repo-only gates. | Add credential-free external metadata receipts; pin mutable installers with checksums. | Release preflight records external checks or operator blocker; no mutable curl|sh remains. | External services operator-owned; not simulated locally. |
| `REPRODUCIBLE-PDF-1` | Medium | LaTeX PDF builds embed runner timestamps (`\today`, `/CreationDate`, intermediate `.log`) which vary run-to-run on the same commit. The deterministic pipeline claims byte-for-byte reproducibility but lacks `SOURCE_DATE_EPOCH` propagation to the TeX build chain. | Export `SOURCE_DATE_EPOCH` in the composite CI setup action; add a rendered-output snapshot-diff test that fails on byte drift. | Two `--core-only` runs on the same commit produce byte-identical PDFs. | SHIPPED: `SOURCE_DATE_EPOCH` propagated from git commit timestamp in `.github/actions/setup-python-env/action.yml`; rendered-snapshot fingerprint infrastructure exists; full two-run LaTeX byte-diff remains a manual verification. |
| `RELEASE-TEST-GATE-1` | Medium | The release workflow ran only static contracts (root contract, capability manifest, export smoke, rendered audit) — a release tag could be cut while the commit's test matrix was red. | Add a bounded executable test gate to the release workflow; wire the public-matrix receipt into CI. | Release runs pipeline-smoke infra lane + no-mocks gate on the exact tagged SHA before publishing; receipt produced by scheduled CI job. | SHIPPED: release.yml gained "Verify core test contract on tagged SHA" step; CI lint gained strict template-drift gate; regression tier now asserts non-empty collection (55 tests); new scheduled `public-matrix-receipt` CI job uploads the receipt artifact. |
| `NO-MOCK-CLAIM-1` | Medium | The "No mocks or fakes" README claim is lexically true but semantically weak against hand-rolled stubs. | Add a hand-rolled-fake heuristic to the advisory inventory; reword the README claim. | `verify_no_mocks.py --inventory` reports hand-rolled fakes; README uses scoped wording. | SHIPPED: `scan_hand_rolled_fakes()` heuristic (Fake*/Stub*/Dummy* patterns) wired into `verify_no_mocks.py --inventory`; README scoped. |
| `TRACKED-OUTPUT-BUDGET-1` | Minor | The generated-artifacts guard has a 50MB blind spot per file and relies on a path allowlist that may not cover new exemplars. | Add per-file advisory ceiling; make budget check fail-closed on any tracked binary approaching the hard cap. | `check_tracked_generated_artifacts.py` flags single files near the cap. | SHIPPED: `PUBLIC_TEMPLATE_OUTPUT_MAX_SINGLE_FILE_BYTES = 20MB` advisory ceiling wired into `public_template_output_budget_findings()`; test added. |
| `NO-MOCK-WORDING-1` | Minor | The README "No mocks" claim uses `pytest-httpserver` as an example of a permitted mock, which contradicts the headline. | Reword `README.md:525` to `README.md:535` to say "No unit-level mock frameworks; HTTP boundaries use an in-process test server." | README phrasing is scoped and the contradiction is resolved. | Minor documentation accuracy. |

## Scoped improvement backlog (2026-08-03)

Deep review of the template repo across source/architecture, tests/coverage,
docs/generated facts, and CI/gates/security (supplemented by a 4-agent
parallel review pass). Findings are tiered **Major / Medium / Minor**; each
carries a stable ID, exact path, problem, smallest next step, and acceptance
evidence. Verify measured counts from source before starting any item (the
`module_line_count_check --include-tests` numbers below are snapshots).

### Major (high-impact, larger effort)

| ID | Problem and impact | Smallest next step | Acceptance evidence |
| --- | --- | --- | --- |
| `MODULARITY-MAJ-1` | Two public exemplar `src/` modules exceed the 800-line advisory ceiling and grow unboundedly: `template_advanced_literature_review/src/multi_phase/search.py` (826), `template_pools_rules_tools/src/figures.py` (815). Splitting keeps exemplars maintainable and the advisory gate honest. | Split each into cohesive submodules (e.g. `search.py` → query/rerank/filter; `figures.py` → per-chart modules) with __init__ re-exports; keep `module_line_count_check` WARN-free; add a composition smoke test. | `module_line_count_check.py` emits zero WARN for those two files; exemplar project test suites still green. |
| `REPRODUCIBLE-PDF-MAJ-1` | `REPRODUCIBLE-PDF-1` is marked SHIPPED but its acceptance evidence ("full two-run LaTeX byte-diff") remains a *manual* verification — the deterministic-pipeline claim is not machine-proven. `test_determinism.py` covers `SOURCE_DATE_EPOCH` injection only. | Add an automated two-run rendered-output snapshot-diff test that renders `--core-only` twice on the same commit and asserts byte-identical PDF/digests, wired into CI. | Two automated runs on one SHA produce byte-identical PDFs; new test is a required gate. |
| `TEST-SPLIT-MAJ-1` | 17 test modules exceed the 800-line advisory ceiling (largest: `template_formal/tests/colony/test_colony_experiments_extended.py` 1826, `test_check_template_drift.py` 1360, `template_madlib/tests/test_composition_and_analysis.py` 1157). Monolithic test files slow collection and obscure failure isolation. | Split the top 5–6 test files by concern (rename classes, keep public test names), run each sub-file independently. | `module_line_count_check --include-tests` WARN count drops materially; full suite green. |
| `PARALLEL-WORKERS-MAJ-1` | Parallel project/test execution spreads worker-count resolution across at least three sources: `infrastructure/core/pipeline/multi_project_parallel.py` (`_resolve_max_workers` line 239, over `MULTI_PROJECT_MAX_WORKERS`), `infrastructure/core/project_test_matrix.py` (bounded `workers` param → `ThreadPoolExecutor`), and `infrastructure/core/pytest_orchestration.py` (inner-per-project xdist, `PYTEST_XDIST_WORKERS` / `TEMPLATE_PROJECT_WORKERS`). Independent precedence/cap rules can drift and cause surprising CPU/contention in CI. | Centralize worker-count resolution in one helper (`os.cpu_count()`-bounded, env-override, explicit-cap, one no-mock negative-control test) and have all three call sites delegate. | `grep -l "MULTI_PROJECT_MAX_WORKERS\|PYTEST_XDIST_WORKERS\|TEMPLATE_PROJECT_WORKERS" infrastructure/` resolves to one shared owner; matrix/bench tests pass. |

### Medium (focused, moderate effort)

| ID | Problem and impact | Smallest next step | Acceptance evidence |
| --- | --- | --- | --- |
| `SECRET-DEDUP-MED-1` | Credential-env regex and stripping are duplicated in `infrastructure/core/runtime/_python_env.py:18` (`_SECRET_ENV_NAME`) and `infrastructure/core/execution_boundary.py:38` (`_SECRET_ENV_NAME` + `build_bounded_env`). Two sources can drift, silently weakening one boundary. | Extract a single shared secret-name predicate/env-stripping helper (e.g. `infrastructure/core/secrets.py`), have both modules delegate; drop the duplicate regex. | `grep _SECRET_ENV_NAME infrastructure/ --include=*.py | wc -l` == 1; existing secret-strip tests pass. |
| `BOUNDARY-TEST-MED-1` | `run_bounded_subprocess(capture_output=False)` timeout path (used by `analysis_pipeline.run_analysis_script` with `float("inf")`) has no direct timeout negative-control test; only the `capture_output=True` path is covered. | Add a `capture_output=False` spawn-that-sleeps + timeout test asserting `timed_out=True` and no surviving descendant. | New test passes; existing analysis_pipeline tests still green. |
| `GATE-ADVISORY-MED-1` | `module_line_count_check` emits only advisory WARNs (exit 0) for oversized src/test modules, so the "thin module" discipline is unenforced. | Introduce a bounded ratchet: fail on any *source* module ≥950 lines (already the fail threshold) and on regressions above an allowlist; keep test WARNs advisory. | Gate still green on current tree but fails if `search.py`/`figures.py` grow further; documented in `scripts/gates/AGENTS.md`. |
| `STATUS-REFRESH-MED-1` | `STATUS.md` "Last updated" is 2026-07-22, but six subsystem rows (orchestration, rendering, validation, steganography, secure-run, discovery) were last manually verified **2026-05-21**, approaching/over the 6-month dormancy refresh target. | Re-run each subsystem's verification step (per `STATUS.md` "How to refresh a row") and update dates/evidence; add an automated freshness check. | `STATUS.md` shows no row older than 6 months; a gate flags future staleness. |
| `DOC-COVER-MED-1` | New security modules (`execution_boundary.py`) and earlier hardening modules are documented in `AGENTS.md` but `docs/_generated/active_projects.md` (Jul 22) and `publication_records.md` (Jul 22) predate more recent regeneration (Aug 3) — generated-facts drift risk. | Regenerate all `docs/_generated/*` from source via their generators and commit; add a `--check` CI lane. | `docs/_generated/active_projects.md` + `publication_records.md` timestamps align with siblings; `check_template_drift --strict` clean. |

### Minor (small, low-risk)

| ID | Problem and impact | Smallest next step | Acceptance evidence |
| --- | --- | --- | --- |
| `DOC-NEG-CONTROL-MIN-1` | The doc audit (`scripts/audit/audit_documentation.py`) emits 59 advisory `gate-negative-control` findings across docs that claim a gate enforces behavior without naming a negative-control fixture. Advisory-only today, but several reflect genuinely weak claims. | Triage the 59 (sample read each); fix the ones that describe testable gates (add "negative control: X fails"), leave genuine prose noise flagged-advisory. | Advisory count drops; no doc-lint/template-drift regression. |
| `INSTALLER-PIN-MIN-1` | `RELEASE-METADATA-1` "pin mutable installers" gap: docs/doctor reference `curl … | sh` installers (e.g. `astral.sh/uv/install.sh` at `infrastructure/doctor/detectors/tooling.py:25`, `docs/guides/getting-started.md:75`) without a checksum. | Document the pinned version + expected SHA-256 for the referenced uv installer; add a note to the dependency-management doc; no functional change. | No repo-shipped installer guidance references an unverifiable `curl|sh` without a checksum note. |
| `BAK-ARTIFACT-MIN-1` | Cleanup hygiene: older `.bak`-style or stray build artifacts (e.g. in `infrastructure/steganography/kmyth/`, cleared earlier) — confirm none remain and the generated-artifacts guard covers new exemplars' output. | Re-run `check_tracked_generated_artifacts.py` and `scripts/audit/check_staged_secrets.py`; grep for `*.bak` outside gitignored vendored dirs. | Zero stray `.bak`/build artifacts in tracked tree; guards pass. |

## Backlog conventions

- IDs are stable and are never silently reused. Each active item must retain a
  problem, impact, smallest next step, acceptance command/evidence, and scope
  boundary.
- Retire an item only after its command, diff, generated artifact, and relevant
  regression evidence exist on disk in the same verification pass.
- Re-baseline measured facts instead of copying old numbers into this file.
- Keep private or rotating project names out of public docs; link to the
  generated active-project roster.
- Preserve the no-mocks policy, project coverage floors, confidentiality
  guards, and generated-artifact guard when closing work.
