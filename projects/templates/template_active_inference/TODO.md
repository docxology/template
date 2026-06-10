# template_active_inference TODO

This backlog is future-only. It is not the current artifact contract and does
not create publication claims. Current claims remain deterministic,
locally reproducible, public, and toy-only. Completed work belongs in generated
artifacts, README/AGENTS files, tests, manuscript fragments, and sheaf
registries rather than in this file.

## Current verification evidence

In this 2026-06-09 audit, `uv run pytest tests/ --cov=src --cov-fail-under=90` passed 371 tests with 90.83% coverage. Replace this paragraph only after rerunning that exact command and updating the result from the fresh output.

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

## Sizing rubric

| Size | Scope |
| --- | --- |
| Minor | Local cleanup, documentation signpost, narrow validator/test ergonomics, and no schema or artifact contract change |
| Medium | One-track or cross-track verifier improvement with additive artifact fields, negative controls, and regenerated docs |
| Major | Blocked scope or release-level changes only; no unblocked major rows are planned in this pass |

The track lanes used below are planning labels only. Their source-of-truth files
remain `tracks.yaml`, `manuscript/sheaf/tracks.yaml`,
`manuscript/sheaf/manifest.yaml`, `figures.yaml`, generated reports, and the
validator code.

## Minor upcoming

These rows are scoped maintenance work. They do not introduce live scientific
claims, new track IDs, artifact filenames, schema migrations, or figure IDs.

| ID | Size | Track lane | Future improvement | Proving artifact | Gate/predicate | Negative control |
| --- | --- | --- | --- | --- | --- | --- |
| `MINOR-DOC-SCOPE-1` | Minor | Scope/documentation | Add a compact TODO lane glossary mapping analytical, pymdp, formal, semantic, visualization, release, and scope lanes to their source-of-truth files | `TODO.md` | documentation contract accepts the glossary without stale command or evidence wording | Glossary link or command typo fails documentation contract |
| `MINOR-TEST-SPEED-1` | Minor | Test ergonomics | Document the slowest full-suite tests and identify which are required end-to-end gates versus fixture-level characterization candidates | `TODO.md` or `tests/README.md` | documentation contract plus focused test docs review | Slow-test note cites a stale count or omits the required full-suite gate |
| `MINOR-METHOD-DOCS-1` | Minor | Methods/documentation | Reduce method-inventory fallback debt for public helpers touched by recent verifier/cache work | `docs/reference/method-inventory.md` | `uv run python scripts/generate_method_inventory.py --check` | Public helper touched by verifier/cache work still has fallback inventory text |
| `MINOR-VIZ-AUDIT-1` | Minor | Visualization | Add a reader-facing note that visualization quality is checked through render metrics, source maps, hashes, and section bindings | `README.md`, `docs/README.md`, or visualization docs | documentation contract and visualization audit wording agree | Visualization note omits source-map, hash, render metric, or section-binding checks |

## Medium upcoming

These rows are real future verifier or cross-track improvements. Each one needs
additive artifacts or rows, a failing negative control, regenerated docs, and
green gates before it can be moved out of this file.

| ID | Size | Track lane | Future improvement | Proving artifact | Gate/predicate | Negative control |
| --- | --- | --- | --- | --- | --- | --- |
| `MEDIUM-TRACK-MATRIX-1` | Medium | Cross-track/release | Add a track-lane matrix mapping every `tracks.yaml` pipeline track to its sheaf fragment, producer, primary artifact, validation gate, and manuscript consumer | `output/data/track_lane_matrix.json` | `set_equals` between matrix track IDs, `tracks.yaml`, and sheaf manifest consumers | Pipeline track lacks a sheaf fragment, producer, artifact, gate, or consumer and still passes |
| `MEDIUM-TEST-PERF-1` | Medium | Test ergonomics | Split slow manuscript-gate mutation tests into cheaper source-only negative controls plus one end-to-end refresh characterization | parametrized source-contract tests and one end-to-end artifact-refresh test | focused gate tests preserve failures while `--durations=20` shows reduced redundant regeneration | Source-only mutation passes without exercising the matching contract |
| `MEDIUM-PROVENANCE-UNIFY-1` | Medium | Provenance/validation spine | Remove remaining producer-order sensitivity between validation-spine and sheaf-track artifacts by making shared artifact contracts explicit | `output/data/artifact_contract_index.json` | validation-spine and sheaf validators agree on shared keys, hashes, and freshness fields | Reordered producer leaves stale shared provenance accepted |
| `MEDIUM-SEMANTIC-LANES-1` | Medium | Semantic/sheaf | Group semantic certificate restrictions by track lane and report per-lane summary booleans without changing current restriction keys | `output/data/sheaf_gluing_certificate.json` | `all` lane summaries rederive from existing restriction rows | Mutated restriction row leaves its lane summary true |
| `MEDIUM-VIZ-LANES-1` | Medium | Visualization/claims | Add per-figure lane coverage so figures state whether they support analytical, pymdp, formal, semantic, or release claims | `output/data/figure_source_map.json` or `output/reports/visualization_quality_audit.json` | `set_equals` figure IDs against `figures.yaml` and `all` figures have at least one valid lane | Figure has source data but no lane coverage and still passes |
| `MEDIUM-SCOPE-AUDIT-1` | Medium | Scope/claim ledger | Extend scope-boundary rows to distinguish current toy claims, future-only claims, blocked empirical claims, and blocked network/private/LLM claims | `output/reports/scope_boundary_audit.json` | `all` current-result rows remain toy-only and blocked contexts stay non-live | Empirical or LLM evidence wording appears outside blocked/future context and passes |

## Blocked major scope

These areas remain out of scope until a later plan supplies provenance,
licensing/privacy review, typed claim evidence, semantic restrictions, gates,
and negative controls. They are not ready for `AI-*` promotion IDs. Blocked rows
are not promotion-ready and should not receive Minor or Medium sizes until their
unblock artifact exists.

| Blocked area | Why blocked | Required unblock artifact | Required gate/predicate | Negative control |
| --- | --- | --- | --- | --- |
| Empirical adapter | Current artifacts are deterministic toy models, not biological or real-world data | `output/data/empirical_adapter_manifest.json` | scope-boundary and claim-ledger gates | Empirical result prose without manifest fails |
| Private or restricted data | This exemplar is public and self-contained | `output/reports/data_provenance_audit.json` | provenance and license validator | Private path or unlicensed source passes |
| Network-dependent research | Pipeline must remain locally reproducible | `output/reports/offline_reproducibility_audit.json` | offline pipeline gate | Network call required for core pipeline |
| LLM-generated evidence | Claims must come from generated local artifacts, not opaque model output | `output/reports/evidence_source_audit.json` | evidence registry and claim-ledger gates | LLM-only claim passes evidence audit |
| Non-toy model claims | Current validation covers finite pedagogical examples only | `output/reports/model_scope_audit.json` | scope-boundary validator | Non-toy generalization appears in results |
