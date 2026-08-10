# template_active_inference TODO

This backlog is future-only. Completed validation and dated review evidence are preserved in
[`docs/maintenance/exemplar-backlog-history.md`](../../../docs/maintenance/exemplar-backlog-history.md)
or in source-owned generated receipts. Each active row must retain a stable ID, size, dependency,
proving artifact, acceptance command, and negative control; absence of an owner or external receipt
keeps a capability blocked rather than silently promoting it.

## Backlog operating rules

- Keep deterministic and offline defaults unchanged unless an upcoming row explicitly scopes an opt-in.
- Do not close a row until its producer, artifact, consumer, gate, and failing negative control are present.
- Treat unavailable network, LLM, container, formal-tool, and publication paths as explicit skips
  or blockers.
- Re-derive counts and receipts from live source data; never copy measurements into this planning file.

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

## Integrity and template-status gaps

Keep the standalone template boundary explicit: this exemplar is a forkable
starter for deterministic toy Active Inference manuscripts, not a source of
empirical biological claims. Future integrity work should first tighten
artifact/claim/release attestation around the existing canonical tracks before
adding new track IDs.

## Configurable-surface gaps

Future configurable surfaces should remain registry-owned. Add or change
capabilities through `tracks.yaml`, `manuscript/sheaf/tracks.yaml`,
`manuscript/sheaf/manifest.yaml`, `figures.yaml`, and
`manuscript/config.yaml`; keep `manuscript/config.yaml.example` structurally in
parity with placeholder-safe values whenever a top-level section is added.

## Documentation and signposting gaps

Every new capability needs a reader-facing signpost in the nearest README or
AGENTS file that states whether it is generic sheaf infrastructure or a
bespoke Active Inference lane. Publication, fork, and standalone guidance must
continue to point at generated records or `STANDALONE.md` instead of copying
release facts into prose.

## Test and validator gaps

Promote only changes with a positive artifact test and a negative control that
proves the matching gate fails closed. Keep long-running full-refresh tests as
end-to-end sentinels, but prefer narrower row-contract tests for future
regression coverage when they preserve the same failure mode.

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

## Minor upcoming

No active rows are currently scoped at this size.

## Medium upcoming

| ID | Size | Dependency | Proving artifact | Acceptance command | Negative control |
| --- | --- | --- | --- | --- | --- |
| `MEDIUM-TEST-PERF-1` | Medium | Test ergonomics; isolated project refresh | cheaper source/row-contract negative controls plus one end-to-end artifact-refresh test | focused gate tests plus `--durations=20` comparison | Source-only mutation passes without exercising the matching contract |
| `MEDIUM-SUBPROCESS-POLICY-1` | Medium | Test ergonomics; release wrappers | future subprocess-wrapper policy audit generated from source-owned declarations | policy audit and a focused mutation of one wrapper policy field | Wrapper without timeout, cwd, check, or useful failure text passes the policy audit |

## Major upcoming

No active rows are currently scoped at this size.

## Backlog status

Rows remain active until the acceptance command and negative control pass in the same source revision.
A blocked major row is a deliberate boundary, not a skipped success.
