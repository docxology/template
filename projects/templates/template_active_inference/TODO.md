# template_active_inference TODO

This roadmap is future-only. It is not the current artifact contract and it does
not create publication claims. Current publication claims remain deterministic,
public, locally reproducible, and toy-only. The live system uses stable canonical
track IDs; future work should deepen canonical tracks such as `provenance`,
`replay_matrix`, `sensitivity`, `uncertainty`, `model_checking`, `interop`,
`adversarial_audit`, `evidence_fields`, `release_bundle`,
`theorem_traceability`, `gate_ergonomics`, `artifact_diffoscope`,
`proof_extraction`, `state_space_catalog`, `causal_ablation`,
`artifact_license`, and `release_notes` rather than adding `_vN` siblings.

## Current baseline

The current system is a validated multi-track toy Active Inference exemplar with
canonical sheaf tracks, semantic gluing, dependency graph, typed claim evidence,
manuscript hydration, Lean/GNN/ontology checks, graph-world and animation
artifacts, and a blocked empirical boundary. Live proofs belong in the registry,
project docs, generated certificates, `output/data/track_improvement_scope.json`,
and output reports rather than repeated here as completed TODO work.

## Promotion rule

A future capability becomes live only after every row below is satisfied in the
repository and passes under the core pipeline. Each roadmap row must identify a
proving artifact, a gate or typed predicate, and a negative control before
implementation begins.

| Requirement | Minimum proof before promotion |
| --- | --- |
| Producer | Configured script or renderer in the analysis DAG |
| Artifact | Deterministic file under `output/data/`, `output/reports/`, or `output/figures/` |
| Manuscript consumer | Bound IMRAD fragment or generated evidence table |
| Typed claim evidence | Claim-ledger predicate with explicit field, expected value, tolerance, or list predicate |
| Semantic restriction | Certificate field that catches disagreement, missing evidence, or stale output |
| Validation gate | `validate_outputs`, `validate_manuscript`, `lake build`, or project test |
| Negative control | Test that mutates artifact/config/claim text and proves the gate fails |

## Within-track roadmap

| ID | Canonical track area | Future improvement | Proving artifact | Gate or predicate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AI-ANALYTICAL-OBS-4` | Analytical | Add another closed-form finite toy observable with equation and assumption cross-links | `output/data/analytical_observable_sweep.json` | `approx` residual plus `set_equals` equation ids | Perturbed observable value passes tolerance |
| `AI-PYMDP-RUNTIME-3` | PyMDP/JAX | Split runtime diagnostics into construction, inference, backend, warning, and fallback rows | `output/reports/pymdp_runtime_diagnostics.json` | `equals` unexpected warning count `0` and `all` fallback rows explained | Unexpected warning is accepted |
| `AI-PYMDP-POLICY-3` | PyMDP/T-maze | Add measured policy posterior summaries for every configured mode/horizon/seed cell | `output/data/pymdp_policy_posterior_grid.json` | `set_equals` configured grid and `all` normalized posteriors | Missing or unnormalized posterior cell passes |
| `AI-PYMDP-EFE-3` | PyMDP/T-maze | Record decomposed EFE terms where available and explicit fallback reasons otherwise | `output/data/si_efe_terms.json` | `all` rows have terms or fallback reason | Row lacks both terms and fallback |
| `AI-GRAPH-TOPOLOGY-3` | Graph-world | Add one richer deterministic finite topology with trace, invariant, and model-checking links | `output/data/si_graph_world_topology_traces.json` | `all` topology summaries agree with traces and witnesses | Summary path length disagrees with trace |
| `AI-ANIMATION-HASH-2` | Animation | Add stable per-frame perceptual hashes and frame metadata to the delta manifest | `output/data/animation_frame_deltas.json` | `len_min` frames and `all` nonzero deltas/hashes | Duplicate/static frames pass |
| `AI-VIZ-PIXEL-2` | Visualization | Expand figure source mapping to data-to-pixel provenance for every deterministic figure | `output/data/figure_source_map.json` | `set_equals` figure ids against `figures.yaml` | Figure lacks source artifact |
| `AI-LEAN-BELIEF-3` | Lean/model-checking | Add constructive finite belief-update normalization theorems tied to generated toy artifacts | `output/reports/lean_theorem_inventory.json` | `set_equals` theorem names and `all` proved | `sorry`, `axiom`, `native_decide`, or missing theorem passes |
| `AI-GNN-SHAPE-3` | GNN | Require every variable to carry exactly one ontology term, dtype, shape, and round-trip row | `output/reports/gnn_lint_report.json` | `all` variables mapped once with type and shape | Duplicate alias or missing shape passes |
| `AI-ONTOLOGY-PROFILE-3` | Ontology | Add model-specific ontology profiles for graph-world and each toy benchmark model | `output/data/ontology_profile_matrix.json` | `all` model variables mapped once | Profile introduces unused or unmapped term |
| `AI-MANUSCRIPT-TOKEN-3` | Manuscript/hydration | Extend token provenance to generated tables, appendix fragments, and figure captions | `output/data/manuscript_token_provenance.json` | `set_equals` rendered tokens and provenance keys | Edited hydrated output hides stale value |
| `AI-CLAIM-PREDICATE-3` | Claim ledger | Improve predicate failure messages and require substantive evidence or explicit waiver for every claim | `output/reports/claim_evidence_audit.json` | `all` claims have evidence, waiver, tracks, and section | Path-only claim passes as evidence |
| `AI-GATE-INDEX-3` | Gate ergonomics | Emit one row per validator check with command, required input, output, and negative control | `output/data/validation_gate_index.json` | `set_equals` validator ids and dependency ids | Validator lacks declared artifact inputs |

## Integration roadmap

| ID | Canonical integration target | Future improvement | Proving artifact | Gate or predicate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AI-SEMANTIC-CLASSIFIED-1` | Semantic certificate | Add typed restriction classes and explicit proof-obligation records inside the canonical certificate | `output/data/sheaf_gluing_certificate.json` | `all` proof obligations ok and typed | Saved certificate omits a required proof obligation |
| `AI-DEPENDENCY-FIELDS-1` | Dependency graph | Add field-level JSONPath edges and artifact-to-rendered-prose span links inside the canonical dependency graph | `output/data/validation_dependency_graph.json` | `set_equals` required edge types plus field-level edge count | Artifact field appears in prose without dependency edge |
| `AI-PROVENANCE-FIELDS-1` | Provenance | Broaden source commit, config digest, seed, producer, and input-artifact lineage to field-level rows | `output/data/artifact_provenance.json` | `all` required fields have hash, producer, seed/config, and source commit | Changed artifact hash passes as current |
| `AI-RELEASE-PARITY-1` | Release bundle | Compare project-local outputs, copied root outputs, PDF/web deliverables, and required hashes after the root pipeline | `output/reports/release_bundle_manifest.json` | `all` copied outputs match or are explicitly deferred before render | Copied root output drift passes |
| `AI-EVIDENCE-FIELDS-1` | Evidence fields | Link every claim field and manuscript token to a JSONPath, validator, and semantic restriction | `output/data/evidence_field_index.json` | `all` evidence fields mapped and source-backed | Claim field lacks a JSONPath edge |
| `AI-THEOREM-LINKS-1` | Theorem traceability | Join Lean theorem inventory, model-checking witnesses, finite models, claims, and evidence fields | `output/data/theorem_traceability_matrix.json` | `all` theorem rows linked to claims and artifacts | Theorem inventory row has no claim or artifact |
| `AI-STALE-LIVE-1` | Stale-artifact controls | Rebuild live semantic fields after upstream artifact mutation and compare against saved canonical reports | `output/reports/stale_artifact_report.json` | `all` stale flags false and saved fields match live fields | Touching upstream JSON leaves stale report passed |
| `AI-SYMBOL-SPINE-3` | Cross-track symbols | Expand the symbol table across GNN, ontology, Lean theorem names, manuscript variables, JSON fields, and figure labels | `output/data/cross_track_symbol_table.json` | `all` symbols have consistent type, shape, ontology, and consumer | Same symbol has incompatible meanings |
| `AI-SCOPE-ROWS-1` | Scope boundary | Make scope classification row-level for current, future, empirical, and blocked-language contexts | `output/reports/scope_boundary_audit.json` | `all` current-result rows classified toy-only | Empirical wording appears outside future/blocked context |

## Future sheaf tracks

The proposed IDs below are not live tracks. Do not add them to
`manuscript/sheaf/tracks.yaml`, `tracks.yaml`, manuscript fragments, or public
claims until the promotion rule is fully satisfied. These names are stable
non-versioned candidates; if promoted, they should remain canonical rather than
spawning tranche-numbered siblings.

| Proposed id | Purpose | First artifact | First manuscript binding | First gate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `proof_dependency_graph` | Expand extracted Lean proof dependencies into theorem-to-definition edges | `output/data/proof_dependency_graph.json` | `methods_lean/proof_dependency_graph.md` | proof dependency validator plus `lake build` | Theorem dependency edge is dropped |
| `state_transition_table` | Emit explicit finite transition tables for every toy topology and T-maze action | `output/data/state_transition_table.json` | `results_invariants/state_transition_table.md` | transition-table validator | Transition table omits a reachable state |
| `ablation_sensitivity_report` | Summarize causal-ablation effects against sensitivity and uncertainty rows | `output/reports/ablation_sensitivity_report.json` | `results_invariants/ablation_sensitivity_report.md` | ablation-sensitivity validator | Ablation effect is reported without source row |
| `release_attestation` | Generate a compact attestation over validation report, bundle hash, license audit, and blocked scope | `output/reports/release_attestation.json` | `discussion_outlook/release_attestation.md` | release-attestation validator | Attestation claims a failed gate passed |
| `empirical_adapter` | Future-only bridge for real datasets after provenance, licensing, privacy, and typed claim gates exist | `output/data/empirical_adapter_manifest.json` | `discussion_outlook/empirical_adapter.md` | blocked until explicit data gates exist | Empirical claim appears without manifest |

## Blocked scope

The following remain explicitly out of scope until a later plan promotes them
with provenance, licensing/privacy review, typed claim evidence, semantic
restrictions, gates, and negative controls.

| Blocked area | Why blocked | Required unblock artifact | Required gate | Negative control |
| --- | --- | --- | --- | --- |
| Empirical biological claims | Current artifacts are deterministic toy models, not biological data | `output/data/empirical_adapter_manifest.json` | scope-boundary and claim-ledger gates | Empirical result prose without manifest fails |
| Private or restricted data | This exemplar is public and self-contained | `output/reports/data_provenance_audit.json` | provenance and license validator | Private path or unlicensed source passes |
| Network-dependent research | Pipeline must remain locally reproducible | `output/reports/offline_reproducibility_audit.json` | offline pipeline gate | Network call required for core pipeline |
| LLM-generated evidence | Claims must come from generated local artifacts, not opaque model output | `output/reports/evidence_source_audit.json` | evidence registry and claim-ledger gates | LLM-only claim passes evidence audit |
| Non-toy model claims | Current validation covers finite pedagogical examples only | `output/reports/model_scope_audit.json` | scope-boundary validator | Non-toy generalization appears in results |

## Suggested order

1. Keep this roadmap future-only; completed live tracks belong in README,
   AGENTS, registries, and generated outputs.
2. Deepen canonical semantic/dependency/provenance/evidence-field rows before
   adding another live track.
3. Prefer finite toy evidence, negative controls, and typed claim predicates
   over broader prose claims.
4. Leave `empirical_adapter` blocked until the unblock artifacts and gates above
   exist and fail closed.

## Deferred review follow-ups (2026-06-02 deep-improvement session)

The 2026-06-02 multi-reviewer audit shipped its keystone correctness/honesty
fixes (deterministic-recompute relabel, genuine GNN round-trip, per-file proof
provenance, duplicate-marker gate, pandoc-crossref single-source figure
numbering, 4 added negative controls, enriched abstract/derivation/pymdp prose).
The rows below are the remaining, non-blocking improvements identified by that
audit. They carry no publication claim and remain future-only under the
promotion rule above.

| ID | Area | Improvement | Proving artifact | Gate or predicate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AI-STALE-SUMMARY-1` | Validation gates | Re-derive every `all_*` aggregate from its rows inside each validator instead of trusting the precomputed summary boolean | existing track JSON summaries | re-derived aggregate equals stored aggregate | mutate one row, leave summary `true`, assert gate fails |
| `AI-EFE-NONVACUOUS-1` | PyMDP/EFE | Make `all_rows_explained` bind a real condition (a `terms_available` row must carry non-empty `terms`; a fallback row must draw `fallback_reason` from measured reasons); rename schema to `si_efe_values` to stop over-promising a term decomposition | `output/data/si_efe_terms.json` | `terms_available` ⇒ non-empty terms | `terms_available=true` + empty terms passes |
| `AI-STUB-DEPTH-1` | Fragments | Expand 6 thin-stub teaching fragments (causal_ablation, state_space_catalog, proof_extraction, artifact_diffoscope, artifact_license, release_notes) to sibling 2-paragraph pedagogy depth | composed manuscript | token gate (all `{{tokens}}` resolve) | n/a (prose) |
| `AI-APPENDIX-HYDRATE-1` | Integration | Hydrate the zero-token appendix cells (counterexample, manuscript_staleness, assumption_index) with existing counts; retire the near-orphan `manuscript/refs/labels.yaml` second figure registry | composed appendix | token gate | edited hydrated output hides stale value |
| `AI-APPENDIX-FIGURES-1` | Visualization | Add two appendix figures (theorem-traceability 3-column graph; causal-ablation heatmap) deriving rows from JSON keys, numbered by pandoc-crossref after the main 1-N | `figures.yaml` + generators | `test_figure_generators_match_registry` | figure lacks source artifact |
| `AI-HYGIENE-1` | Cleanup | Tolerance SSOT, duplicate skipif decorator, GNN `_parse_param_blocks` tests, poset-law prose sharpening, Bernoulli 8-symbol enumeration via `{{bernoulli_ontology_term_count}}` | n/a | full suite + ruff/mypy | n/a |

## Known residual (2026-06-02): full-suite artifact-isolation flakiness

Every test passes in isolation and coverage passes at 92.03% (`fail_under = 90`),
but the full `pytest tests/` run is order/load-sensitive: the set of failing
artifact-validation tests (e.g. `test_semantic_certificate_*`,
`test_canonical_sheaf_*`, `test_validate_manuscript_contract`,
`test_promoted_roadmap_artifacts_*`) varies run-to-run (observed 1→11→2→4 across
runs at 2x normal wall-clock under machine load ~8). Root cause is the stateful
diffoscope (rows derived from `artifact_provenance.json` rows) and semantic
certificate carrying cross-test state under the run-once `ensure_gate_artifacts`
guard, exposed when artifacts regenerate concurrently. `test_integration_audit_
negative_controls` was hardened (regenerates its own diffoscope precondition).

| ID | Area | Improvement | Proving artifact | Gate or predicate | Negative control |
| --- | --- | --- | --- | --- | --- |
| `AI-TEST-ISOLATION-1` | Test infra | Make artifact-validation tests order-independent: either regenerate meta-artifacts (provenance/diffoscope/semantic certificate) at the start of each, or make those comparisons stateless within a single write→validate call | n/a (test infra) | `pytest tests/` green across 5 consecutive runs on an idle host | shuffle test order (`-p randomly`) stays green |
