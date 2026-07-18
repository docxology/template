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
  publication records were refreshed on 2026-07-17.
- The full public matrix is green: 24/24 projects pass their local coverage
  floors, and the isolated union reports 38,008 statements at 94.85% against
  the 75% combined gate.
- `uv run mypy --strict infrastructure` now passes with zero errors across 695
  source files; the relaxed public-scope ratchet remains a separate gate.
- Roadmap, status, contribution-map, regression-testing, and threat-model
  surfaces were reconciled against the current generated facts and active IDs;
  historical changelog entries remain unchanged.
- The root release boundary is explicit: package/tag `3.5.1`/`v3.5.1` is the
  last root release, the current checkout remains `[Unreleased]`, and the
  separately published standalone `v1.0.1` release is not treated as root
  changelog parity. See [`docs/maintenance/release-boundary.md`](docs/maintenance/release-boundary.md).
- The external GitHub branch-protection requirement for the `Regression Tier`
  check remains an administrator-owned acceptance item; repository files alone
  cannot prove that setting.
- The health sweep now has a bounded four-worker implementation with a serial
  diagnostic mode; the final-tree benchmark reduced wall time from 104.45s
  serial to 70.02s parallel for the same 22 gates. A clean-checkout benchmark
  remains the final acceptance evidence.
- Publication, LLM-boundary, hostile-render, and provenance-metadata controls
  are now shipped and covered by offline negative tests; ownership and private-
  sidecar promotion governance follow-ups remain externally dependent.

## Active backlog

### SECURITY-OWNERSHIP-1 - Formalize sole-owner exceptions and required reviews

- **Problem:** sensitive CI, publishing, credential, guard, rendering, LLM,
  provenance, and cryptographic areas currently have a historical bus factor of
  one.
- **Why it matters:** unavailable or compromised ownership can block or weaken
  review of high-impact changes even when generated CODEOWNERS parity is green.
- **Smallest next step:** refresh the sensitive-area map with explicit
  sole-owner exceptions, required external review classes, and a branch-
  protection checklist that includes the `Regression Tier`.
- **Acceptance:** ownership artifacts and policy identify every exception;
  CODEOWNERS parity remains green; the required-check checklist is handed to a
  repository administrator and is not marked complete from local evidence.
- **Command/evidence:** `uv run pytest
  tests/infra_tests/project/test_codeowners_parity.py -q --no-cov`; attach the
  external branch-protection checklist separately.
- **Out of scope:** inventing second reviewers, changing GitHub team
  membership, or rewriting git history.

### SECURITY-PRIVATE-PROMOTION-1 - Gate private-project promotion

- **Problem:** a private control-plane project may retain unresolved identity,
  authorization, redaction, secret-store, route, MCP, or export-test gaps when
  moved toward active/public/deployed scope.
- **Why it matters:** promotion can turn a local security TODO into a public
  artifact or operational boundary.
- **Smallest next step:** wire the shipped offline attestation validator into
  the private sidecar's promotion runbook and any administrator-controlled
  promotion command before a project enters active/public/deployed scope.
- **Acceptance:** every promotion workflow invokes the validator; incomplete
  attestations are refused, complete or explicitly risk-accepted attestations
  record reviewer/scope/evidence, and private names or secrets do not enter
  public docs.
- **Command/evidence:** `uv run python -m infrastructure.project.promotion
  <attestation.yaml>` plus the complete/incomplete fixture suite in
  `tests/infra_tests/project/test_promotion.py`; no private-project
  authentication is exercised by the public template.
- **Out of scope:** implementing private-project authentication in this public
  template.

### COVERAGE-BASELINE-1 - Close meaningful coverage gaps

- **Problem:** the current baseline is now measured and provenance-backed, but
  meaningful first-party branches remain unevenly exercised beneath the broad
  aggregate totals.
- **Why it matters:** stale percentages and unprioritized gaps create false
  confidence and waste test effort on generated or optional code.
- **Smallest next step:** use the refreshed baseline to add real tests for
  publication records, workspace handling, DOCX/EPUB fallbacks, transmission
  validation, pipeline summaries, and offline LLM/API failure branches.
- **Acceptance:** the current document keeps source dates and provenance;
  each targeted branch gains meaningful no-mock coverage; infrastructure stays
  at least 60%, every public project stays at least 90%, and provenance checks
  pass.
- **Command/evidence:** `COVERAGE_FILE=.coverage.infra uv run pytest
  tests/infra_tests/ --cov=infrastructure --cov-fail-under=60 --timeout=120
  -m 'not requires_ollama'`, plus every public-project coverage report.
- **Out of scope:** coverage theater, mocks/fakes, lowering thresholds, or
  treating live-provider execution as default evidence.

### RUNTIME-SUPPORT-1 - Prepare Python lifecycle transition

- **Problem:** Python 3.10 remains in the supported matrix while its lifecycle
  endpoint approaches; support claims must change coherently.
- **Why it matters:** a partial runtime transition strands contributors with
  mismatched locks, CI cells, package metadata, and documentation.
- **Smallest next step:** decide the supported floor before the 3.10 EOL,
  document the decision, and update `requires-python`, CI, locks, contributor
  docs, and release notes as one change.
- **Acceptance:** every supported-version CI cell and project gate passes with
  no stale version claims or lock drift.
- **Command/evidence:** run the complete CI matrix and each public-project gate
  after the version-floor change; check all lockfiles and `requires-python`
  declarations in the same diff.
- **Out of scope:** dropping a Python version without an explicit release
  boundary or supporting an untested interpreter.

### CI-ERGONOMICS-1 - Reduce local gate latency

- **Problem:** the local health sweep is dominated by sequential documentation
  lint and security checks even when independent inputs are unchanged.
- **Why it matters:** slow feedback encourages skipped gates and makes release
  verification less repeatable.
- **Smallest next step:** repeat the measured serial/parallel comparison from a
  clean checkout after this change is landed, retaining the result manifest.
- **Acceptance:** clean-checkout local health time falls by at least 25% in a
  reproducible benchmark, with every existing gate still executed and no
  changed threshold or skipped failure.
- **Command/evidence:** capture before/after timings for the health command on a
  clean checkout and compare the result manifest to prove every gate ran.
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
