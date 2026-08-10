# Exemplar backlog history

This review record preserves completed-work evidence that was removed from the
future-only `projects/templates/*/TODO.md` files. The TODO files are planning
inputs, not release notebooks; current measured status belongs in
`docs/_generated/COUNTS.md`, project output receipts, and the generated
publication records. This record intentionally names the source surface and
the evidence class without turning completed work back into an active task.

## Archived 2026-08-02 publication and accuracy passes

| Exemplar | Former TODO section | Preserved evidence |
| --- | --- | --- |
| `template_eda_notebook` | `2026-08-02 publication pass` | Project suite, coverage, prerender, drift, render-error, dataset-statistic, version-parity, notebook-launch, and deterministic-generator evidence were recorded in the project TODO and regenerated outputs. The generator deliberately preserves the fixture contract rather than claiming byte identity. |
| `template_literature_meta_analysis` | `2026-08-02 publication-pass evidence` / `Fixed in this publication pass` | Offline corpus tests, render and artifact validation, retrieval-engine ledger reconciliation, figure/citation corrections, and full-text license/checksum boundaries were recorded and remain represented by project outputs and tests. |
| `template_gold_refinement` | `2026-08-02 review-and-render pass` | Config-shape synchronization, cross-reference repair, metadata parity, full pipeline render/validation, and manuscript-token verification were recorded in the project review evidence. |
| `template_methods_paper` | `Pass log` | Gate-count derivation, exact claim-ledger binding, deterministic compiler checks, documentation parity, and the full render/validation pass were recorded in project tests and generated outputs. |
| `template_redacted_report` | `Log` | Redaction-count correction, residual-risk taxonomy repair, catalog/documentation completion, config parity, deterministic artifact validation, manuscript-to-audit binding, and the stable-raster deferral were recorded in the project evidence. |
| `template_registered_report` | `Pass log (2026-08-02)` | Registration schema parity, review-packet and figure regeneration, sensitivity-analysis binding, deviation-ledger checks, and deterministic demonstration-study evidence were recorded in the project outputs. |
| `template_search_project` | `2026-08-02 integrity fixes` | Machine-local path removal, stale deep-search evidence refresh, dead-module reference repair, catalog completion, and test-inventory parity were recorded in project outputs and tests. |
| `template_textbook` | `Pass 2026-08-02` | Example-config shape parity, documentation inventory, cross-reference repair, render-quality fixes, catalog completion, and worked-number verification were recorded in the project review evidence. |

## Archived completion notes

| Exemplar | Former completion surface | Preserved evidence |
| --- | --- | --- |
| `template_autoresearch_project` | `Shipped` / empty `Medium` section | Source-ledger freshness, declarative loop phases, evidence overview, benchmark-boundary, and source-ledger contract work remain represented by their generated artifacts and focused tests. |
| `template_autoscientists` | `Fixes completed in this pass` | Claim-ledger correction, test/documentation inventory parity, config-shape synchronization, manuscript notation repair, and regenerated evidence remain in the project source and outputs. |
| `template_code_project` | `Accuracy pass` / `Fixed in this pass` | Optimizer-caption, threshold, token-leak, documentation inventory, catalog, and regenerated pipeline evidence remain in source, tests, and output receipts. |
| `template_formal` | dated `Round-*` and `Still open` sections | Formal theorem expansion, experiment/ablation history, typed negative controls, publication accuracy, catalog synchronization, and remaining scientific-depth limitations remain in `ISA.md`, formal specs, source tests, and generated artifacts. |
| `template_madlib` | completed bullets in integrity/test ladders | Version/config, output-validator, digest, token-provenance, and review-packet contract work remains in source-owned validators and tests. |
| `template_newspaper` | `Review fixes completed` | Version/typography/coverage/config/catalog corrections and canonical fictional-edition regeneration remain in the project source, tests, and render reports. |
| `template_pitch_deck` | `Fixes completed in this pass` | Schema, content, figure-flow, transactional audit, and publication-boundary corrections remain in project tests and generated deck evidence. |

## Retention rule

Future TODO entries may cite this record for context, but a completed item is
not reopened here. New claims require a source producer, a proving artifact,
an acceptance command, and a failing negative control before entering an
active backlog table.

## Archived 2026-08-09 future-only backlog migration

### `template_active_inference`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

Current evidence (re-run the commands below to refresh; live counts, coverage,
and timings are read from
[`docs/_generated/COUNTS.md`](../_generated/COUNTS.md), not pinned
here as a hardcoded date):

```bash
uv run python scripts/validate_outputs.py
uv run python scripts/compose_manuscript.py --validate-only --strict
uv run python scripts/check_documentation_contract.py --check
uv run python scripts/generate_method_inventory.py --check
uv run pytest tests/test_figures.py tests/test_figure_style.py tests/test_semantic_extensions.py tests/gates/ -q
COVERAGE_FILE=/tmp/template_ai_publication.coverage uv run pytest tests/ --cov=src --cov-fail-under=90 --durations=20 -q
```

Observed in this pass: prerender, PDF render, output validation, output copy,
and strict template-drift checks passed. The combined PDF rendered as 61 pages
with zero `^! ` LaTeX log errors and zero unresolved `??` references. The
publication-readiness pass regenerated animation, integration-audit,
sheaf-track, manuscript-variable, scholarship, figure, and method-inventory
artifacts before validation. The canonical output validation is green for the current
artifact tree, including the 23 registered figures, GIF evidence, auxiliary
visualization classification, 21 connected scholarship rows, and toy-only
scope-boundary checks. The source artifact contract now records exhaustive
finite model-checking witnesses and refreshes provenance after final artifact
writes, preventing fixed-point hash drift. A full suite run is retained as a
slow end-to-end gate; the first concurrent run observed 781 passed, 4 failed,
1 skipped, with 93.58% coverage, while later focused refresh tests remained
resource-sensitive under the shared 24-agent workload. The full suite runs via
`uv run pytest tests/ --cov=src --cov-fail-under=90` (from the project
directory; prefix both paths with the exemplar folder when running from the
template root); live test counts, coverage, and timings are read from
[`docs/_generated/COUNTS.md`](../_generated/COUNTS.md), not pinned here.


## Promotion rule

A future capability becomes live only after it has a configured producer,
deterministic artifact, manuscript consumer, typed claim evidence, semantic
restriction, validation gate, and failing negative control. Prefer deepening
stable canonical tracks over adding versioned `_vN` siblings.

| Requirement | Minimum proof before promotion |
| --- | --- |
| Producer | Configured script or renderer in the analysis DAG |
| Artifact | Deterministic file under `output/data/`, `output/reports/`, or `output/figures/` |
| Manuscript consumer | Bound IMRAD fragment or generated evidence table |
| Typed claim evidence | Claim-ledger predicate with explicit field, expected value, tolerance, or list predicate |
| Semantic restriction | Certificate field that catches disagreement, missing evidence, or stale output |
| Validation gate | `validate_outputs`, `validate_manuscript`, `lake build`, or project test |
| Negative control | Test that mutates artifact/config/claim text and proves the gate fails |


## Ordered improvement ladder

1. Preserve the current deterministic toy claims, schema contracts, and copied
   output parity through the standard monorepo pipeline.
2. Tighten existing lane validators and negative controls before expanding the
   manuscript surface.
3. Add empirical, network, LLM, private-data, or non-toy claims only after the
   blocked major-scope ladder below supplies the required provenance,
   licensing, privacy, and evidence predicates.


### `template_advanced_literature_review`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

Run from the template repository root:

```bash
uv run pytest projects/templates/template_advanced_literature_review/tests/ --cov=projects/templates/template_advanced_literature_review/src --cov-fail-under=90
uv run python scripts/audit/check_template_drift.py --strict --project templates/template_advanced_literature_review
uv run python scripts/docgen/exemplar_roster.py --check
```

Live test counts and coverage snapshots belong in `../../../docs/_generated/COUNTS.md`.


## Ordered improvement ladder

1. Preserve multi-phase corpus integrity with explicit fixture/live classification and source provenance.
2. Add focused validators for phase boundary enforcement and cross-phase consistency checks.
3. Expand LLM filtering calibration with domain-specific positive/negative controls.
4. Complete phase provenance tracking across all pipeline stages.
5. Document advanced multi-phase patterns for replication in other domains.
6. Refresh generated docs after any multi-phase surface changes.


## Promotion Rule

Move an item out of this file only after its source producer, generated artifact, documentation, and focused tests are updated together AND multi-phase provenance is verified throughout the pipeline.


### `template_autoresearch_project`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

Current validation is the monorepo public-template gate set: per-project pytest
with 90% `src/` coverage, strict template drift, prerender validation, and the
normal analysis/render/validate/copy pipeline. This TODO records future work
only; prior evidence belongs in generated artifacts, reports, tests, and the
README/AGENTS contract.

Latest measured validation is regenerated by the public-template gates; do not
copy historical counts into this backlog.

- Project-only gate (`scripts/pipeline/stage_01_test.py --project-only`):
  370/370 tests passed, 96.5% `src/` coverage (≥ 90% required).
- Manuscript prerender (`infrastructure.validation.cli prerender`): clean, no
  render-blocking pitfalls or undefined citations.
- Analysis (stage_02): both declared scripts (`run_autoresearch_loop.py`,
  `z_generate_manuscript_variables.py`) exited 0.
- Render (stage_03): combined PDF generated; 0 `^! ` LaTeX errors in logs;
  0 unresolved `??` in extracted text; 38 pages.
- Validation (stage_04): 8/8 checks green (PDF, transmission bookends,
  markdown, output structure, figure registry, evidence registry, project
  design overlays, artifact manifest), with a rendered-provenance receipt.
- Template drift (`check_template_drift.py --strict`): no drift detected.
- Manifest: 117 attested stable outputs, including transmission figures,
  `manuscript_composition.json`, and `output/web/favicon.ico`.

Live test counts and coverage are read from
[`docs/_generated/COUNTS.md`](../_generated/COUNTS.md), not pinned
here. Edge-case coverage lives in `tests/test_edge_{config,ledger,loop,gates}.py`
and manuscript-token/format helpers in `tests/test_format_helpers.py`; keep both
green as the loop surfaces evolve.


## Ordered improvement ladder

1. Preserve review/publication separation and offline deterministic execution.
2. Keep source-ledger, evidence-overview, benchmark-boundary, and module-size
   gates green while refactoring.
3. Add a second task adapter only after current schemas and review packets stay
   stable through another full public-template verification pass.
4. Version reusable review-packet schemas before exposing downstream tooling.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AR-REVIEW-BOUNDARY-1` | Minor | Human approval boundary | self-approval regression receipt | project review-artifact tests | generated approval without `human_review.yaml` must fail |
| `AR-MODULE-WATCH-1` | Minor | Module-size drift gate | module-size report | strict drift gate | oversized logic hub must fail the gate |
| `AR-METHOD-ADAPTER-1` | Major | Stable loop/report schemas | second deterministic adapter receipt | project suite and evidence validation | network or generated-code adapter must be unavailable |
| `AR-REVIEW-PACKET-V2` | Medium | Review-packet schema v1 | migration and v2 receipt | packet compatibility tests | v2 self-approval or unknown version must fail |


### `template_autopoiesis`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Project tests and coverage: the exemplar gate collected 512 items; observed 511 passed, 1 skipped, 0 failed, with 96.81% coverage on the exemplar-only run. The one skip is the pre-existing signal-domain first-primitive negative-control parametrization (the second signal primitive supplies that control). The manuscript's `{{TEST_COUNT}}` / `{{COVERAGE_PCT}}` tokens come from the render-time measurement in `src/manuscript_variables.py::measure_test_summary`, never a hand-authored number.
- Prerender validation passed: no render-blocking pitfalls or undefined citations.
- Stage-02 analysis completed 7/7 declared scripts (coverage measurement, figure assets, cover art, archetype realization, full-child realization, sealing, manuscript variables).
- Stage-03 rendered the combined PDF (19 pages) and HTML successfully; render logs contain 0 `^! ` errors and the PDF contains 0 `??` markers.
- Stage-04 passed PDF, transmission-bookend, Markdown, output-structure, figure-registry, evidence-registry, design-overlay, and artifact-manifest checks.
- Stage-05 copied 48 publication files to `output/templates/template_autopoiesis/`.
- Strict template drift reported no drift.
- The renderer still reports non-blocking preamble-recovery warnings because `preamble.md` is not fenced as one LaTeX block; this remains a cleanup item below.


## Ordered improvement ladder

1. Eliminate the remaining test skip by selecting the first available negative-control primitive per domain, then regenerate measured outputs.
2. Extend mutation meta-gate coverage across all domains and kernels.
3. Add the archetype-selection filter to the configurable surface.
4. Finish `SPEC.md` Phase 10 and re-sync it with the declared grammar.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AUTOPOIESIS-MUTATION-1` | Medium | Existing mutation meta-gate | per-domain mutation report | `uv run pytest projects/templates/template_autopoiesis/tests -q` | removing a domain guard must fail the mutated case |
| `AUTOPOIESIS-ARCHETYPE-1` | Medium | Config schema extension | filtered child manifest | project validator plus generated-child integrity tests | unknown archetype filter must fail closed |
| `AUTOPOIESIS-SPEC-1` | Major | Grammar/spec lockstep | `SPEC.md` Phase 10 checklist | strict drift and spec-contract tests | fenced preamble/spec mismatch must fail validation |


### `template_code_project`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_code_project/manuscript --repo-root .`
- Project tests and coverage: `uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-fail-under=90`
- Stage 02 analysis must write `output/data/optimization_results.csv` before strict manuscript-variable generation: `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_code_project`
- Stage 03 manuscript render: `uv run python scripts/pipeline/stage_03_render.py --project templates/template_code_project`
- Stage 04 output validation: `uv run python scripts/pipeline/stage_04_validate.py --project templates/template_code_project`
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Code quality: `uv run ruff check projects/templates/template_code_project/src/` and `uv run mypy projects/templates/template_code_project/src/` must both pass clean.
- Benchmark reproducibility: tracked benchmark reports and figures contain only deterministic facts; wall-clock timing is logged as a runtime diagnostic, and two-run byte-equality tests enforce the boundary.
- Live test count and measured coverage percentage → [`docs/_generated/COUNTS.md`](../_generated/COUNTS.md) (regenerated, never hardcoded here; both numbers drift faster than this file).


## Ordered improvement ladder

1. Preserve the strict analysis-to-manuscript variable contract.
2. Add focused validators for any new generated artifact family.
3. Expand benchmark scenarios only with deterministic seeds, expected-shape tests, and documented claim boundaries.
4. Refresh generated docs after any public-surface change.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `CODE-OPTIMIZER-NEG-1` | Minor | Deterministic objective fixtures | optimizer claim negative-control test | `uv run pytest tests/regression/projects/template_code_project -q --no-cov` | changing the objective must fail the pinned claim |
| `CODE-DASHBOARD-SCHEMA-1` | Medium | Dashboard producer schema | dashboard schema receipt | project test gate and artifact validator | missing chart field must fail schema validation |
| `CODE-SUBPROCESS-1` | Medium | Shared subprocess policy | wrapper inventory row | `uv run python scripts/audit/check_claim_bindings.py` plus project gate | missing timeout/cwd policy must fail the inventory |


### `template_data_descriptor`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Project tests exercise descriptor loading, schema hashing, uniqueness checks, file inventory gates, field constraints, metadata-only release manifests, publication-readiness scoring, byte-level descriptor↔file verification (digest + row reconciliation), plot-ready figure preparers, and an end-to-end figure-generation integration test. `scripts/generate_release_artifacts.py` exports deterministic descriptor-review artifacts under `output/reports/`; `scripts/generate_figures.py` renders the five manuscript figures under `manuscript/figures/`.
- Re-run the project, pre-render, artifact, and drift gates after descriptor
  changes; measured counts and render receipts belong in generated documents.
- Keep the standalone clone path independent of monorepo-only imports and
  verify it with a fresh-checkout replay before changing the publisher schema.


## Ordered improvement ladder

1. Keep descriptor validation green.
2. Add external repository publication receipts after a real fork publishes.
3. When a real (non-synthetic) dataset is forked in, extend `_MEDIA_TYPES` and row-count verification to the formats that dataset needs, and pin the new fixture checksums in the descriptor.
4. If the shared `infrastructure.documentation.generated_figure_registry` publisher changes its registry envelope, update `src/data_descriptor/registry.py` to stay byte-compatible so standalone clones keep regenerating identical registries.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `DATA-PUBLICATION-1` | Medium | A real fork and owner receipt | publication receipt + standalone replay | project tests and standalone export check | fabricated publication receipt must fail |
| `DATA-MEDIA-1` | Major | Real licensed non-CSV fixture | media checksum/row manifest | descriptor validator with declared media type | unsupported media or wrong checksum must fail |


### `template_eda_notebook`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Project tests and coverage: `uv run pytest projects/templates/template_eda_notebook/tests --cov=projects/templates/template_eda_notebook/src --cov-fail-under=90`
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Code quality: `uv run ruff check projects/templates/template_eda_notebook/src/` and `uv run mypy projects/templates/template_eda_notebook/src/` must both pass clean.
- Notebook binding: `tests/test_notebook.py` checks the walkthrough is valid nbformat, binds to `src.__all__`, and carries no logic in cells.
- Coverage floor: ≥90% on `src/`; live test count and achieved coverage are
  tracked in `docs/_generated/COUNTS.md`, not hardcoded here.


## Ordered improvement ladder

1. Preserve the notebook -> tested src extraction contract (no logic in cells).
2. Add focused tests + a thin script plot for any new figure-data family.
3. Expand the dataset or cleaning strategies only with deterministic fixtures,
   exact-value tests, and documented claim boundaries.
4. Refresh generated docs after any public-surface change.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `EDA-STATISTICS-1` | Minor | Existing deterministic fixture | exact-statistic assertion matrix | `uv run pytest projects/templates/template_eda_notebook/tests -q` | one altered source statistic must fail |
| `EDA-NOTEBOOK-BINDING-1` | Medium | Notebook extraction contract | notebook-to-source binding receipt | notebook binding gate and project coverage | changed notebook cell without source update must fail |


### `template_formal`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- mypy-as-oracle: `uv run mypy --strict projects/templates/template_formal/src` must exit 0; `tests/test_mypy_oracle.py` also runs this as a subprocess and separately asserts non-zero exit + matching error substring on each `tests/mypy_fixtures/*.py` negative-control fixture.
- Project tests and coverage: `uv run pytest projects/templates/template_formal/tests/ --cov=projects/templates/template_formal/src --cov-fail-under=90`.
- Latest full regression run: 279 tests exercised with 95.29% coverage (authoritative gate: `stage_01_test.py --project-only` → 279/279 passed); the sole initial mypy-oracle failure from the new analysis type boundary was fixed and its exact oracle lane re-passed.
- Zero mocks: `grep -rn "MagicMock\|mocker.patch\|unittest.mock" projects/templates/template_formal/tests/` must return nothing.
- Optional formal side-spec: `scripts/check_formal_specs.sh` runs the Lean 4 `lake build` and the TLA+ TLC model check as real subprocesses; both are non-default (require `lake`/`elan` and a Java runtime respectively) and are not part of the core pipeline.
- Manuscript honesty gate: grep for `"dependent type"` and `"linear type"` outside the manuscript's explicit "What mypy --strict proves" scoping section must return zero matches (ISC-44).
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`.


## Ordered improvement ladder

1. Preserve the paired static+dynamic proof contract: every new ADT/session-type/affine-handle claim gets both a `tests/mypy_fixtures/` negative control and a runtime-raise unit test before merge.
2. Keep the formal side-specs (if retained) wired to a real runnable check; cut cleanly (zero `.lean`/`.tla` files) if they ever become unmaintainable rather than let them go stale.
3. Expand the colony/pheromone integration scenario only with deterministic seeds and documented emergent-property assertions (never a scripted/staged result).
4. Refresh generated docs (`docs/_generated/active_projects.md`, `exemplar_roster.md`, `COUNTS.md`) after registration and after any public-surface change.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `FORMAL-ABLATION-1` | Medium | Existing colony experiment fixtures | calibrated ablation matrix | project tests plus deterministic manuscript binding | omitted axis must fail the experiment registry |
| `FORMAL-INVARIANT-1` | Medium | Typed runtime protocol surface | typed-invariant negative-control fixture | strict mypy oracle and runtime test | illegal state fixture must fail mypy/runtime checks |
| `FORMAL-SPEC-1` | Major | Optional Lean/TLA+ tools | real formal-spec receipt | explicit formal script when tools are installed | decorative or skipped spec must not report pass |


### `template_literature_meta_analysis`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

Run from the template repository root:

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/   --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90
uv run python scripts/audit/check_template_drift.py --strict --project templates/template_literature_meta_analysis
uv run python scripts/docgen/exemplar_roster.py --check
```

Live test counts and coverage snapshots belong in `../../../docs/_generated/COUNTS.md`.


## Ordered improvement ladder

1. Preserve offline fixture reproducibility and synthetic-data honesty.
2. Add focused validators for live retrieval manifests and full-text inventories.
3. Expand KG calibration only with fixture-backed negative controls.
4. Refresh generated docs after any public-surface change.


## Promotion Rule

Move an item out of this file only after its source producer, generated artifact, documentation, and focused tests are updated together.


### `template_madlib`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_madlib/manuscript --repo-root .`
- Project tests and coverage: 181 passed, 99.22% coverage (required floor: 90%).
- Generated artifacts come from `scripts/01_generate_madlib_artifacts.py` and `scripts/z_generate_manuscript_variables.py`.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --project templates/template_madlib --strict` — no drift detected.
- Project-local output validator: `scripts/02_validate_outputs.py` → `src.output_validator.validate_generated_outputs`, declared third analysis script; writes `output/reports/output_validation.json`.
- Live test counts and coverage are read from
  [`docs/_generated/COUNTS.md`](../_generated/COUNTS.md), not pinned
  here; keep every `src/` module (config, composition, tokens, analysis,
  artifact_writers, manuscript_variables) branch-covered under the 90% gate.


## Ordered improvement ladder

1. Keep release metadata, module size, tests, and drift gates green as the published canonical exemplar evolves.
2. Add schema migrations only with compatibility tests from the current config.
3. Add negative controls for digest-invariant drift and missing review-packet artifacts as those surfaces change.
4. Promote domain-fork examples only after they add domain validators and explicit non-claim boundaries.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `MADLIB-MIGRATION-1` | Medium | Current config schema | versioned migration fixture | `uv run pytest projects/templates/template_madlib/tests -q` | old schema with dropped field must fail or migrate explicitly |
| `MADLIB-DIGEST-PROPERTY-1` | Minor | Deterministic token digest contract | digest invariant cases | focused token tests | reordered/altered lexicon must change the digest |


### `template_newspaper`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_newspaper/manuscript --repo-root .` — passed; no render-blocking pitfalls or undefined citations.
- Canonical core pipeline: `uv run python scripts/runner/execute_pipeline.py --project templates/template_newspaper --core-only` — use this gate to measure the current infrastructure/project tests, generated figures, manuscript render, output validation, and copy status.
- Focused project gate: `uv run pytest projects/templates/template_newspaper/tests --cov=projects/templates/template_newspaper/src --cov-fail-under=90` — 150 passed, 0 failed, 0 skipped, 99.70% coverage.
- Drift gate: `uv run python scripts/audit/check_template_drift.py --project templates/template_newspaper --strict` — passed.
- Render quality: front page raster inspection found no clipping, overlap, missing figures, unreadable text, broken columns, or excessive blank areas; PDF logs contain 0 `^! ` errors and extracted newspaper text contains 0 `??` tokens.
- Measured artifact: `output/data/render_report.json` reports `page_count: 12`, `all_pages_fit: true`; `pdfinfo` reports 12 pages for `output/pdf/the-triplicate.pdf`.
- Live test count and measured branch coverage → [`docs/_generated/COUNTS.md`](../_generated/COUNTS.md) (regenerated, never hardcoded here).


## Ordered improvement ladder

1. Keep deterministic fictional edition generation and project tests green.
2. Add structured layout audit output and validation.
3. Add copy-and-customize content fixtures for small, medium, and long editions.
4. Promote real-news forks only with source provenance, fact checks, and clear publication approval gates.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `NEWSPAPER-LAYOUT-AUDIT-1` | Medium | ReportLab geometry and raster fixtures | glyph-collision/layout audit JSON | project tests plus rendered audit | overlapped glyph fixture must fail |
| `NEWSPAPER-FIXTURE-LENGTH-1` | Minor | Content schema | small/medium/long deterministic editions | project render and byte/dimension checks | truncated or overset edition must fail |


### `template_pools_rules_tools`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Project tests and coverage (2026-08-02): 259 passed, 2 skipped, 0 failed; 94.88% total coverage, above the 90% floor. Command: `uv run pytest projects/templates/template_pools_rules_tools/tests --cov=projects/templates/template_pools_rules_tools/src --cov-fail-under=90`.
- Pre-render validation (2026-08-02): passed with no render-blocking pitfalls or undefined citations.
- Analysis stage (2026-08-02): 6/6 scripts completed successfully; observed 3 fonds, 2/2 rule sets OK, 4 tools discovered and valid, 8 bibliography entries, 5 contacts, and 5 datasets. The non-IMRaD section-schema messages are advisory by design.
- Render stage (2026-08-02): combined PDF generated successfully from 8 manuscript sections; 9 figures found, including the cover art. Render logs contain 0 lines beginning with `!` and the combined PDF contains 0 `??` tokens; `pdfinfo` reports 21 pages.
- Output validation: all component checks pass (PDF, bookends, Markdown, structure, figure registry, evidence registry, design overlays, and artifact manifest). The rendered-provenance binding remains blocked by the shared validator's `ARTIFACT_MANIFEST_INCOMPLETE` comparison of stable generated files; this exemplar does not modify shared infrastructure, so the issue remains recorded here.
- Output copy stage: passed; 121 files copied to `output/templates/template_pools_rules_tools/` and the combined PDF was copied successfully.
- Repo drift gate (2026-08-02): `uv run python scripts/audit/check_template_drift.py --project templates/template_pools_rules_tools --strict` passed.
- Standalone mirror sync (2026-08-02): `scripts/publish/sync_standalone_mirrors.py --project template_pools_rules_tools --commit` reported SYNCED (+3 ~14 -0); mirror commit `f9bd990` (verified by fresh clone: four-tools manuscript, combined PDF, figures, and figure registry present).
- Type-checking: `uv run mypy projects/templates/template_pools_rules_tools/src --config-file projects/templates/template_pools_rules_tools/pyproject.toml`
- Strong-rule validation gate: `uv run python projects/templates/template_pools_rules_tools/scripts/04_validate_strong_rules.py`
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
- Live test count and measured coverage percentage → [`docs/_generated/COUNTS.md`](../_generated/COUNTS.md) (regenerated, never hardcoded here).


## Ordered improvement ladder

1. Add a fourth fond type (e.g. `template_models`) only after its fond exemplar exists and the shared allowlists/docs owner approves the change.
2. Broaden strong-rule programmatic evaluation as new constraint families are defined, while preserving the read-only resource-pool boundary.
3. Add per-resource schema assertions whenever a pool gains required fields.
4. Refresh generated docs and the SKILL manifest after any public-surface change.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `POOLS-RESOURCE-SCHEMA-1` | Medium | Typed resource loaders | fonds/rules/tools schema receipt | project evaluator and drift gates | missing required resource field must fail |
| `POOLS-EVALUATOR-1` | Minor | Existing strong-rule fixtures | expanded evaluator coverage report | focused no-mock project tests | malformed rule/context must fail |
| `POOLS-FOURTH-FOND-1` | Major | Owner-approved fourth fond exemplar | public fond manifest and registry update | public-scope and standalone gates | absent exemplar must remain blocked, not skipped as pass |


### `template_prose_project`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_prose_project/manuscript --repo-root .` — **pass** (no render-blocking pitfalls or undefined citations).
- Project tests and coverage (live counts in
  [`docs/_generated/COUNTS.md`](../_generated/COUNTS.md), not pinned here):
  `uv run pytest projects/templates/template_prose_project/tests/ --cov=projects/templates/template_prose_project/src --cov-fail-under=90`
  — **134 passed, 99.58% coverage** (measured 2026-08-02 with an isolated
  `--cov-config` datafile; the repo-root coverage config merges concurrent
  agents' `.coverage` data, so re-measure with `COVERAGE_FILE` isolation).
- Prose analysis is offline by default and uses real markdown and BibTeX fixtures.
- Canonical pipeline (analysis → render → validate → copy) for
  `templates/template_prose_project`: **green**; all five configured checks
  pass; combined PDF renders with **0 LaTeX errors, 0 unresolved `??`,
  14 pages**, no unresolved `{{TOKEN}}`.
- Determinism recipe (run twice, diff): `run_prose_pipeline.py` run twice into
  an isolated `--project-root` produces **byte-identical** `manuscript_report.json`,
  `checks.json`, `evidence_summary.json`, `run_summary.json` (verified 2026-08-02).
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --project templates/template_prose_project --strict` — **no drift detected**.
- Style + type gates over public source paths:
  `uv run python -m infrastructure.project.public_scope source-paths` piped to ruff and mypy.


## Ordered improvement ladder

1. Keep offline prose checks green under project coverage.
2. Preserve the versioned evidence-summary schema and add compatibility tests for new fields.
3. Keep editorial profiles named, config-owned, and migration-tested.
4. Add optional LLM review only behind explicit config and offline-safe defaults.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `PROSE-LLM-REVIEW-1` | Medium | Explicit configured provider and transcript | opt-in review receipt | project tests with LLM disabled by default | enabled review without provider must fail closed |
| `PROSE-REPORT-SCHEMA-1` | Minor | Stable evidence-summary schema | versioned report schema | schema and manuscript-binding tests | unknown report field/version must fail |


### `template_autoscientists`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Pre-render validation passed with no render-blocking pitfalls or undefined citations.
- Project test gate: **114 passed, 1 skipped** (`requires_ollama`), **99.29%** isolated source coverage.
- Full core pipeline (8 stages) completed green; single-stage analysis/render/validate/copy all exit 0 with Stage-04 validation passing every check (PDF, transmission bookends, Markdown, output structure, figure registry, evidence registry, project design overlays, artifact manifest, rendered provenance).
- Combined PDF: **14 pages**, **0** `^! ` LaTeX error lines, **0** unresolved `??` markers.
- Qualified template-drift gate: `template_drift: no drift detected.`


## Ordered improvement ladder

1. Keep the deterministic fixture-replay baseline green and coverage-gated (integrity).
2. Keep `manuscript/config.yaml.example` shape-synced with live `SearchConfig` defaults (configurable surface).
3. Promote the live agent path only when offline fixtures + no-network default validation exist (test/validator boundary).


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AS-TRANSCRIPT-1` | Medium | Transcript schema and provenance | stale-transcript audit receipt | project replay tests | changed transcript revision must fail |
| `AS-REPLAY-1` | Minor | Offline fixture runner | no-network replay report | default project gate | network-only replay path must be unavailable by default |


### `template_gold_refinement`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Project tests and coverage (read live counts from
  [`docs/_generated/COUNTS.md`](../_generated/COUNTS.md), not a
  pinned number here):
  `uv run pytest projects/templates/template_gold_refinement/tests/ --cov=projects/templates/template_gold_refinement/src --cov-fail-under=90`
- Stage-02 refinery analysis (figures, token injection, evidence/figure registries):
  `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_gold_refinement`
- Stage-03 manuscript render (ore → nine-nines certification, zero unresolved `{{TOKEN}}` vars):
  `uv run python scripts/pipeline/stage_03_render.py --project templates/template_gold_refinement`
- Confidentiality and drift guards:
  `uv run python scripts/audit/check_tracked_all.py` and
  `uv run python scripts/audit/check_template_drift.py --strict`


## Ordered improvement ladder

1. Keep the refinery pipeline, deterministic token injection, and evidence
   registry green under the 90% project coverage gate.
2. Add transmission bookend manuscript sections.
3. Publish or record references for the planned documented platforms.
4. Expose the reverse assay (target purity → shortest ordered prefix) through config and a generated report.
5. Add config selection for the multi-objective purity vector without introducing an unvalidated aggregate score.
6. Formalize the analogy-break boundary as a theorem with a matching validator.
7. Wire the refinery to `infrastructure.validation` and measure purity on a
   real manuscript.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `GOLD-BOOKEND-1` | Medium | Transmission/page validator | transmission bookend receipt | project render and publication tests | missing first/last page must fail |
| `GOLD-PURITY-1` | Medium | Configured reverse assay and purity vector | typed assay/report manifest | project tests and manuscript binding | altered purity vector must fail |
| `GOLD-ANALOGY-1` | Major | Formal boundary statement | analogy-boundary theorem + validator | formal/infrastructure validation when enabled | analogy crossing without evidence must fail |


### `template_methods_paper`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Project tests and coverage: `uv run pytest projects/templates/template_methods_paper/tests --cov=projects/templates/template_methods_paper/src --cov-fail-under=90`
  — last full run: **90 passed, 0 failed, 99.01% coverage** (2026-08-02).
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --project templates/template_methods_paper --strict`
  — last run: **no drift detected** for this exemplar (2026-08-02). A
  repo-level `repo_docs_hardcoded_test_count` warning currently fires for
  `template_storybook/tests/AGENTS.md` (hardcoded '12 tests' from a prior
  commit); it is outside this exemplar's subtree and is tracked by the
  storybook lane.
- Code quality: `uv run ruff check projects/templates/template_methods_paper/src/` and `uv run mypy projects/templates/template_methods_paper/src/` must both pass clean — last run: **ruff clean, mypy clean (14 source files)** (2026-08-02).
- Prerender: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_methods_paper/manuscript --repo-root .`
  — last run: **no render-blocking pitfalls or undefined citations** (2026-08-02).
- Full pipeline (analysis → variables → render → validate → copy):
  **stage 02 3/3 scripts, stage 03 1/1 PDF (14 pages), stage 04 clean,
  stage 05 clean**; render log `^! ` count **0**, `??` count **0**
  (2026-08-02).
- Determinism: `tests/test_compiler.py::test_compile_method_is_deterministic` recompiles the same `Method` five times and asserts a single `plan_hash`.
- Coverage floor: ≥90% on `src/`; live test count and achieved coverage are tracked in `docs/_generated/COUNTS.md` (not hardcoded here).


## Ordered improvement ladder

1. Preserve the staged-gate-then-deterministic-compile contract (no gate
   reordering, no unhashed nondeterminism reaching `plan_hash`).
2. Add focused tests + a thin script export for any new step kind or
   exporter format.
3. Expand the worked examples or controlled vocabulary only with
   deterministic fixtures, exact-value tests, and documented claim
   boundaries.
4. Refresh generated docs after any public-surface change.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `METHODS-DSL-EXACT-1` | Minor | Existing staged DSL | exact-value test matrix | project test suite | changed numeric literal must fail |
| `METHODS-EXPORTER-1` | Medium | Deterministic compiler/exporter | versioned export receipt | compiler, prerender, and drift gates | malformed export must fail closed |


### `template_redacted_report`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Tests cover classification ceilings, redaction bounds, overlap rejection, orphan decisions, sensitive-marker coverage, release authority, taxonomy adapters, sanitized in-memory packets, source-safe ledgers, segment hash manifests, reviewer approval gates, paragraph audit tables, mosaic-risk scoring, typed fixture loading, malformed/missing input failures, two-run artifact byte equality, source-canary non-disclosure, visual redaction styles, background modes, Kmyth requested/available matrix semantics, and the full 16-variant development matrix.
- Keep Stage 02 generation deterministic and text-free for the public projection,
  with `output/reports/redaction_audit.json` and the hashed
  `output/data/release_ledger.json` produced from source-owned contracts.


## Ordered improvement ladder

1. Keep redaction validator tests green.
2. Bind manuscript tables to the source-safe audit and ledger contracts.
3. Extend policy taxonomy adapters only with invented, cleared fixtures.
4. Keep segment hashes, residual-risk reports, and approval gates typed and fail-closed.
5. Add rendered public report examples only with provenance receipts.
6. Add visual redaction/background regression only when raster tooling is pinned.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `REDACTED-AUDIT-BIND-1` | Medium | Existing source/audit ledger | manuscript-to-audit binding receipt | strict project validation | changed audit value without source update must fail |
| `REDACTED-VISUAL-1` | Major | Stable raster toolchain | pixel regression manifest | explicit visual gate only when tooling is pinned | missing raster tool must report unavailable, not pass |


### `template_registered_report`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Tests cover registration freezing, required sections, duplicate hypotheses, outcome drift, deviation classification, stage/ethics metadata, sensitivity-analysis validation, review packets, exploratory-claim boundaries, and the deterministic demonstration study (seeded data synthesis, permutation test, plan-driven analysis binding, figure-data helpers, and manuscript-prose binding against live analysis values). `scripts/generate_review_artifacts.py` exports deterministic frozen-registration, adherence, deviation-ledger, and review-packet artifacts under `output/reports/`; `scripts/generate_figures.py` renders four committed manuscript figures and writes the executed analysis to `output/data/demo_analysis.json`, to which the manuscript numbers are bound.
- Fresh full-suite run: all tests pass with coverage above the 90% floor; prerender validation reports no render-blocking pitfalls; the combined PDF renders with zero LaTeX errors and zero unresolved `??` references.


## Ordered improvement ladder

1. Keep preregistration tests green.
2. Keep deviation-ledger export and review packets schema-compatible.
3. Keep registration packet outputs reproducible from source and fixtures.
4. Keep the deterministic demonstration study and manuscript figures bound to live analysis values.
5. Add publication receipts for a real exemplar.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `REGISTERED-PUBLICATION-1` | Medium | Real fork and owner receipt | publication payload receipt | project artifact and preflight gates | synthetic DOI/receipt must fail |
| `REGISTERED-MIGRATION-1` | Minor | Frozen registration schema | compatibility fixture | project protocol tests | dropped registration field must fail |


### `template_search_project`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

Run from the template repository root:

```bash
uv run pytest projects/templates/template_search_project/tests/ \
  --cov=projects/templates/template_search_project/src --cov-fail-under=90
uv run python scripts/audit/check_template_drift.py --strict --project templates/template_search_project
uv run python -m infrastructure.validation.cli markdown projects/templates/template_search_project/manuscript/
```

Live test counts and coverage snapshots belong in
[`docs/_generated/COUNTS.md`](../_generated/COUNTS.md), not this
file.

- The default pipeline (`project_config.search.sources: [local]`) is fully offline and
  CI-safe, backed by the bundled `data/corpus.json`.
- LLM synthesis (`llm.enabled`) defaults to `false` so tests and CI never
  require an Ollama server.
- `deep_search` is enabled by default and exercises the multi-keyword
  arXiv/Crossref fan-out. Paperclip is fail-fast (not graceful) when
  `PAPERCLIP_API_KEY` is unset and is deliberately omitted from the default
  `sources` list; add it only alongside a real key.


## Ordered improvement ladder

1. Preserve offline-by-default reproducibility and synthetic-fixture honesty.
2. Add focused validators for any new generated artifact family (search
   cache, fulltext cache, deep-search aggregate).
3. Expand live-backend coverage only with graceful degradation and
   documented claim boundaries.
4. Refresh generated docs after any public-surface change.


## Promotion Rule

Move an item out of this file only after its source producer, generated
artifact, documentation, and focused tests are updated together.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `SEARCH-CACHE-1` | Medium | Offline cache schema | cache identity/age receipt | project tests with network disabled | stale cache must degrade explicitly |
| `SEARCH-FULLTEXT-1` | Medium | Full-text fixture/license boundary | full-text coverage report | focused retrieval validators | missing full text must not count as retrieved |
| `SEARCH-DEEP-1` | Minor | Deep-search query plan | deterministic deep-search manifest | byte-repeat and claim tests | changed query order must change receipt |


### `template_sia`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Manuscript pre-render gate: `uv run python -m infrastructure.validation.cli prerender projects/templates/template_sia/manuscript --repo-root .`
  → clean (no render-blocking pitfalls, no undefined citations), 2026-08-02.
- Project tests and coverage (live counts in
  [`docs/_generated/COUNTS.md`](../_generated/COUNTS.md), not pinned here):
  `uv run pytest projects/templates/template_sia/tests/ --cov=projects/templates/template_sia/src --cov-fail-under=90`
  → 66 passed, 1 deselected (`requires_ollama`), isolated coverage 99.69% (2026-08-02).
- Default loop execution replays recorded fixtures; `--live-sia` is bounded but does not apply code mutations.
- The `requires_ollama` project marker is excluded by default so the local
  coverage gate cannot accidentally import or contact the live LLM bridge.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --strict`
  → `template_drift: no drift detected` for `templates/template_sia` (2026-08-02).
- Canonical stage run (2026-08-02): Stage 02 analysis 2/2 scripts,
  Stage 03 render green, Stage 04 all checks pass (PDF, bookends, markdown,
  structure, figure registry, evidence registry, design overlays, artifact
  manifest, rendered-provenance bind), Stage 05 copy complete.
  Render quality: 0 `^! ` LaTeX errors, 0 `??` in `pdftotext`, combined PDF 9 pages.
- Style + type gates over public source paths:
  `uv run python -m infrastructure.project.public_scope source-paths` piped to ruff and mypy.
- Thin-orchestrator boundary: `src/loop.py` owns project configuration, fixture
  selection, shared-harness invocation, and derived artifacts; the CLI imports
  that API. `tests/test_architecture_contract.py` rejects a return to
  `src → scripts` imports or a second script-layer implementation.


## Ordered improvement ladder

1. Keep fixture replay and artifact-manifest tests green.
2. Add stale-fixture and non-mutation validators.
3. Add typed config for any new live-loop controls.
4. Promote real live improvement only with sandboxing, diff review, rollback, and explicit human approval gates.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `SIA-STALE-FIXTURE-1` | Medium | Recorded loop transcript schema | stale-fixture/non-mutation report | project replay gate | changed fixture revision must fail |
| `SIA-TYPED-LOOP-1` | Minor | Typed `project_config.sia` loader | loop configuration receipt | project tests and config validation | unknown loop key must fail |
| `SIA-APPROVAL-FORK-1` | Major | Sandbox, diff, rollback, human approval | fork guidance and approval receipt | explicit opt-in live lane | mutation without approval must fail |


### `template_storybook`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Project tests and coverage (2026-08-02):
  `uv run pytest projects/templates/template_storybook/tests/ --cov=projects/templates/template_storybook/src --cov-fail-under=90`
  → 21 passed, 0 failed, 0 skipped; coverage 95.68% (pytest) / 94.4% (stage-01
  project-tests run, `scripts/pipeline/stage_01_test.py --project-only --project templates/template_storybook`).
- Pre-render validation:
  `uv run python -m infrastructure.validation.cli prerender projects/templates/template_storybook/manuscript --repo-root .`
  → no render-blocking pitfalls or undefined citations.
- Stage-02 storybook render: 15/15 analysis scripts passed; primary PDF
  `output/pdf/the-shape-between.pdf` (14 pages) + contact sheet + manifest
  regenerated.
- Stage-03 manuscript render: `template_storybook_combined.pdf` (8 pages) plus
  HTML and 6 Beamer slide decks; 0 `^! ` lines in `output/pdf/*.log`, 0 `??`
  in both PDFs.
- Stage-04 validation: all checks passed; rendered provenance receipt written.
- Stage-05 copy: outputs copied to repo `output/templates/template_storybook/`.
- Template drift (2026-08-02):
  `uv run python scripts/audit/check_template_drift.py --project templates/template_storybook --strict`
  → no drift detected.


## Ordered improvement ladder

1. Keep deterministic page rendering and PDF assembly green.
2. Add trim-size variants.
3. Keep contact-sheet generation and page-level accessibility metadata aligned
   with content changes.
4. Keep the raster contrast audit aligned with any new overlay modes.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `STORYBOOK-TRIM-1` | Medium | Configurable page geometry | trim-size manifest | project render and raster checks | unsupported trim size must fail |
| `STORYBOOK-CAPTION-1` | Minor | Caption-zone schema | per-page caption placement receipt | deterministic image/PDF QA | caption overflow must fail |
| `STORYBOOK-ACCESSIBILITY-1` | Medium | Page metadata producer | accessibility metadata report | project accessibility gate | missing alt/title metadata must fail |


### `template_template`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Manuscript pre-render gate:
  `uv run python -m infrastructure.validation.cli prerender projects/templates/template_template/manuscript --repo-root .`
  → no render-blocking pitfalls or undefined citations (2026-08-02).
- Project tests and coverage:
  `uv run pytest projects/templates/template_template/tests/ --cov=projects/templates/template_template/src --cov-fail-under=90`
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --project template_template --strict`
- Live test counts and coverage snapshots belong in
  `../../../docs/_generated/COUNTS.md`, not hardcoded here.


## Ordered improvement ladder

1. Keep confidentiality and metrics tests green under coverage.
2. Add stale-metric detection for any new generated field.
3. Expand architecture visualization only with deterministic inputs and
   documented omissions.
4. Refresh generated docs after public-roster or metric-surface changes.
5. Keep the appendix matrix and figure data in lockstep (the 08f table and
   `figure_comparative_matrix.py` share the 14×10 shape; verify the container
   row's `~` stays aligned with the data module's 0.5 value).
6. Re-verify chapter 07 steganography prose whenever `infrastructure/steganography`
   defaults change (`overlay_opacity`, `overlay_text`, hash algorithms,
   barcode placement).


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `META-SCHEMA-1` | Medium | Generated metric schema | schema-versioned metrics receipt | meta-template tests | stale metric key must fail |
| `META-MATRIX-1` | Minor | Public roster generator | matrix lockstep report | generated-doc and roster gates | roster drift must fail |
| `META-STEG-1` | Minor | Steganography config producer | deterministic metadata revalidation | metadata/visual tests | changed default must invalidate stale evidence |


### `template_textbook`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Manuscript pre-render gate:
  `uv run python -m infrastructure.validation.cli prerender projects/templates/template_textbook/manuscript --repo-root .`
  → **clean** (no render-blocking pitfalls, no undefined citations).
- Project tests and coverage:
  `uv run pytest projects/templates/template_textbook/tests/ --cov=projects/templates/template_textbook/src --cov-fail-under=90`
  → **192 passed, coverage 96.19%** (last measured run; ≥90% floor met).
- Canonical pipeline stages (2026-08-02 pass):
  - `stage_02_analysis.py` → 3/3 scripts, exit 0 (figures, diagrams, worked-model summary).
  - `stage_03_render.py` → `template_textbook_combined.pdf`, 98 pages,
    0 LaTeX errors (`^! ` in logs), **0 unresolved `??`** in extracted text.
  - `stage_04_validate.py` → clean; `stage_05_copy.py` → outputs copied.
- Repo drift gate: `uv run python scripts/audit/check_template_drift.py --project templates/template_textbook --strict`
  → **no drift detected**.
- Structural integrity is driven by `manuscript/config.yaml`, chapter stubs,
  figure generation, and the unified audit gate
  (`textbook.audit.run_manuscript_audit`): default mode validates the fillable
  scaffold, while `--require-complete` fails on nonzero per-section stub
  counts and reports the total.
- Live test counts and coverage snapshots belong in
  `../../../docs/_generated/COUNTS.md`, not hardcoded here.


## Ordered improvement ladder

1. Keep scaffold, figure, diagram, and manuscript-integrity tests green.
2. Add structured scaffold audit output and stale-file detection.
3. Add copy-and-customize examples for short course notes and full textbook
   shapes.
4. Promote a filled textbook fork only after
   `audit_textbook_quality.py --require-complete` reports zero stubs.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `TEXTBOOK-CONFIG-MIGRATION-1` | Minor | Live/example config shape | compatibility key-set receipt | textbook config tests | orphaned or dropped config key must fail |
| `TEXTBOOK-STALE-DIAGRAM-1` | Medium | Diagram inventory | stale/orphan diagram report | audit and render gates | unreferenced diagram must fail |
| `TEXTBOOK-FACT-REGISTRY-1` | Medium | Worked-example source data | numeric-fact registry | manuscript evidence gate | changed numeric fact without registry update must fail |


### `template_pitch_deck`

The following pre-normalization sections were archived on 2026-08-09:

## Current validation evidence

- Prerender passed with no render-blocking pitfalls or undefined citations.
- Project tests: `uv run python -m pytest projects/templates/template_pitch_deck/tests --cov=projects/templates/template_pitch_deck/src --cov-fail-under=90 -q` — 125 passed, 98.43% coverage.
- Analysis: `stage_02_analysis.py --project templates/template_pitch_deck` — 5/5 scripts passed; token/cliché audit clean (40/102/170 text fields), diagrams/charts regenerated, diligence coverage 5/5, 9/9, 11/11. Its isolated project environment lacks optional `python-pptx`, so the six artifacts were regenerated from the repo environment with `20_render_decks.py`.
- Manuscript render, output validation, and output copy stages all passed; 44 files copied to `output/templates/template_pitch_deck/`.
- Render quality: six pitch-deck artifacts present; PDF pages 11/37/56, combined manuscript PDF 8 pages; PDF logs contain 0 `^! ` lines; extracted PDFs contain 0 `??` markers.
- Drift passed: `check_template_drift.py --project templates/template_pitch_deck --strict`.
- Relative-link audit: 36 Markdown files / 20 relative links, all resolve.


## Ordered improvement ladder

1. Add the second pitch-subject deck (a broader meta-science-group pitch) to prove the schema generalizes beyond `template_template`.
2. Add a `docs/architecture.md` walkthrough of the theme/slide-kind/diligence system.
3. Add hypothesis-based property tests for budget filtering and token resolution.


## Active backlog index

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `DECK-SECOND-SUBJECT-1` | Medium | Generalized content schema | second deterministic deck | project render and slide QA | subject-specific hard-code must fail schema coverage |
| `DECK-AUDIT-1` | Medium | Transactional slide audit | all-length audit receipt | project tests and PPTX/image QA | partial audit state must fail |
| `DECK-QR-1` | Minor | Publication-aware sequencing | QR/link manifest | slide content and publication checks | QR emitted before publication target exists must fail |

## Archived 2026-08-09 future-only backlog migration

### `template_active_inference`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MEDIUM-TEST-PERF-1` | open | Medium | Test ergonomics; isolated project refresh | Implement the scoped change; run focused gate tests plus `--durations=20` comparison and attach cheaper source/row-contract negative controls plus one end-to-end artifact-refresh test. | cheaper source/row-contract negative controls plus one end-to-end artifact-refresh test | focused gate tests plus `--durations=20` comparison | Source-only mutation passes without exercising the matching contract |
| `MEDIUM-SUBPROCESS-POLICY-1` | open | Medium | Test ergonomics; release wrappers | Implement the scoped change; run policy audit and a focused mutation of one wrapper policy field and attach future subprocess-wrapper policy audit generated from source-owned declarations. | future subprocess-wrapper policy audit generated from source-owned declarations | `uv run pytest tests -q --no-cov --timeout=120` | Wrapper without timeout, cwd, check, or useful failure text passes the policy audit |


### `template_advanced_literature_review`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ARL-PHASE-VALIDATION-1` | open | Minor | Phase configuration schema | Implement the scoped change; run phase configuration tests and replay gate and attach phase-boundary validation receipt. | phase-boundary validation receipt | `uv run pytest tests -q --no-cov --timeout=120` | invalid temporal bounds must fail before replay |
| `ARL-LLM-FILTER-1` | open | Medium | Calibration corpus and opt-in provider | Implement the scoped change; run LLM filter tests with known positive/negative examples and attach calibration fixture bundle. | calibration fixture bundle | `uv run pytest tests -q --no-cov --timeout=120` | unavailable provider must report skip, not pass |


### `template_autoresearch_project`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AR-REVIEW-BOUNDARY-1` | open | Minor | Human approval boundary | Implement the scoped change; run project review-artifact tests and attach self-approval regression receipt. | self-approval regression receipt | `uv run pytest tests -q --no-cov --timeout=120` | generated approval without `human_review.yaml` must fail |
| `AR-MODULE-WATCH-1` | open | Minor | Module-size drift gate | Implement the scoped change; run strict drift gate and attach module-size report. | module-size report | `uv run pytest tests -q --no-cov --timeout=120` | oversized logic hub must fail the gate |
| `AR-REVIEW-PACKET-V2` | open | Medium | Review-packet schema v1 | Implement the scoped change; run packet compatibility tests and attach migration and v2 receipt. | migration and v2 receipt | `uv run pytest tests -q --no-cov --timeout=120` | v2 self-approval or unknown version must fail |
| `AR-METHOD-ADAPTER-1` | open | Major | Stable loop/report schemas | Implement the scoped change; run project suite and evidence validation and attach second deterministic adapter receipt. | second deterministic adapter receipt | `uv run pytest tests -q --no-cov --timeout=120` | network or generated-code adapter must be unavailable |


### `template_autopoiesis`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AUTOPOIESIS-MUTATION-1` | open | Medium | Existing mutation meta-gate | Implement the scoped change; run `uv run pytest projects/templates/template_autopoiesis/tests -q` and attach per-domain mutation report. | per-domain mutation report | `uv run pytest tests -q --no-cov --timeout=120` | removing a domain guard must fail the mutated case |
| `AUTOPOIESIS-ARCHETYPE-1` | open | Medium | Config schema extension | Implement the scoped change; run project validator plus generated-child integrity tests and attach filtered child manifest. | filtered child manifest | `uv run pytest tests -q --no-cov --timeout=120` | unknown archetype filter must fail closed |


### `template_code_project`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `CODE-OPTIMIZER-NEG-1` | open | Minor | Deterministic objective fixtures | Implement the scoped change; run `uv run pytest tests/regression/projects/template_code_project -q --no-cov` and attach optimizer claim negative-control test. | optimizer claim negative-control test | `uv run pytest tests/regression/projects/template_code_project -q --no-cov` | changing the objective must fail the pinned claim |
| `CODE-DASHBOARD-SCHEMA-1` | open | Medium | Dashboard producer schema | Implement the scoped change; run project test gate and artifact validator and attach dashboard schema receipt. | dashboard schema receipt | `uv run pytest tests -q --no-cov --timeout=120` | missing chart field must fail schema validation |
| `CODE-SUBPROCESS-1` | open | Medium | Shared subprocess policy | Implement the scoped change; run `uv run python scripts/audit/check_claim_bindings.py` plus project gate and attach wrapper inventory row. | wrapper inventory row | `uv run python scripts/audit/check_claim_bindings.py` plus project gate | missing timeout/cwd policy must fail the inventory |


### `template_eda_notebook`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `EDA-STATISTICS-1` | open | Minor | Existing deterministic fixture | Implement the scoped change; run `uv run pytest projects/templates/template_eda_notebook/tests -q` and attach exact-statistic assertion matrix. | exact-statistic assertion matrix | `uv run pytest tests -q --no-cov --timeout=120` | one altered source statistic must fail |
| `EDA-NOTEBOOK-BINDING-1` | open | Medium | Notebook extraction contract | Implement the scoped change; run notebook binding gate and project coverage and attach notebook-to-source binding receipt. | notebook-to-source binding receipt | `uv run pytest tests -q --no-cov --timeout=120` | changed notebook cell without source update must fail |


### `template_formal`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `FORMAL-ABLATION-1` | open | Medium | Existing colony experiment fixtures | Implement the scoped change; run project tests plus deterministic manuscript binding and attach calibrated ablation matrix. | calibrated ablation matrix | `uv run pytest tests -q --no-cov --timeout=120` | omitted axis must fail the experiment registry |
| `FORMAL-INVARIANT-1` | open | Medium | Typed runtime protocol surface | Implement the scoped change; run strict mypy oracle and runtime test and attach typed-invariant negative-control fixture. | typed-invariant negative-control fixture | strict mypy oracle and runtime test | illegal state fixture must fail mypy/runtime checks |


### `template_literature_meta_analysis`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `LIT-KG-CALIBRATION-1` | open | Medium | Knowledge-graph extraction schema | Implement the scoped change; run KG parser/scorer tests preserve score direction and attach calibration fixture bundle. | calibration fixture bundle | `uv run pytest tests -q --no-cov --timeout=120` | inverted score direction must fail |


### `template_madlib`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MADLIB-DIGEST-PROPERTY-1` | open | Minor | Deterministic token digest contract | Implement the scoped change; run focused token tests and attach digest invariant cases. | digest invariant cases | `uv run pytest tests -q --no-cov --timeout=120` | reordered/altered lexicon must change the digest |
| `MADLIB-MIGRATION-1` | open | Medium | Current config schema | Implement the scoped change; run `uv run pytest projects/templates/template_madlib/tests -q` and attach versioned migration fixture. | versioned migration fixture | `uv run pytest tests -q --no-cov --timeout=120` | old schema with dropped field must fail or migrate explicitly |


### `template_newspaper`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `NEWSPAPER-FIXTURE-LENGTH-1` | open | Minor | Content schema | Implement the scoped change; run project render and byte/dimension checks and attach small/medium/long deterministic editions. | small/medium/long deterministic editions | `uv run pytest tests -q --no-cov --timeout=120` | truncated or overset edition must fail |
| `NEWSPAPER-LAYOUT-AUDIT-1` | open | Medium | ReportLab geometry and raster fixtures | Implement the scoped change; run project tests plus rendered audit and attach glyph-collision/layout audit JSON. | glyph-collision/layout audit JSON | `uv run pytest tests -q --no-cov --timeout=120` | overlapped glyph fixture must fail |


### `template_pools_rules_tools`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `POOLS-EVALUATOR-1` | open | Minor | Existing strong-rule fixtures | Implement the scoped change; run focused no-mock project tests and attach expanded evaluator coverage report. | expanded evaluator coverage report | `uv run pytest tests -q --no-cov --timeout=120` | malformed rule/context must fail |
| `POOLS-RESOURCE-SCHEMA-1` | open | Medium | Typed resource loaders | Implement the scoped change; run project evaluator and drift gates and attach fonds/rules/tools schema receipt. | fonds/rules/tools schema receipt | `uv run pytest tests -q --no-cov --timeout=120` | missing required resource field must fail |


### `template_prose_project`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `PROSE-REPORT-SCHEMA-1` | open | Minor | Stable evidence-summary schema | Implement the scoped change; run schema and manuscript-binding tests and attach versioned report schema. | versioned report schema | `uv run pytest tests -q --no-cov --timeout=120` | unknown report field/version must fail |


### `template_autoscientists`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AS-REPLAY-1` | open | Minor | Offline fixture runner | Implement the scoped change; run default project gate and attach no-network replay report. | no-network replay report | `uv run pytest tests -q --no-cov --timeout=120` | network-only replay path must be unavailable by default |
| `AS-TRANSCRIPT-1` | open | Medium | Transcript schema and provenance | Implement the scoped change; run project replay tests and attach stale-transcript audit receipt. | stale-transcript audit receipt | `uv run pytest tests -q --no-cov --timeout=120` | changed transcript revision must fail |


### `template_gold_refinement`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GOLD-BOOKEND-1` | open | Medium | Transmission/page validator | Implement the scoped change; run project render and publication tests and attach transmission bookend receipt. | transmission bookend receipt | `uv run pytest tests -q --no-cov --timeout=120` | missing first/last page must fail |
| `GOLD-PURITY-1` | open | Medium | Configured reverse assay and purity vector | Implement the scoped change; run project tests and manuscript binding and attach typed assay/report manifest. | typed assay/report manifest | `uv run pytest tests -q --no-cov --timeout=120` | altered purity vector must fail |
| `GOLD-ANALOGY-1` | open | Major | Formal boundary statement | Implement the scoped change; run formal/infrastructure validation when enabled and attach analogy-boundary theorem + validator. | analogy-boundary theorem + validator | `uv run pytest tests -q --no-cov --timeout=120` | analogy crossing without evidence must fail |


### `template_methods_paper`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `METHODS-DSL-EXACT-1` | open | Minor | Existing staged DSL | Implement the scoped change; run project test suite and attach exact-value test matrix. | exact-value test matrix | `uv run pytest tests -q --no-cov --timeout=120` | changed numeric literal must fail |
| `METHODS-EXPORTER-1` | open | Medium | Deterministic compiler/exporter | Implement the scoped change; run compiler, prerender, and drift gates and attach versioned export receipt. | versioned export receipt | `uv run pytest tests -q --no-cov --timeout=120` | malformed export must fail closed |


### `template_redacted_report`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `REDACTED-AUDIT-BIND-1` | open | Medium | Existing source/audit ledger | Implement the scoped change; run strict project validation and attach manuscript-to-audit binding receipt. | manuscript-to-audit binding receipt | `uv run pytest tests -q --no-cov --timeout=120` | changed audit value without source update must fail |


### `template_registered_report`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `REGISTERED-MIGRATION-1` | open | Minor | Frozen registration schema | Implement the scoped change; run project protocol tests and attach compatibility fixture. | compatibility fixture | `uv run pytest tests -q --no-cov --timeout=120` | dropped registration field must fail |


### `template_search_project`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `SEARCH-DEEP-1` | open | Minor | Deep-search query plan | Implement the scoped change; run byte-repeat and claim tests and attach deterministic deep-search manifest. | deterministic deep-search manifest | `uv run pytest tests -q --no-cov --timeout=120` | changed query order must change receipt |
| `SEARCH-CACHE-1` | open | Medium | Offline cache schema | Implement the scoped change; run project tests with network disabled and attach cache identity/age receipt. | cache identity/age receipt | `uv run pytest tests -q --no-cov --timeout=120` | stale cache must degrade explicitly |
| `SEARCH-FULLTEXT-1` | open | Medium | Full-text fixture/license boundary | Implement the scoped change; run focused retrieval validators and attach full-text coverage report. | full-text coverage report | `uv run pytest tests -q --no-cov --timeout=120` | missing full text must not count as retrieved |


### `template_sia`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `SIA-TYPED-LOOP-1` | open | Minor | Typed `project_config.sia` loader | Implement the scoped change; run project tests and config validation and attach loop configuration receipt. | loop configuration receipt | `uv run pytest tests -q --no-cov --timeout=120` | unknown loop key must fail |
| `SIA-STALE-FIXTURE-1` | open | Medium | Recorded loop transcript schema | Implement the scoped change; run project replay gate and attach stale-fixture/non-mutation report. | stale-fixture/non-mutation report | `uv run pytest tests -q --no-cov --timeout=120` | changed fixture revision must fail |


### `template_storybook`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `STORYBOOK-CAPTION-1` | open | Minor | Caption-zone schema | Implement the scoped change; run deterministic image/PDF QA and attach per-page caption placement receipt. | per-page caption placement receipt | `uv run pytest tests -q --no-cov --timeout=120` | caption overflow must fail |
| `STORYBOOK-TRIM-1` | open | Medium | Configurable page geometry | Implement the scoped change; run project render and raster checks and attach trim-size manifest. | trim-size manifest | `uv run pytest tests -q --no-cov --timeout=120` | unsupported trim size must fail |
| `STORYBOOK-ACCESSIBILITY-1` | open | Medium | Page metadata producer | Implement the scoped change; run project accessibility gate and attach accessibility metadata report. | accessibility metadata report | `uv run pytest tests -q --no-cov --timeout=120` | missing alt/title metadata must fail |


### `template_template`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `META-MATRIX-1` | open | Minor | Public roster generator | Implement the scoped change; run generated-doc and roster gates and attach matrix lockstep report. | matrix lockstep report | `uv run pytest tests -q --no-cov --timeout=120` | roster drift must fail |
| `META-STEG-1` | open | Minor | Steganography config producer | Implement the scoped change; run metadata/visual tests and attach deterministic metadata revalidation. | deterministic metadata revalidation | `uv run pytest tests -q --no-cov --timeout=120` | changed default must invalidate stale evidence |
| `META-SCHEMA-1` | open | Medium | Generated metric schema | Implement the scoped change; run meta-template tests and attach schema-versioned metrics receipt. | schema-versioned metrics receipt | `uv run pytest tests -q --no-cov --timeout=120` | stale metric key must fail |


### `template_textbook`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TEXTBOOK-CONFIG-MIGRATION-1` | open | Minor | Live/example config shape | Implement the scoped change; run textbook config tests and attach compatibility key-set receipt. | compatibility key-set receipt | `uv run pytest tests -q --no-cov --timeout=120` | orphaned or dropped config key must fail |
| `TEXTBOOK-STALE-DIAGRAM-1` | open | Medium | Diagram inventory | Implement the scoped change; run audit and render gates and attach stale/orphan diagram report. | stale/orphan diagram report | `uv run pytest tests -q --no-cov --timeout=120` | unreferenced diagram must fail |
| `TEXTBOOK-FACT-REGISTRY-1` | open | Medium | Worked-example source data | Implement the scoped change; run manuscript evidence gate and attach numeric-fact registry. | numeric-fact registry | `uv run pytest tests -q --no-cov --timeout=120` | changed numeric fact without registry update must fail |


### `template_pitch_deck`

The following pre-normalization sections were archived on 2026-08-09:

## Closed active rows 2026-08-09

The following rows were removed after the same-revision acceptance and negative-control pass.
Closure evidence: release matrix template-public-matrix/v3; command stage_01_test.py --project-only --all-projects --public-projects --profile release --project-workers serial; receipt_digest=e8317bb5fa42be6588de2f8e378996fdd0fc61449fc731dbf8938152f2141b43; 24/24 lanes passed, 5960 tests collected, combined coverage 94.7101%, 2026-08-09

| ID | Status | Size | Dependency | Next action / unblock condition | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `DECK-QR-1` | open | Minor | Publication-aware sequencing | Implement the scoped change; run slide content and publication checks and attach QR/link manifest. | QR/link manifest | `uv run pytest tests -q --no-cov --timeout=120` | QR emitted before publication target exists must fail |
| `DECK-SECOND-SUBJECT-1` | open | Medium | Generalized content schema | Implement the scoped change; run project render and slide QA and attach second deterministic deck. | second deterministic deck | `uv run pytest tests -q --no-cov --timeout=120` | subject-specific hard-code must fail schema coverage |
| `DECK-AUDIT-1` | open | Medium | Transactional slide audit | Implement the scoped change; run project tests and PPTX/image QA and attach all-length audit receipt. | all-length audit receipt | `uv run pytest tests -q --no-cov --timeout=120` | partial audit state must fail |

## Post-refactor revalidation 2026-08-09

The archived closures above were revalidated after the Madlib configuration
model and Redacted Report Kmyth-support module split. The same isolated
release-profile command passed all 24 public lanes, collected 5,960 tests, and
reported 94.7101% combined coverage. Receipt SHA-256:
`fd00581decf60b62bf98a36777bd66931273d50a20383078a27045c23909f9a2`.

## Final committed-tree revalidation 2026-08-09

The committed tree was revalidated after the documentation inventory and
root-only coverage-cleanup fixes. The two-worker isolated release profile
passed all 24 public lanes with no inner xdist, collected 5,960 tests, and
reported 94.7116% combined coverage with output-isolation digests. Receipt
SHA-256:
`984b4c33b9c2592d4e3895e627cc402ffb73ef0ca5d54936d062708a973ed1e7`.

## Root backlog closures 2026-08-09

These root rows were removed from `TO-DO.md` after the final committed-tree
acceptance pass. The remaining root rows are intentionally future work or
external/tool blockers; no closure below implies that live publication,
administrator authority, or private-sidecar promotion occurred.

| ID | Former status | Evidence | Acceptance and negative control |
| --- | --- | --- | --- |
| `STATUS-REFRESH-MED-1` | partial | `docs/_generated/status_evidence.json`; stable status IDs with typed command, scope, owner, date, mode, receipt, and health fields | `status_evidence.py --check` and `status_freshness.py --as-of 2026-08-09` passed; fixtures for missing receipts, stale/future dates, and mismatched health fail |
| `PUBLIC-PUBLISH-MANIFEST-MED-1` | partial | `template-publication-payload/v1` immutable manifest and provider handoff in `infrastructure/publishing/preflight.py` and archival orchestration | Documentation/publishing suites passed; local-only roots, symlink escapes, duplicate paths, credential-shaped metadata, changed payloads, and invalid targets are rejected before provider I/O |
| `TEST-DISCOVERY-PERF-MED-1` | partial | [`test-performance-evidence.json`](test-performance-evidence.json), schema `template-test-performance-v1`, benchmarked commit `db7b3b061`, 204 matched tests per lane | `scripts/maintenance/benchmark_tests.py --target pipeline-smoke --profile quick --parallel-workers 2 --minimum-improvement 30` passed at 34.24% improvement; dirty/staged/untracked source changes invalidate the evidence and serial diagnostics remain available |
| `MODULARITY-MED-1` | open | Madlib `config_models.py` and Redacted Report `kmyth_support.py` splits preserve import façades; root health and the public matrix remain green | `module_line_count_check.py` passed; focused import/behavior tests and the no-mocks inventory passed; oversized modules and removed re-exports remain negative controls |
| `COVERAGE-SNAPSHOT-MED-1` | partial | `docs/_generated/coverage_snapshot.json` schema 3, source-tree identity, and all 24 regenerated public rows; source revision `25169a501` | `counts.py --check` and the 24-lane release profile passed; newly tracked/untracked source or test files and legacy provenance schema are rejected |
| `REGRESSION-SIGNPOST-MIN-1` | partial | `tests/regression/README.md`, `docs/maintenance/regression-testing.md`, and the full-roster claim manifest | `uv run pytest tests/regression/ -q --no-cov --timeout=120` passed with 55 tests; empty collection, stale roster, missing claim path, and undocumented state fail |
| `BUNDLE-ENTRYPOINT-MIN-1` | partial | Discoverable bundle/archive commands in runner help, orchestration menu, and `docs/RUN_GUIDE.md`; rehearsal CLI is dry-run by default | `bundle_executable.py --help`, `archive_publication.py --help`, and `release_rehearsal.py --help` passed; missing projects/bundles fail and default core execution does not build or publish |

The committed benchmark snapshot intentionally omits subprocess output tails;
the raw local receipt was hashed separately during review, while the committed
summary retains the comparable timings, selection, revision, and acceptance
decision without machine-local paths.

## Fresh-checkout rehearsal 2026-08-09

The committed revision `d676d67a0e419b5d553765821eaadd5fb8a0d895` was rehearsed twice in independent local
Darwin checkouts. Both runs passed offline dependency setup, root health,
generated-document and status checks, claims, backlog, strict public contract,
the complete 24-project serial release matrix, and the representative
`template_code_project` render. Both final clean-status checks blocked because
the render changed tracked canonical output files; this is retained as an
active release blocker rather than treated as a green rehearsal. The redacted
summary is [`clean-checkout-evidence.json`](clean-checkout-evidence.json), and
the raw local receipt digest is
`e3ed676727af37a7929193534562253901f9db1d16daf11147f69397dd0b9f70`.
Hosted Linux, optional bundle verification, and owner/administrator receipts
were not available in this run.

## Final HEAD public-matrix revalidation 2026-08-09

After the fresh-checkout evidence was recorded, the final committed tree at
`0f749358073eabd3b3dec59db50b6d0e058c0d75` was rerun through the two-worker
isolated release profile. All 24 public lanes passed, with 5,960 collected
tests, 94.711585% combined coverage, no skips or timeouts, no inner xdist, and
all output-isolation checks passing. The receipt SHA-256 is
`21fd8bddeaa4429786778e522b3e2fa764eb0d42f96757fd2c9a6afff945b9b9`.

The same final tree passed the infrastructure coverage-bearing release gate:
9,843 tests passed, 9 were skipped, 73 were deselected, and infrastructure
coverage was 84.28% against the 60% floor. The optional service lane and the
multi-manuscript-config advisory remained explicit warnings; neither was
promoted to success.
