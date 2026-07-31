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
  coverage was 94.47%. This is current evidence for the remaining
  `PUBLIC-MATRIX-1` blocker, not a zero-failure release receipt.
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

## Open cross-cutting work (2026-07-30)

The following items are the remaining infrastructure-level work identified by
the Mahakala adversarial review and the all-exemplar audit. Shipped fixes are
recorded in [`CHANGELOG.md`](CHANGELOG.md); project-local improvements remain
in each canonical exemplar's `TODO.md`.

| ID | Priority | Problem and impact | Smallest next step | Acceptance evidence | Scope boundary |
| --- | --- | --- | --- | --- | --- |
| `PUBLIC-MATRIX-1` | High | The public matrix is not yet a single zero-failure release gate: 23 lanes passed, while `template_active_inference` measured 89.35% against its 90% floor; the run also exposed test-generated output churn. | Add a deterministic per-project matrix receipt with bounded Lean policy, clean-output isolation, and targeted active-inference coverage. | Every roster entry has a passing lane at its declared coverage floor; combined coverage remains at least 75%; no timeout, coverage failure, or output drift receipt. | IN PROGRESS — receipt module, test_runner integration, and CLI arg shipped; template_active_inference: 2 latent bugs fixed, 105 new tests; coverage 88.91→89.35%. |
| `RENDERED-PROVENANCE-1` | High | Source-only publication checks can pass while rendered strict audit asks for provenance review on current-output snapshots. | Add stage/source/config fingerprints and a rendered strict release gate for every public exemplar. | Rendered strict publication audit returns zero review-required findings and every artifact has producer/provenance evidence. | Generated outputs and release validation; no weakening of disposable-output policy. |
| `CONFIG-FAIL-CLOSED-1` | High | Placeholder tokens, stale injected manuscripts, and unconsumed source files can survive tolerant exploratory paths into release. | Add strict release-mode token, source-layout, and rendered-tree freshness validators. | Negative controls for `{{TOKEN}}`, `${token}`, stale injected chapters, and unconsumed Markdown fail the release command. | Strict release/render boundaries; exploratory authoring remains tolerant. |
| `PROJECT-EXECUTION-BOUNDARY-1` | High | Direct stage/library calls still need a complete symlink policy and subprocess environment/network boundary; configured script lexical confinement is now shipped. | Centralize trusted lifecycle-link classification and run project hooks with an explicit non-secret environment and network policy. | Traversal, intermediate-symlink, secret-inheritance, network-egress, and hook-root negative controls pass. | Does not remove intentional private lifecycle links or live research capabilities; requires an explicit opt-in for networked hooks. |
| `SECURE-RUN-1` | High | Secure-run now requires distinct output and fresh hash evidence, but project hooks still run in the caller's process boundary. | Add a reviewed subprocess boundary with secret stripping, root confinement, and process-group cleanup. | A hostile hook cannot read ambient credentials, escape its project, or outlive a failed secure run. | Steganography and secure orchestration only; no cryptographic algorithm redesign. |
| `SECRET-SCAN-1` | High | The repository-wide tracked-blob scan is now shipped, but staged new files are not inspected until they enter the index and no operator rotation receipt is recorded for a future leak. | Add a staged-diff scan and a documented credential-rotation handoff around the shipped high-confidence scanner. | Tracked and staged scans cover every blob, report file/line evidence without printing secret values, block high-confidence credentials, and link any finding to operator rotation evidence. | Detection and handoff only; credential revocation remains operator-owned. |
| `PUBLIC-CAPABILITY-PARITY-1` | Medium | Shared exemplar structure does not prove runtime parity across formats, hydration, analysis, package identity, and Python floor. | Generate one capability manifest from each project and compare it with the public roster and CI matrix. | Manifest has one row per public exemplar; declared capabilities and observed smoke probes agree. | Inventory and drift detection; no forced feature parity between intentionally different templates. |
| `RELEASE-METADATA-1` | Medium | DOI/GitHub metadata freshness, installer pinning, and live branch protection cannot be fully proven by repository-only gates. | Add credential-free external metadata receipts and pin remaining mutable installers/actions with checksums or reviewed versions. | Release preflight records current external checks or an explicit operator blocker; no mutable `curl|sh` or unpinned release installer remains. | External services and administrator settings remain operator-owned and are not simulated locally. |
| `MODULARITY-1` | Medium | Three modules still exceed the advisory 800-line composability budget, increasing review and hidden coupling risk. | Split the largest infrastructure and exemplar modules along existing contracts, preserving public imports. | `module_line_count_check.py` reports no advisory warnings; focused API and behavior tests remain green. | Refactoring only; no behavior or public API changes without a separate contract row. |

Each of the 24 canonical `template_*` exemplars has its own local ladder. The
`template_textbook` `TODO:`/`STUB` markers remain intentional authoring
placeholders governed by that exemplar's contract, not root infrastructure
backlog items. Generated reports, virtual environments, and historical
documents are not TODO sources for the current public scope.

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
