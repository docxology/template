# template_active_inference TODO

This backlog is future-only. It is not the current artifact contract and does
not create publication claims. Current claims remain deterministic,
locally reproducible, public, and toy-only. Completed work belongs in generated
artifacts, README/AGENTS files, tests, manuscript fragments, and sheaf
registries rather than in this file.

## Current verification evidence

Current evidence on 2026-06-13:

```bash
COVERAGE_FILE=/tmp/template_ai_track_lane.coverage uv run pytest tests/ --cov=src --cov-fail-under=90 --durations=20 -q
```

`uv run pytest tests/ --cov=src --cov-fail-under=90` passed 392 tests with
90.81% coverage in 1320.85s (0:22:00), run with
`COVERAGE_FILE=/tmp/template_ai_track_lane.coverage`, `--durations=20`, and
`-q`. Focused visualization/style/gate evidence also passed:
`uv run pytest tests/test_figures.py tests/test_figure_style.py tests/gates/ -q`
returned 58 passed in 240.82s (0:04:00). Manuscript mutation gates now restore
byte-for-byte edits directly and reserve recomposition for the source-fragment
duplicate-marker case.

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
| Visualization | `figures.yaml`, `src/visualizations/`, `src/roadmap_tracks/visualization_contract.py`, `output/data/figure_source_map.json`, `output/reports/visualization_quality_audit.json`, `output/reports/figure_hash_manifest.json`, `output/data/statistical_visualization_bridge.json` |
| Release | `output/reports/release_bundle_manifest.json`, `output/reports/artifact_diffoscope.json`, `output/reports/artifact_license_audit.json`, `output/reports/release_notes_evidence.json`, `output/reports/release_attestation.json`, `output/reports/security_posture_audit.json` |
| Scope | `output/reports/scope_boundary_audit.json`, `output/reports/blocked_scope_manifest.json`, `output/data/track_improvement_scope.json`, `output/data/scholarship_source_matrix.json`, `data/claim_ledger.yaml` |

## Minor upcoming

These rows are scoped maintenance work. They do not introduce live scientific
claims, new track IDs, artifact filenames, schema migrations, or figure IDs.
No active minor rows are currently scoped; keep this table empty until a narrow
future-only maintenance item has a proving artifact, gate, and negative control.

| ID | Size | Track lane | Future improvement | Proving artifact | Gate/predicate | Negative control |
| --- | --- | --- | --- | --- | --- | --- |

## Medium upcoming

These rows are real future verifier or cross-track improvements. Each one needs
additive artifacts or rows, a failing negative control, regenerated docs, and
green gates before it can be moved out of this file.

The visualization style, auxiliary-output, accessibility, and dense-matrix
readability rows scoped on 2026-06-13 are implemented in the generated
visualization-quality audit rather than retained as open TODO rows: the audit
now recomputes typography-token minima, rejects raw font-size literals in figure
generators, classifies non-registry visual outputs, and binds those checks into
`validate_outputs` and the semantic restrictions.

| ID | Size | Track lane | Future improvement | Proving artifact | Gate/predicate | Negative control |
| --- | --- | --- | --- | --- | --- | --- |
| `MEDIUM-TEST-PERF-1` | Medium | Test ergonomics | Continue splitting repeated full-refresh mutation tests in roadmap-promotion and claim-ledger paths while retaining one fixed-point refresh characterization | cheaper source/row-contract negative controls plus one end-to-end artifact-refresh test | focused gate tests preserve failures while `--durations=20` shows reduced redundant regeneration; current slowest rows are roadmap-promotion and claim-ledger refreshes | Source-only mutation passes without exercising the matching contract |

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

## Major unblock ladder

Do not start these as feature work until the previous rung is green. Each rung
must preserve the public, deterministic default path and leave current toy claims
unchanged.

| Rung | New capability class | Minimum unblock before promotion |
| --- | --- | --- |
| 1 | Empirical adapters | Public fixture manifest, license/privacy audit, deterministic replay cache, and claim-ledger predicates that distinguish toy from empirical evidence |
| 2 | Network research | Offline cache manifest, fetch provenance, dependency pinning, no-network validation mode, and stale-cache negative controls |
| 3 | LLM evidence | Prompt/model/version manifest, deterministic transcript artifact, human-review provenance, and explicit non-authoritative evidence labeling |
| 4 | Private data | External private-data sidecar, redaction manifest, access-boundary audit, license/privacy approval artifact, and zero private path leakage in public outputs |
| 5 | Non-toy model claims | Scope-specific model card, expanded state-space/proof obligations, empirical/benchmark provenance, uncertainty calibration, and claim predicates that fail on toy-only evidence |
