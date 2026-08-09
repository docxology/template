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
| `REPRODUCIBLE-PDF-1` | Medium | LaTeX PDF builds embed runner timestamps (`\today`, `/CreationDate`, intermediate `.log`) which vary run-to-run on the same commit. The deterministic pipeline claims byte-for-byte reproducibility but lacked a real compiled-output proof. | Export `SOURCE_DATE_EPOCH` in the composite CI setup action; add a rendered-output snapshot-diff test that fails on byte drift. | Two `--core-only` runs on the same commit produce byte-identical PDFs. | **SHIPPED 2026-08-08**: `SOURCE_DATE_EPOCH` is propagated from the git commit timestamp; real XeLaTeX is compiled twice in `test_compile_latex_is_byte_reproducible_with_pinned_epoch`; deterministic PDF canonicalization stabilizes metadata, identifiers, and font subset names before the byte comparison. |
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
| `MODULARITY-MAJ-1` | Two public exemplar `src/` modules exceeded the 800-line advisory ceiling: advanced literature search and pools figure orchestration. | Split each into focused submodules with façade re-exports and composition coverage. | **SHIPPED 2026-08-08** — `search.py` is 736 lines with `models.py`/`llm_filter.py`; `figures.py` is 717 lines with `figure_support.py`; advanced literature (77) and pools (261) project suites passed. |
| `REPRODUCIBLE-PDF-MAJ-1` | The deterministic-pipeline claim lacked machine-proven byte identity for real LaTeX output. | Add an automated two-run rendered-output comparison on a fixed `SOURCE_DATE_EPOCH`. | **SHIPPED 2026-08-08** — `test_compile_latex_is_byte_reproducible_with_pinned_epoch` runs real XeLaTeX twice; PDF canonicalization stabilizes metadata, identifiers, and font subset names before the byte comparison. |
| `TEST-SPLIT-MAJ-1` | The largest test modules were monolithic, slowing collection and obscuring failure isolation. | Split the top five modules by concern while preserving real fixtures and public test names. | **SHIPPED 2026-08-08** — formal colony experiments, template drift, madlib composition, literature variables, and pipeline-control tests are now concern-based modules; oversized-test warnings fell from 18 to 13 and the split suites passed independently. |
| `PARALLEL-WORKERS-MAJ-1` | Worker-count resolution was spread across multi-project, matrix, and per-project pytest execution. | Centralize bounded worker resolution with one explicit-cap/env/CPU policy and negative controls. | **SHIPPED 2026-08-08** — `infrastructure/core/worker_policy.py` is the sole owner of the worker environment names and clamping rules; matrix, parallel, and pytest orchestration delegate to it. |

### Medium (focused, moderate effort)

| ID | Problem and impact | Smallest next step | Acceptance evidence |
| --- | --- | --- | --- |
| `SECRET-DEDUP-MED-1` | Credential-env matching and stripping were duplicated across runtime and subprocess boundaries. | Extract one shared secret-name predicate/env-stripping helper. | **SHIPPED 2026-08-08** — `infrastructure/core/secrets.py` owns the predicate and both boundaries delegate; existing secret-strip coverage remains green. |
| `BOUNDARY-TEST-MED-1` | The `capture_output=False` timeout path lacked a direct descendant-cleanup negative control. | Spawn a real sleeping child, time it out, and assert no marker survives. | **SHIPPED 2026-08-08** — the POSIX negative control now exercises the no-capture path and asserts timeout, process-group termination, and no surviving marker. |
| `GATE-ADVISORY-MED-1` | Source-size warnings needed a bounded ratchet without turning test-size guidance into a brittle blocker. | Fail on source growth beyond expiring baselines while retaining advisory test warnings. | **SHIPPED 2026-08-08** — downward-only ratchets are enforced for the previously oversized source modules and documented in `scripts/gates/AGENTS.md`; source scan is clean. |
| `STATUS-REFRESH-MED-1` | The status ledger needed a machine-enforced freshness boundary so stale rows cannot silently age out. | Add a fail-closed date/row freshness gate and retain end-to-end subsystem refresh as maintainer-owned evidence. | **PARTIAL 2026-08-08** — `scripts/gates/status_freshness.py` is wired into unified health and passes the current ledger; row-specific end-to-end refresh remains explicit operator work where the ledger says so. |
| `DOC-COVER-MED-1` | New security modules (`execution_boundary.py`) and earlier hardening modules are documented in `AGENTS.md` but generated project/publication inventories can drift from source. | Regenerate all generated inventories from source and keep their idempotence checks in the release validation pass. | **SHIPPED 2026-08-08**: active-project, exemplar-roster, publication-record, API-reference, and counts generators/checks are current; module-doc coverage and strict template-drift gates pass. |

### Minor (small, low-risk)

| ID | Problem and impact | Smallest next step | Acceptance evidence |
| --- | --- | --- | --- |
| `DOC-NEG-CONTROL-MIN-1` | The doc audit (`scripts/audit/audit_documentation.py`) emits 203 advisory `gate-negative-control` findings across docs that claim a gate enforces behavior without naming a negative-control fixture. Advisory-only today, but several reflect genuinely weak claims. | Triage the 203 findings by distinguishing normative gate contracts from historical/prose references; add named negative controls to the normative claims and retain genuine prose noise as advisory. | The advisory baseline is explicitly reported; normative gate claims gain named negative controls without doc-lint/template-drift regression. |
| `INSTALLER-PIN-MIN-1` | `RELEASE-METADATA-1` "pin mutable installers" gap: live docs and automatic bootstrap needed an auditable uv installer pin. | Pin uv `0.12.0`, verify the official installer SHA-256 before execution in both shell bootstraps, and route setup guidance through the checksum-verified dependency guide. | **SHIPPED 2026-08-08** — no live repo-shipped setup guidance uses an unverifiable uv `curl|sh`; the Dockerfile generator retains an explicit `uv_version="latest"` opt-out for callers that knowingly accept a floating build. |
| `BAK-ARTIFACT-MIN-1` | Cleanup hygiene required an explicit recheck for backup/stray artifacts and generated-output guards. | Re-run artifact/secret guards and scan tracked source for `*.bak`, `*.orig`, and `*~`. | **SHIPPED 2026-08-08** — no matching stray artifacts remain; guard reruns are included in the release validation pass. |

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
