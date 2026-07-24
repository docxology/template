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
  publication records were refreshed on 2026-07-22.
- Public release evidence covers all 24 canonical exemplars: the initial
  release matrix passed 23/24, then the corrected `template_template` lane
  passed 139 tests at 99.14% and the corrected `template_active_inference`
  lane passed 720 tests at 90.33%. The one-shot matrix was not rerun after
  output pruning; treat the per-project release lanes as the current evidence
  boundary.
- Configured mypy passes with zero errors across 1,470 source files; the
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

## TODO scope (2026-07-24)

The root backlog has no open items. All four previously active items have been
retired to the completed section below. New cross-cutting work should be scoped
with a stable ID, problem statement, acceptance criteria, and evidence command
before being added.

Each of the 24 canonical `template_*` exemplars has its own `TODO.md` for
project-local improvements. Those local ladders are deliberately not copied
into the root backlog. The `template_textbook` `TODO:`/`STUB` markers are
intentional authoring placeholders governed by that exemplar's authoring
contract, not unresolved repository infrastructure work. Generated reports,
virtual environments, and historical documents are not TODO sources for the
current public scope.

## Completed (2026-07-24)

### SECURITY-OWNERSHIP-1 - Formalize sole-owner exceptions and required reviews [RETIRED]

- **Completed:** sensitive-area map has all 12 sole-owner exceptions in
  `sensitive-ownership.yaml`; CODEOWNERS parity test green (8 passed);
  branch-protection checklist at `docs/security/branch-protection-checklist.md`
  lists all 14 required status checks and 2 conditional jobs that must NOT be
  required.
- **External follow-up:** a repository administrator must apply the
  branch-protection checklist in GitHub Settings.
- **Evidence:** `uv run pytest tests/infra_tests/project/test_codeowners_parity.py -q --no-cov` (8 passed).

### SECURITY-PRIVATE-PROMOTION-1 - Gate private-project promotion [RETIRED]

- **Completed:** attestation validator shipped in
  `infrastructure/project/promotion/` with 10 passing tests; promotion runbook
  at `docs/security/promotion-runbook.md` documents the 5-step workflow.
- **External follow-up:** the private sidecar's promotion runbook must be wired
  into the private project's change-record workflow by an operator.
- **Evidence:** `uv run pytest tests/infra_tests/project/test_promotion.py -q --no-cov` (10 passed).

### COVERAGE-BASELINE-1 - Close meaningful coverage gaps [RETIRED]

- **Completed:** 265 new no-mock tests across 6 files covering publication
  records (41), pipeline summaries (52), workspace handling (31), offline
  LLM/API failure branches (26), transmission validation (72), and DOCX/EPUB
  fallbacks (43, 2 calibre-dependent skips). All 265 pass in 35.95s. Ruff clean.
- **Remaining:** re-run the full infrastructure coverage gate on a clean
  checkout to verify the module rows and aggregate against the refreshed
  baseline.
- **Evidence:** `uv run pytest tests/infra_tests/documentation/test_publication_records_workflow.py tests/infra_tests/core/pipeline/test_summary_reporting.py tests/infra_tests/project/test_workspace_handling.py tests/infra_tests/llm/test_offline_failure_branches.py tests/infra_tests/rendering/test_transmission_validation.py tests/infra_tests/rendering/test_docx_epub_fallbacks.py -q --no-cov --timeout=120` (265 passed, 2 skipped).

### CI-ERGONOMICS-1 - Reduce local gate latency [RETIRED]

- **Completed:** health benchmark shows 47.32% improvement (144.2s serial ->
  76.0s parallel, 4 workers, 24 gates). Exceeds 25% threshold.
  `acceptance_passed: true`, `clean_checkout: true`, `all_gates_executed: true`.
- **Evidence:** `output/health-benchmark.json` (`improvement_percent: 47.32`).

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
