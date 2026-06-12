# template_active_inference TODO

This backlog is future-only. It is not the current artifact contract and does
not create publication claims. Current claims remain deterministic,
locally reproducible, public, and toy-only. Completed work belongs in generated
artifacts, README/AGENTS files, tests, manuscript fragments, and sheaf
registries rather than in this file.

## Current verification evidence

Current full-suite evidence: `uv run pytest tests/ --cov=src --cov-fail-under=90` passed 383 tests with 91.22% coverage in the 2026-06-12 audit. The same run used `COVERAGE_FILE=/tmp/template_ai.coverage` and `--durations=20 -q`, finishing in 1385.87 seconds. Replace this paragraph only after rerunning the full-suite command and updating the result from the fresh output.

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

## Lane glossary

| Lane | Source-of-truth files |
| --- | --- |
| Analytical | `src/analytical/`, `output/data/parameter_sweep.csv`, `output/data/analytical_observable_sweep.json`, `output/data/analytical_assumption_index.json`, `output/data/sensitivity_sweep.json`, `output/data/uncertainty_summary.json`, `output/data/toy_benchmark_matrix.json`, `output/data/state_space_catalog.json`, `output/data/causal_ablation_matrix.json` |
| pymdp | `pymdp.yaml`, `src/simulation/`, `output/data/si_tmaze_summary.json`, `output/data/si_tmaze_trace.json`, `output/data/si_policy_comparison.json`, `output/data/pymdp_policy_posterior_grid.json`, `output/reports/pymdp_runtime_diagnostics.json` |
| Formal | `lean/`, `gnn/`, `output/reports/model_checking_witnesses.json`, `output/data/theorem_traceability_matrix.json`, `output/data/proof_extraction_index.json`, `output/data/proof_dependency_graph.json` |
| Semantic | `manuscript/sheaf/tracks.yaml`, `manuscript/sheaf/manifest.yaml`, `output/data/sheaf_gluing_certificate.json`, `output/data/validation_dependency_graph.json`, `output/data/cross_track_symbol_table.json`, `output/data/manuscript_token_provenance.json`, `output/data/evidence_field_index.json` |
| Visualization | `figures.yaml`, `src/visualizations/`, `output/data/figure_source_map.json`, `output/reports/visualization_quality_audit.json`, `output/reports/figure_hash_manifest.json`, `output/data/statistical_visualization_bridge.json` |
| Release | `output/reports/release_bundle_manifest.json`, `output/reports/artifact_diffoscope.json`, `output/reports/artifact_license_audit.json`, `output/reports/release_notes_evidence.json`, `output/reports/release_attestation.json` |
| Scope | `output/reports/scope_boundary_audit.json`, `output/reports/blocked_scope_manifest.json`, `output/data/track_improvement_scope.json`, `output/data/scholarship_source_matrix.json`, `data/claim_ledger.yaml` |

## Minor upcoming

These rows are scoped maintenance work. They do not introduce live scientific
claims, new track IDs, artifact filenames, schema migrations, or figure IDs.

| ID | Size | Track lane | Future improvement | Proving artifact | Gate/predicate | Negative control |
| --- | --- | --- | --- | --- | --- | --- |

## Medium upcoming

These rows are real future verifier or cross-track improvements. Each one needs
additive artifacts or rows, a failing negative control, regenerated docs, and
green gates before it can be moved out of this file.

| ID | Size | Track lane | Future improvement | Proving artifact | Gate/predicate | Negative control |
| --- | --- | --- | --- | --- | --- | --- |
| `MEDIUM-TRACK-MATRIX-1` | Medium | Cross-track/release | Add a track-lane matrix mapping every `tracks.yaml` pipeline track to its sheaf fragment, producer, primary artifact, validation gate, and manuscript consumer | `output/data/track_lane_matrix.json` | `set_equals` between matrix track IDs, `tracks.yaml`, and sheaf manifest consumers | Pipeline track lacks a sheaf fragment, producer, artifact, gate, or consumer and still passes |
| `MEDIUM-TEST-PERF-1` | Medium | Test ergonomics | Split slow manuscript-gate mutation tests into cheaper source-only negative controls plus one end-to-end refresh characterization | parametrized source-contract tests and one end-to-end artifact-refresh test | focused gate tests preserve failures while `--durations=20` shows reduced redundant regeneration | Source-only mutation passes without exercising the matching contract |
| `MEDIUM-PROVENANCE-UNIFY-1` | Medium | Provenance/validation spine | Remove remaining producer-order sensitivity between validation-spine and sheaf-track artifacts by making shared artifact contracts explicit | `output/data/artifact_contract_index.json` | validation-spine and sheaf validators agree on shared keys, hashes, and freshness fields | Reordered producer leaves stale shared provenance accepted |
| `MEDIUM-SCOPE-MANIFEST-CONCORDANCE-1` | Medium | Scope/claim ledger | Derive scope-boundary blocked-context rows from `output/reports/blocked_scope_manifest.json` instead of duplicating the required blocked categories in the scope-audit builder | `output/reports/scope_boundary_audit.json` and `output/reports/blocked_scope_manifest.json` | blocked manifest IDs and scope-audit blocked categories agree exactly | Removing `llm_generated_evidence` from the blocked manifest leaves scope audit green |

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
| LLM-generated evidence | Claims must come from generated local artifacts, not opaque model output | `output/data/llm_evidence_audit.json` | evidence registry and claim-ledger gates | LLM-only claim passes evidence audit |
| Non-toy model claims | Current validation covers finite pedagogical examples only | `output/reports/model_scope_audit.json` | scope-boundary validator | Non-toy generalization appears in results |
