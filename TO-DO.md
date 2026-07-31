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

## Open cross-cutting work (2026-07-31)

The following items are the remaining infrastructure-level work identified by
the Mahakala adversarial review and the all-exemplar audit. Shipped fixes are
recorded in [`CHANGELOG.md`](CHANGELOG.md); project-local improvements remain
in each canonical exemplar's `TODO.md`.

| ID | Priority | Problem and impact | Smallest next step | Acceptance evidence | Status / Scope |
| --- | --- | --- | --- | --- | --- |
| `PUBLIC-MATRIX-1` | High | The public matrix is not yet a single zero-failure release gate: 23 lanes passed, while `template_active_inference` measured 89.35% against its 90% floor; the run also exposed test-generated output churn. | Run the full public matrix with `--receipt` and finish template_active_inference coverage to 90%. | Receipt module passing; 90% floor met per project; no output drift. | SHIPPED: receipt module, test_runner, CLI arg, 105 new tests, 251 direct tests. 90% floor pending gate rebuild. |
| `RENDERED-PROVENANCE-1` | High | Source-only publication checks can pass while rendered strict audit asks for provenance review. | Add stage/source/config fingerprints and a rendered strict release gate. | Rendered strict publication audit returns zero review-required findings. | Generated outputs and release validation. |
| `CONFIG-FAIL-CLOSED-1` | High | Placeholder tokens, stale injected manuscripts, unconsumed source files survive tolerant paths into release. | Integrate shipped placeholder-token and unconsumed-markdown checkers into CI release pipeline. | `{{TOKEN}}`, `${token}`, stale chapters, unconsumed Markdown fail release command. | SHIPPED: `check_placeholder_tokens()` + `check_unconsumed_markdown()` in publication audit, wired into SOURCE/RENDERED_CHECKERS. |
| `PROJECT-EXECUTION-BOUNDARY-1` | High | Direct stage/library calls need symlink policy and subprocess environment/network boundary. | Centralize lifecycle-link classification; run project hooks with explicit policy. | Traversal, symlink, secret, egress, hook-root negative controls pass. | Does not remove intentional lifecycle links or live research. |
| `SECURE-RUN-1` | High | Secure-run needs distinct output and hash evidence, but hooks run in caller's process boundary. | Add subprocess boundary with secret stripping, root confinement, cleanup. | Hostile hook cannot read credentials, escape project, or outlive failed run. | Steganography and secure orchestration only. |
| `SECRET-SCAN-1` | High | Tracked-blob scan shipped; staged new files not inspected until they enter the index; no rotation handoff. | Add staged-diff scan and credential-rotation handoff. | Tracked and staged scans cover every blob; no value printing; findings link to rotation evidence. | SHIPPED: `staged_diff_secret_findings()` in git_guards, `scripts/audit/check_staged_secrets.py`, `docs/security/credential-rotation-handoff.md`. |
| `PUBLIC-CAPABILITY-PARITY-1` | Medium | Shared exemplar structure doesn't prove runtime parity across formats, hydration, analysis, package identity, Python floor. | Generate capability manifest per project; compare with public roster and CI matrix. | One row per public exemplar; declared capabilities and smoke probes agree. | Inventory and drift detection; no forced feature parity. |
| `RELEASE-METADATA-1` | Medium | DOI/GitHub metadata freshness, installer pinning, live branch protection not fully provable by repo-only gates. | Add credential-free external metadata receipts; pin mutable installers with checksums. | Release preflight records external checks or operator blocker; no mutable curl|sh remains. | External services operator-owned; not simulated locally. |
| `MODULARITY-1` | Medium | Three modules exceed advisory 800-line composability budget. | Split largest infrastructure modules along existing contracts. | `module_line_count_check.py` reports no advisory warnings; API and behavior tests green. | SHIPPED: `checks_publication.py` 932->748 via `checks_publication_validators.py`. |

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