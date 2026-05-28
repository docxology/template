# AutoResearch Project TODO

> Project-level roadmap for `template_autoresearch_project` after the survey
> integration and RedTeam hardening pass. Keep this exemplar deterministic,
> offline, evidence-governed, and explicitly unapproved by default.

## Current Best Move

The best next move is consolidation, not broader autonomy. The project now
demonstrates a strong public AutoResearch exemplar: bounded ML execution,
machine-readable artifacts, citation source ledger, deferred review gates, local
security evidence, and manuscript hydration. The next work should make those
surfaces easier to maintain and harder to misread before adding any new research
behavior.

Last verified in this worktree on 2026-05-26 after the compact evidence-report
and loop/statistics consolidation pass:

- Project gate: `77 passed`, `90.53%` project `src/` line+branch coverage.
- Project test-duration measurement: `77 passed in 41.67s`; retained
  schema-fixture setup and the clean-scaffold full-loop check dominate the
  remaining cost.
- Render path: pre-render validation, variable hydration, PDF render, output
  validation, docs lint, strict template drift, Bandit, mypy, `git diff
  --check`, and manuscript hygiene greps passed.
- Report-size guard: default `output/reports/evidence_registry.json` is `88,889`
  bytes, total `output/reports/` is `229,204` bytes, and
  `output/reports/evidence_registry_full.json` is absent unless explicitly
  requested with `TEMPLATE_EVIDENCE_REGISTRY_FULL=1`.
- Generated review artifacts can be ready for review while
  `publication_approved` remains `false`.
- Loop settlement is now recorded in `output/data/autoresearch_phase_ledger.json`;
  figure quality is recorded in `output/data/figure_quality_report.json`; local
  rank-stability and calibration-bin interval diagnostics are generated from the
  shared diagnostic bundle.

## Non-Negotiable Invariants

- [x] Default execution performs no network calls, no LLM calls, no runtime
  dataset downloads, no generated-code execution, and no autonomous publication
  approval.
- [x] `output/data/autoresearch_review_packet.json` and
  `output/data/review_decisions.json` stay machine-distinct between review
  readiness and publication approval.
- [x] Numbered manuscript prose keeps run-derived facts tokenized through
  `{{TOKEN}}` hydration and registry-backed figure blocks.
- [x] Every survey/current-trends citekey stays covered by
  `manuscript/source_ledger.yaml`, `manuscript/references.bib`, and numbered
  manuscript prose.
- [x] `scripts/regenerate_mnist_fixture.py` remains manual maintenance tooling
  only; default pipeline scripts and loop execution must not import or call it.
- [x] Security artifacts remain local integrity evidence only: no external
  signing, no production SLSA claim, no runtime monitoring claim.

## P0 - Land The Current Hardening Safely

- [x] Review the current dirty tree before staging.
  - Files to inspect:
    - `docs/_generated/canonical_facts.md`
    - `infrastructure/autoresearch/`
    - `projects/template_autoresearch_project/`
    - `tests/infra_tests/autoresearch/test_autoresearch.py`
    - `tests/infra_tests/project/test_autoresearch_project_contract.py`
  - Command:
    ```bash
    git status -sb
    git diff --stat
    git diff --check
    ```
  - Expected: only intentional AutoResearch hardening, docs, tests, and
    generated-fact changes are present; no generated `output/` files are staged.

- [x] Re-run the release gate immediately before commit.
  - Command:
    ```bash
    uv run python scripts/01_run_tests.py --project template_autoresearch_project --project-only --quiet
    uv run python -m infrastructure.validation.cli prerender projects/template_autoresearch_project/manuscript --repo-root .
    uv run python projects/template_autoresearch_project/scripts/z_generate_manuscript_variables.py
    uv run python scripts/03_render_pdf.py --project template_autoresearch_project
    uv run python scripts/04_validate_output.py --project template_autoresearch_project
    uv run python scripts/lint_docs.py
    uv run python scripts/check_template_drift.py --strict
    uv run bandit -c bandit.yaml -q -lll -r projects/template_autoresearch_project
    uv run mypy infrastructure/autoresearch projects/template_autoresearch_project/src
    ```
  - Expected: all commands pass; update
    `docs/_generated/canonical_facts.md` if the measured AutoResearch coverage
    changes.

- [x] Add a short commit message that names the durable boundary.
  - Suggested message:
    ```bash
    git commit -m "harden autoresearch review and evidence boundaries"
    ```
  - Expected: the commit does not include private projects or generated output
    trees.

## P1 - Make Manual Approval A First-Class Input

- [x] Add a human-authored approval intake file that is never generated.
  - Create: `projects/template_autoresearch_project/human_review.yaml`
  - Initial content:
    ```yaml
    schema: template-autoresearch-human-review-v1
    publication_approved: false
    reviewer: ""
    reviewed_at: null
    decisions:
      proposal_review: deferred
      evidence_review: deferred
    notes: ""
    ```
  - Rule: generated code may read this file, but must not write or mutate it.

- [x] Add config loading for the manual approval file.
  - Modify: `projects/template_autoresearch_project/src/config.py`
  - Add a small loader such as `load_human_review(path: Path) -> dict[str, Any]`
    that validates:
    - `schema == "template-autoresearch-human-review-v1"`
    - `publication_approved` is a boolean
    - every decision is one of `approved`, `deferred`, `rejected`
    - `reviewed_at` is `null` unless `publication_approved: true`
  - Test: `projects/template_autoresearch_project/tests/test_config.py`

- [x] Route the manual review state into generated review outputs without
  allowing self-approval.
  - Modify:
    - `projects/template_autoresearch_project/src/loop.py`
    - `projects/template_autoresearch_project/src/reports.py`
    - `projects/template_autoresearch_project/src/writers.py`
  - Expected behavior:
    - Missing `human_review.yaml` defaults to unapproved/deferred.
    - `publication_approved: false` remains the default in generated JSON.
    - A true approval is possible only from the human-authored file.
  - Tests:
    - `projects/template_autoresearch_project/tests/test_loop.py`
    - `projects/template_autoresearch_project/tests/test_reports.py`
    - `projects/template_autoresearch_project/tests/test_writers.py`

- [x] Add a validator check that fails on generated self-approval.
  - Modify:
    - `infrastructure/autoresearch/validation.py`
    - `tests/infra_tests/autoresearch/test_autoresearch.py`
  - Expected: if generated review decisions claim approval without a
    human-authored approval source, validation reports a blocking issue.

## P1 - Promote The Source Ledger To A Project Contract

- [x] Define the source-ledger schema next to the manuscript docs.
  - Modify:
    - `projects/template_autoresearch_project/manuscript/README.md`
    - `projects/template_autoresearch_project/docs/configuration.md`
  - Required fields:
    - `citekey`
    - `canonical_url`
    - `source_tier`
    - `checked_as_of`
  - Expected: docs state tests are offline and do not validate live URLs.

- [x] Move ledger validation out of only manuscript-variable tests into a
  reusable project helper.
  - Create: `projects/template_autoresearch_project/src/source_ledger.py`
  - Responsibilities:
    - parse `manuscript/source_ledger.yaml`
    - validate HTTPS canonical URLs
    - validate ISO dates that are not in the future
    - validate allowed source tiers
    - return a stable list of citekeys
  - Test: `projects/template_autoresearch_project/tests/test_source_ledger.py`

- [x] Keep the manuscript regression as an integration check.
  - Modify: `projects/template_autoresearch_project/tests/test_manuscript_variables.py`
  - Expected: this test should call the reusable helper, then verify each
    citekey is present in `references.bib` and numbered manuscript prose.

- [x] Add an optional offline freshness report.
  - Create: `projects/template_autoresearch_project/scripts/check_source_ledger.py`
  - Expected:
    - no network calls
    - exits nonzero if any `checked_as_of` date is future-dated
    - prints source-tier counts
  - Run:
    ```bash
    uv run python projects/template_autoresearch_project/scripts/check_source_ledger.py
    ```

## P1 - Split Oversized Source Modules By Responsibility

- [x] Split `src/ml_task.py` into stable units.
  - Current file: `projects/template_autoresearch_project/src/ml_task.py`
  - Proposed files:
    - `src/ml_data.py`: fixture loading, provenance loading, array validation
    - `src/ml_models.py`: nearest-centroid, softmax, MLP, patch-attention
      primitives
    - `src/ml_training.py`: deterministic SGD loop, schedules, clipping, L2
    - `src/ml_selection.py`: candidate scoring, ranking, tie-breaking
    - `src/ml_task.py`: public orchestration API and dataclasses only
  - Tests to keep green:
    ```bash
    uv run python -m pytest projects/template_autoresearch_project/tests/test_ml_task.py -q
    uv run python scripts/01_run_tests.py --project template_autoresearch_project --project-only --quiet
    ```

- [x] Split `src/figures.py` into figure families.
  - Current file: `projects/template_autoresearch_project/src/figures.py`
  - Proposed files:
    - `src/figures_core.py`: shared Matplotlib helpers, path handling, metadata
    - `src/figures_ml.py`: ML diagnostic figures
    - `src/figures_process.py`: stage matrix, closure flow, lifecycle
    - `src/figures_security.py`: security control matrix and integrity chain
    - `src/figures.py`: compatibility exports
  - Tests:
    ```bash
    uv run python -m pytest projects/template_autoresearch_project/tests/test_writers.py projects/template_autoresearch_project/tests/test_security.py -q
    uv run python scripts/check_template_drift.py --strict
    ```

- [x] Split `src/diagnostics.py` into diagnostics and statistics units.
  - Current file: `projects/template_autoresearch_project/src/diagnostics.py`
  - Proposed files:
    - `src/diagnostics_records.py`: prediction records and candidate rows
    - `src/diagnostics_metrics.py`: F1, kappa, NLL, Brier, top-k
    - `src/diagnostics_intervals.py`: Wilson, bootstrap, McNemar
    - `src/diagnostics_reports.py`: JSON payload builders
    - `src/diagnostics.py`: compatibility exports
  - Tests:
    ```bash
    uv run python -m pytest projects/template_autoresearch_project/tests/test_ml_task.py -q
    uv run mypy projects/template_autoresearch_project/src
    ```

- [x] Keep `src/manuscript_variables.py` below the drift threshold after each
  table/token change.
  - Current split already moved table builders into `src/manuscript_tables.py`.
  - Add future table builders to `src/manuscript_tables.py`; add future source
    validation to `src/source_ledger.py`.
  - Gate:
    ```bash
    uv run python scripts/check_template_drift.py --strict
    ```

## P1 - Version Generated Artifact Schemas

- [x] Add `schema` fields to generated JSON payloads that do not already have
  one.
  - Candidate outputs:
    - `output/data/review_decisions.json`
    - `output/data/autoresearch_review_packet.json`
    - `output/data/ml_candidate_selection_audit.json`
    - `output/data/ml_diagnostic_boundary.json`
    - `output/data/autoresearch_security_profile.json`
    - `output/data/autoresearch_threat_model.json`
    - `output/data/autoresearch_supply_chain_inventory.json`
    - `output/data/autoresearch_integrity_attestation.json`
  - Modify:
    - `projects/template_autoresearch_project/src/reports.py`
    - `projects/template_autoresearch_project/src/writers.py`
    - `projects/template_autoresearch_project/src/diagnostics.py`
    - `projects/template_autoresearch_project/src/security.py`

- [x] Add a schema manifest artifact.
  - Create generated artifact:
    - `output/data/autoresearch_schema_manifest.json`
  - Modify:
    - `projects/template_autoresearch_project/src/writers.py`
    - `projects/template_autoresearch_project/autoresearch.yaml`
    - `projects/template_autoresearch_project/domain_profile.yaml`
    - `projects/template_autoresearch_project/docs/outputs.md`
  - Test:
    - `projects/template_autoresearch_project/tests/test_writers.py`
    - `tests/infra_tests/project/test_autoresearch_project_contract.py`

- [x] Add regression tests for required schema versions.
  - Create: `projects/template_autoresearch_project/tests/test_artifact_schemas.py`
  - Expected: every required generated JSON artifact has either an explicit
    schema field or a documented reason it is a generic data table.

## P2 - Package The Run As A Research Object Without Overclaiming

- [x] Add a local research-object manifest.
  - Generated artifact:
    - `output/data/research_object_manifest.json`
  - Contents:
    - project name
    - generated artifact paths
    - SHA-256 hashes
    - manuscript output paths
    - evidence registry path
    - source ledger path
    - review approval state
  - Rule: call it a local research-object manifest, not RO-Crate compliance
    unless a formal RO-Crate profile is implemented.

- [x] Add manuscript text that names the manifest as packaging evidence.
  - Modify:
    - `projects/template_autoresearch_project/manuscript/02_methodology.md`
    - `projects/template_autoresearch_project/manuscript/03_results.md`
  - Expected: text remains tokenized where run-derived paths or counts appear.

- [x] Add output validation for the manifest.
  - Modify:
    - `scripts/04_validate_output.py` only if the check belongs in shared
      infrastructure, otherwise keep it inside project readiness validation.
    - Prefer project-local validation first to avoid widening Layer 1 scope too
      early.

## P2 - Improve Security Evidence Without Expanding Claims

- [x] Add machine-readable non-claim fields to security outputs.
  - Modify: `projects/template_autoresearch_project/src/security.py`
  - Required fields:
    - `not_external_signing: true`
    - `not_slsa_certification: true`
    - `not_runtime_monitoring: true`
    - `not_network_security_assessment: true`
  - Test: `projects/template_autoresearch_project/tests/test_security.py`

- [x] Add a static no-network import guard for the project runtime.
  - Test: `projects/template_autoresearch_project/tests/test_security.py`
  - Expected: default runtime files do not import `requests`, `httpx`,
    `urllib.request.urlopen`, `socket`, or browser automation modules.
  - Exception: `src/mnist_fixture.py` and
    `scripts/regenerate_mnist_fixture.py` may retain manual maintenance
    download paths with HTTPS/hash/size checks.

- [x] Add an optional inventory export format only after schema versioning.
  - Candidate: CycloneDX-like local JSON.
  - Constraint: docs must say it is not a complete dependency SBOM unless all
    dependency graph inputs are represented.

## P2 - Make Runtime Cost Easier To Control

- [x] Measure which tests dominate the 4 minute project gate.
  - Command:
    ```bash
    uv run python -m pytest projects/template_autoresearch_project/tests --durations=20 -q
    ```
  - Expected: identify whether ML training, render hydration, or loop tests are
    the slowest surfaces.

- [x] Add a fast deterministic fixture for tests that do not need full loop
  execution.
  - Candidate files:
    - `projects/template_autoresearch_project/tests/conftest.py`
    - `projects/template_autoresearch_project/tests/fixtures/`
  - Constraint: do not mock core behavior; use real small payloads and real
    serialization.

- [x] Keep one full-loop integration test.
  - Expected: at least one test still executes
    `run_autoresearch_loop(project_root)` on a clean scaffold.
  - Reason: this is the end-to-end guard against artifact contract drift.

## P3 - Defer New Autonomy And New Domains

- [x] Do not add live literature mining to this public exemplar.
  - Better target: a separate archived/search exemplar or a new optional
    project that can be kept out of the deterministic public CI path.

- [x] Do not add live proof search or Lean autoformalization to this exemplar.
  - Better target: a separate formal-methods project with its own toolchain,
    tests, and failure modes.

- [x] Do not broaden beyond the local MNIST fixture until approval, source
  ledger, schema versioning, and module splits are stable.
  - Reason: a second dataset would multiply outputs and figures before the
    project’s governance surfaces are fully maintainable.

These P3 items are completed as explicit deferrals: the public exemplar remains
deterministic, offline, and scoped to the checked-in local MNIST fixture.

## Done Criteria For The Next Project Pass

- [x] Current hardening is committed cleanly with no generated outputs staged.
- [x] `human_review.yaml` exists and is the only route to true publication
  approval.
- [x] Source-ledger validation lives in reusable project code and remains
  offline.
- [x] Every new generated JSON artifact has a schema version or an explicit
  documented exemption.
- [x] Largest project source files have been split without breaking public
  imports.
- [x] Full gate remains green:
  ```bash
  uv run python scripts/01_run_tests.py --project template_autoresearch_project --project-only --quiet
  uv run python -m infrastructure.validation.cli prerender projects/template_autoresearch_project/manuscript --repo-root .
  uv run python projects/template_autoresearch_project/scripts/z_generate_manuscript_variables.py
  uv run python scripts/03_render_pdf.py --project template_autoresearch_project
  uv run python scripts/04_validate_output.py --project template_autoresearch_project
  uv run python scripts/lint_docs.py
  uv run python scripts/check_template_drift.py --strict
  uv run bandit -c bandit.yaml -q -lll -r projects/template_autoresearch_project
  ```
