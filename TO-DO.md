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

## TODO scope (2026-07-24)

The root backlog is limited to the items below. Items marked **[LOCAL COMPLETE]**
have their repository-side deliverables shipped; only external administrator
action or ongoing coverage work remains.

Each of the 24 canonical `template_*` exemplars has its own `TODO.md` for
project-local improvements. Those local ladders are deliberately not copied
into the root backlog. The `template_textbook` `TODO:`/`STUB` markers are
intentional authoring placeholders governed by that exemplar's authoring
contract, not unresolved repository infrastructure work. Generated reports,
virtual environments, and historical documents are not TODO sources for the
current public scope.

## Active backlog

### SECURITY-OWNERSHIP-1 - Formalize sole-owner exceptions and required reviews [LOCAL COMPLETE]

- **Problem:** sensitive CI, publishing, credential, guard, rendering, LLM,
  provenance, and cryptographic areas currently have a historical bus factor of
  one.
- **Why it matters:** unavailable or compromised ownership can block or weaken
  review of high-impact changes even when generated CODEOWNERS parity is green.
- **Completed (2026-07-24):** sensitive-area map refreshed with explicit
  sole-owner exceptions in [`sensitive-ownership.yaml`](.github/sensitive-ownership.yaml);
  CODEOWNERS generated block includes all 12 sensitive paths with parity test
  green; branch-protection checklist documented at
  [`docs/security/branch-protection-checklist.md`](docs/security/branch-protection-checklist.md)
  listing all 14 required status checks, 2 conditional jobs that must NOT be
  required, and review requirements.
- **Remaining (external):** a repository administrator must apply the
  branch-protection checklist in GitHub Settings. This cannot be proven from
  repository files alone.
- **Command/evidence:** `uv run pytest
  tests/infra_tests/project/test_codeowners_parity.py -q --no-cov` (8 passed,
  2026-07-24); attach the external branch-protection confirmation separately.
- **Out of scope:** inventing second reviewers, changing GitHub team
  membership, or rewriting git history.

### SECURITY-PRIVATE-PROMOTION-1 - Gate private-project promotion [LOCAL COMPLETE]

- **Problem:** a private control-plane project may retain unresolved identity,
  authorization, redaction, secret-store, route, MCP, or export-test gaps when
  moved toward active/public/deployed scope.
- **Why it matters:** promotion can turn a local security TODO into a public
  artifact or operational boundary.
- **Completed (2026-07-24):** the offline attestation validator is shipped in
  `infrastructure/project/promotion/` with 10 passing tests. The promotion
  runbook is documented at
  [`docs/security/promotion-runbook.md`](docs/security/promotion-runbook.md)
  with a 5-step workflow: prepare attestation, validate attestation, validate
  candidate, compose security decision, record and proceed. The
  `evaluate_promotion_candidate(...)` composite API rejects mismatched project
  names, source-commit mismatches, and uncommitted changes.
- **Remaining (external):** the private sidecar's promotion runbook must be
  wired into the private project's change-record workflow by an operator.
  No private-project authentication is implemented in this public template.
- **Command/evidence:** `uv run python -m infrastructure.project.promotion
  attestation <attestation.yaml>` plus the complete/incomplete fixture suite
  in `tests/infra_tests/project/test_promotion.py` (10 passed, 2026-07-24).
- **Out of scope:** implementing private-project authentication in this public
  template.

### COVERAGE-BASELINE-1 - Close meaningful coverage gaps [LOCAL COMPLETE]

- **Problem:** the current baseline is now measured and provenance-backed, but
  meaningful first-party branches remain unevenly exercised beneath the broad
  aggregate totals.
- **Why it matters:** stale percentages and unprioritized gaps create false
  confidence and waste test effort on generated or optional code.
- **Progress (2026-07-23):** 145 no-mock tests added across 6 modules
  (from 2026-07-22), plus 3 remaining public-function docstrings added to
  infrastructure modules. Infrastructure docstring coverage now zero-gap for
  public functions.
- **Progress (2026-07-24):** additional no-mock tests added for publication
  records, workspace handling, DOCX/EPUB fallbacks, pipeline summaries, and
  offline LLM/API failure branches.
- **Remaining:** re-run the full infrastructure coverage gate (times out at 5
  minutes — run on a clean checkout with ``--benchmark-disable`` and reduced
  parallelism). Use the refreshed baseline to verify module rows and aggregate.
- **Smallest next step:** re-run the infrastructure coverage gate after the
  new tests are landed to verify the module rows and aggregate.
- **Acceptance:** the current document keeps source dates and provenance;
  each targeted branch gains meaningful no-mock coverage; infrastructure stays
  at least 60%, every public project stays at least 90%, and provenance checks
  pass.
- **Command/evidence:** the safe local coverage lane is ``COVERAGE_FILE=.coverage.infra
  uv run pytest tests/infra_tests/ -n 2 --dist loadscope
  --benchmark-disable --cov=infrastructure --cov-report=term-missing
  --cov-fail-under=60 --durations=10 -m "not requires_ollama and
  not requires_docker and not network and not slow and not bench and
  not benchmark and not performance" --timeout=120``; retain the uncached serial
  form with xdist flags removed as the diagnostic oracle, plus every
  public-project coverage report.
- **Out of scope:** coverage theater, mocks/fakes, lowering thresholds, or
  treating live-provider execution as default evidence.

### CI-ERGONOMICS-1 - Reduce local gate latency [COMPLETE]

- **Problem:** the local health sweep is dominated by sequential documentation
  lint and security checks even when independent inputs are unchanged.
- **Why it matters:** slow feedback encourages skipped gates and makes release
  verification less repeatable.
- **Completed (2026-07-23):** health benchmark on clean checkout at
  `30f2bfc` shows **47.32% improvement** (144.2s serial -> 76.0s parallel,
  4 workers, 24 gates, acceptance=PASS). This exceeds the 25% threshold.
  The ruff/ruff-format gates now use the project-pinned version instead of
  the latest unpinned release, eliminating version-mismatch formatting
  failures. Benchmark evidence: `output/health-benchmark.json`
  (`acceptance_passed: true`, `improvement_percent: 47.32`,
  `clean_checkout: true`, `all_gates_executed: true`).
- **Acceptance:** clean-checkout local health time fell by at least 25% in a
  reproducible benchmark, with every existing gate still executed and no
  changed threshold or skipped failure. **MET.**
- **Command/evidence:** `uv run python scripts/maintenance/benchmark_health.py
  --output output/health-benchmark.json --minimum-improvement 25`
  (output/health-benchmark.json: acceptance_passed=true,
  improvement_percent=47.32, clean_checkout=true).
- **Out of scope:** weakening gates, hiding warnings, or introducing a required
  service dependency for local verification.

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
