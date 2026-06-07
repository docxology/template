```{=latex}
\phantomsection
\addcontentsline{toc}{section}{Appendix}
\section*{Appendix}
```

# Appendix: full track coverage {#sec:appendix_full_sheaf}

<!-- sheaf-track:prose -->

This section is the **composability proof** for the manifest-indexed sheaf model: all {{appendix_sheaf_track_count}} appendix-bound fragment tracks render into one flat manuscript section without section-specific compose branches. The registry defines {{sheaf_track_count}} composable types; optional `layers` is methods-only and excluded from this row. The `animation` fragment is bound here as an optional registry type alongside the live proof, simulation, formal, notation, validation-spine, integration, audit, finite-catalog, ablation, license, release-evidence, scholarship, assumption-index, delta, and staleness tracks.

The proof is a publication-systems check ([@eq:appendix_track_count]). It demonstrates that heterogeneous fragments share one registry, manifest, renderer dispatch path, coverage matrix, and hydration boundary; it does not assert that every track carries equal scientific weight.

<!-- sheaf-track:formalism -->

For each track $t \in \mathcal{T}_{\mathrm{Full}}$, the appendix row binds a fragment path $f(t)$ and the composer emits `<!-- sheaf-track:t -->` before the rendered body. Generated renderers such as `section_figures` and markdown renderers pass through the same `resolve_track_body()` dispatch, so the appendix exercises the common compose interface rather than a bespoke appendix path.

$$
|\mathcal{T}_{\mathrm{Full}}| = {{appendix_sheaf_track_count}}
$$ {#eq:appendix_track_count}

The fragment registry defines {{sheaf_track_count}} composable track types; optional `layers` is bound on the methods sheaf section only. Optional `animation` is bound in this appendix proof; the deterministic GIF artifact in `tracks.yaml` `extension_tracks` is produced by the core analysis DAG and remains separate from this fragment slot.

Because this appendix binds every non-optional appendix track plus optional `animation`, it is the maximal publication stalk of the coverage presheaf and exercises every publication renderer through the common `resolve_track_body()` dispatch. The same compose path is gated by the {{sheaf_law_count}} sheaf laws verified in [@sec:methods_sheaf] ({{sheaf_laws_verified}}/{{sheaf_law_count}} satisfied): the appendix section glues to a unique output (separation), occupies the terminal position of the linear extension under its own `appendix` group row (poset and gluing), binds only well-typed fragments (typing), and owns every fragment path it references (compositionality). No count in this appendix is hand-written; all are injected from the registry-backed oracle.

<!-- sheaf-track:simulation -->

Analytical sweep artifacts feed [@sec:results_mi_sweep] and [@sec:results_invariants]; simulation invariants merge after [@sec:results_si_tmaze]. No additional path listing is required beyond those Results sections.

<!-- sheaf-track:assumption_index -->

The appendix `assumption_index` row points to
`output/data/analytical_assumption_index.json`. It binds
{{analytical_assumption_count}} finite Bernoulli-Ising assumption rows to
{{analytical_equation_count}} equation identifiers and generated artifacts, with
indexed status `{{analytical_assumptions_indexed}}`.

The point is to make analytical signposting mechanical. If an equation is added
without an assumption row, or if a row loses its evidence artifact, the index
gate fails and the manuscript cannot present the equation as part of the
validated finite toy proof surface.

<!-- sheaf-track:pymdp -->

pymdp harness summary: `output/data/si_tmaze_summary.json` (mean belief entropy, action trace). Runtime diagnostics: `output/reports/pymdp_runtime_diagnostics.json` (known warnings {{pymdp_runtime_known_warning_count}}, unexpected warnings {{pymdp_runtime_unexpected_warning_count}}). Policy posterior grid: `output/data/pymdp_policy_posterior_grid.json` ({{pymdp_policy_posterior_row_count}} rows). Full log: `output/logs/pymdp_runs.jsonl`.

<!-- sheaf-track:interop -->

`sheaf-track:interop` binds `output/data/interop_roundtrip_report.json`, `output/data/gnn_roundtrip_report.json`, `output/reports/gnn_lint_report.json`, and ontology profile artifacts into the appendix proof row. The appendix claim is exactly {{interop_check_count}} checks with lossless status `{{interop_all_lossless}}`.

<!-- sheaf-track:provenance -->

The appendix provenance fragment points to `output/data/artifact_provenance.json`, the canonical artifact that records required toy artifact hashes, producer scripts, source commit, deterministic seeds, config digests, and {{provenance_bundle_count}} bundle rows.

<!-- sheaf-track:replay_matrix -->

`replay_matrix.json` provides the appendix proof for deterministic replay: {{replay_matrix_row_count}} producer replay/fingerprint rows with matched status `{{replay_matrix_all_matched}}`.

<!-- sheaf-track:counterexample -->

The appendix counterexample fragment points to
`output/reports/counterexample_matrix.json`, the expected-failure matrix that
keeps promoted validation gates falsifiable. It currently records
{{counterexample_count}} known-bad fixtures, and the hydrated pass flag is
`{{counterexample_all_known_bad_fail}}`, meaning those fixtures are expected to
fail rather than sneak through a positive-control gate.

This row is the negative-control ledger for the sheaf. Each counterexample names
a promoted track, target validation gate, mutation, and observed expected-failure
status. A new live track without a counterexample row is therefore visibly
incomplete in the track-improvement scope.

<!-- sheaf-track:adversarial_audit -->

`sheaf-track:adversarial_audit` binds `output/reports/adversarial_audit.json`, `output/reports/scope_boundary_audit.json`, and claim-audit outputs. The appendix claim is exactly {{adversarial_audit_count}} expected-failure rows with documented status `{{adversarial_audit_all_documented}}` and known-bad-passing count {{adversarial_known_bad_passed}}.

<!-- sheaf-track:evidence_fields -->

`evidence_field_index.json` provides the appendix proof for field-level claim evidence: {{evidence_field_count}} mapped fields with status `{{evidence_fields_mapped}}`.

<!-- sheaf-track:release_bundle -->

`release_bundle_manifest.json` provides the appendix proof for required deliverables: {{release_bundle_artifact_count}} artifacts with source-present status `{{release_bundle_sources_present}}`.

<!-- sheaf-track:gate_ergonomics -->

`validation_gate_index.json` provides the appendix proof for gate ergonomics: {{validation_gate_index_count}} indexed gates.

<!-- sheaf-track:artifact_diffoscope -->

### Appendix track: artifact diffoscope

`artifact_diffoscope` binds `output/reports/artifact_diffoscope.json` into the
full sheaf appendix. Rows: {{artifact_diffoscope_row_count}}. All equal:
`{{artifact_diffoscope_all_equal}}`.

This diffoscope is deliberately narrow and reproducibility-facing. For each
non-cyclic generated artifact, it compares the saved provenance digest to the
live file digest at validation time. The validator re-derives equality from the
rows, so a stale `all_equal: true` summary cannot hide one changed artifact.

The row count is not a decoration; it is the number of artifact fingerprints
that survived cycle exclusion and therefore can be compared directly. This
keeps the release bundle honest about mutable files while avoiding
self-referential hashes for artifacts that necessarily include their own
provenance.

<!-- sheaf-track:artifact_license -->

### Appendix track: artifact license

`artifact_license` binds `output/reports/artifact_license_audit.json` into the
full sheaf appendix. Rows: {{artifact_license_row_count}}. All safe:
`{{artifact_license_all_safe}}`.

The license audit classifies each generated or source-backed artifact under the
public exemplar's configured license boundary. It is intentionally conservative:
generated local outputs and project-owned source files pass, while an artifact
outside those public source kinds would need an explicit provenance and license
row before it could support a manuscript claim.

This is also where the blocked empirical-adapter boundary matters. Private,
restricted, or network-derived data are not smuggled in as evidence; they remain
blocked until privacy, licensing, typed-claim, semantic, and negative-control
gates are implemented in the same artifact path.

<!-- sheaf-track:scholarship -->

`sheaf-track:scholarship` binds `output/data/scholarship_source_matrix.json` into
the appendix proof row. The appendix claim is exactly
{{scholarship_source_count}} connected source rows with connected status
`{{scholarship_sources_connected}}`; each row names a bibliography key, method
role, manuscript section, registered track set, evidence artifact, and
claim-boundary statement. The row set includes
{{scholarship_quantitative_method_role_count}} quantitative/statistical or
visualization-quality method roles, including {{visualization_statistics_backed_count}}
statistically backed figures with bridge status
`{{visualization_statistics_bridge_ok}}`. The explicit crosswalk has
{{statistical_visualization_bridge_row_count}} rows and
{{statistical_visualization_bridge_source_count}} statistical source links; every
row is referenced in the manuscript
(`{{statistical_visualization_bridge_all_referenced}}`), and every such
reference section is manifest-bound to sheaf tracks
(`{{statistical_visualization_bridge_references_sheaf_bound}}`) with a
visualization track present
(`{{statistical_visualization_bridge_references_visualization_bound}}`). This
binds statistics and figure-quality claims to generated artifacts rather than
bibliography authority.

The visualization registry is also now a paper-integration object: role metadata
complete `{{visualization_intent_metadata_complete}}`, paper claims complete
`{{visualization_paper_claims_complete}}`, and section bindings complete
`{{visualization_figures_section_bound}}`. Those flags are read from the saved
visualization-quality audit and then rechecked through the semantic sheaf
restrictions.

<!-- sheaf-track:sensitivity -->

`sheaf-track:sensitivity` binds `output/data/sensitivity_sweep.json`, measured `output/data/si_policy_grid.json`, compatibility-named EFE values artifact `output/data/si_efe_terms.json`, `output/data/analytical_observable_sweep.json`, and graph-world topology artifacts including `output/data/si_graph_world_topology_traces.json`. The appendix claim is exactly {{sensitivity_cell_count}} complete canonical grid cells.

<!-- sheaf-track:uncertainty -->

`sheaf-track:uncertainty` binds `output/data/uncertainty_summary.json`. The appendix claim is exactly {{uncertainty_row_count}} normalized rows across {{uncertainty_bin_count}} entropy bins with status `{{uncertainty_all_normalized}}`.

<!-- sheaf-track:benchmark -->

`sheaf-track:benchmark` binds `output/data/toy_benchmark_matrix.json`. The appendix claim is exactly {{benchmark_model_count}} complete toy-model rows with status `{{benchmark_all_models_complete}}`.

<!-- sheaf-track:manuscript_staleness -->

The appendix `manuscript_staleness` row points to
`output/reports/manuscript_staleness_report.json`. It checks
{{manuscript_staleness_row_count}} token bindings after hydration, including late
audit variables, and the pass flag is `{{manuscript_staleness_all_fresh}}`.

This is the rendered-output side of the sheaf contract. Source fragments may
contain hydration placeholders, but the public manuscript must not; the staleness report
compares each token's generated value against the resolved markdown so stale
counts are caught after composition, not only during source-file linting.

<!-- sheaf-track:visualization -->

![](../output/figures/ising_mi_curve.png){width=90%}

*Reproduced from [@fig:ising_mi_curve]. Closed-form $I(\lambda)$ and an independent exact recomputation via total correlation for the symmetric Bernoulli-Ising toy across {{param_sweep_grid_points}} grid points up to $\lambda_{\max}$ = {{lambda_max}}; grid maximum {{ising_mi_saturation}} nats. Both estimators are deterministic (no sampling), so the right panel is a cross-implementation agreement check (max residual {{sweep_max_residual}} nats), not a sampling residual.*

![](../output/figures/si_tmaze_actions.png){width=90%}

*Reproduced from [@fig:si_tmaze_actions]. Discrete action index over time for the pymdp T-maze rollout (policy length {{si_tmaze_policy_len}}).*

![Theorem traceability graph generated from {{theorem_traceability_row_count}} linked theorem rows and {{proof_dependency_edge_count}} proof-dependency edges.](../output/figures/theorem_traceability_graph.png){#fig:theorem_traceability_graph width=95% fig-alt="Three-column graph generated from theorem traceability and proof dependency JSON. Each row links a Lean theorem to its proof-dependency edge count and finite model witness count; all theorem rows have resolved dependency edges: {{proof_dependency_all_resolved}}."}

![Causal-ablation heatmap: {{ablation_sensitivity_row_count}} source-backed rows joined to sensitivity and uncertainty artifacts; all effects source-backed: {{ablation_sensitivity_source_backed}}.](../output/figures/causal_ablation_heatmap.png){#fig:causal_ablation_heatmap width=92% fig-alt="Heatmap generated from the causal ablation and sensitivity reports. Rows are toy graph topologies, columns are perturbation types, and each cell shows the maximum absolute deterministic effect sourced from generated JSON rows."}

![](../output/figures/scholarship_source_map.png){width=95%}

*Reproduced from [@fig:scholarship_source_map]. Scholarship source map: {{scholarship_source_count}} source rows across {{scholarship_method_role_count}} method roles and {{scholarship_source_family_count}} source families. Connected status: {{scholarship_sources_connected}}.*

![](../output/figures/sheaf_coverage_heatmap.png){width=95%}

*Reproduced from [@fig:sheaf_coverage_heatmap]. Sheaf track coverage matrix: {{imrad_manifest_rows}} IMRAD rows × {{sheaf_track_count}} fragment columns. Black = present (P), white = absent (—), gray = missing (M). Counts: {{coverage_present}} present / {{coverage_bound}} bound / {{coverage_missing}} missing.*

<!-- sheaf-track:lean -->

Lean modules under `lean/TemplateActiveInference/` declare horizon and coupling witnesses. Build with `lake build` in `lean/`; [@fig:lean_boundary_status] summarizes proved versus deferred statements for this boundary fragment.

<!-- sheaf-track:model_checking -->

`sheaf-track:model_checking` binds `output/reports/model_checking_witnesses.json` and the Lean theorem inventories. The appendix claim is exactly {{model_checking_witness_count}} finite exhaustive witnesses with pass status `{{model_checking_all_passed}}`; Lean graph-world topology coverage is {{lean_graph_world_topology_witness_count}} generated topology ids with all-witnessed flag `{{lean_graph_world_all_topologies_witnessed}}`.

<!-- sheaf-track:theorem_traceability -->

`theorem_traceability_matrix.json` provides the appendix proof for theorem traceability: {{theorem_traceability_row_count}} linked rows with status `{{theorem_traceability_linked}}`.

<!-- sheaf-track:proof_extraction -->

### Appendix track: proof extraction

`proof_extraction` binds `output/data/proof_extraction_index.json` into the full
sheaf appendix. Extracted theorems: {{proof_extraction_theorem_count}}.
Constructive status: `{{proof_extraction_all_constructive}}`.

The extraction index is intentionally modest: it records theorem names,
statements, source files, leading tactics, and forbidden proof-token checks.
That makes the Lean boundary inspectable without pretending that every proof
term has been translated into a proof object. A row with a missing statement or
forbidden token fails the formal interop gate and the canonical sheaf gate.

`output/data/proof_dependency_graph.json` adds the dependency view used by the
appendix figure. It contributes {{proof_dependency_edge_count}} theorem-source,
theorem-tactic, theorem-definition, and theorem-witness edges, with resolved
edge status `{{proof_dependency_all_resolved}}`; this is the artifact that keeps
the theorem-traceability graph tied to generated Lean and model-checking rows.

<!-- sheaf-track:state_space_catalog -->

### Appendix track: state-space catalog

`state_space_catalog` binds `output/data/state_space_catalog.json` into the full
sheaf appendix. Rows: {{state_space_catalog_row_count}}. All finite:
`{{state_space_catalog_all_finite}}`.

The catalog is the finite-scope boundary for every toy claim in the exemplar.
Each row records a model id, state count, action count, policy count, source
artifact, and finite flag; the validator recomputes that counts are positive
and that every row remains finite. This prevents a manuscript sentence about
exhaustive checking from silently drifting into an unbounded or empirical
setting.

`output/data/state_transition_table.json` makes the boundary operational. It
contains {{state_transition_row_count}} deterministic transition rows and covers
all reachable finite models with status `{{state_transition_all_covered}}`.
Readers can therefore audit not just the number of states, but the actual
state/action/next-state relation used by the model-checking witnesses.

<!-- sheaf-track:causal_ablation -->

### Appendix track: causal ablation

`causal_ablation` binds `output/data/causal_ablation_matrix.json` into the full
sheaf appendix. Cells: {{causal_ablation_row_count}}. Complete grid:
`{{causal_ablation_complete_grid}}`.

The matrix is a finite teaching device: every row names a topology, a coupling
value, a perturbation, a scalar effect, and the generated source row that made
the effect admissible. It is not a claim about empirical interventions. It
shows how an intervention-shaped table can be made falsifiable inside the sheaf:
delete one perturbation cell or clear one deterministic flag and the grid gate
fails before the manuscript can reuse the result.

`output/reports/ablation_sensitivity_report.json` then joins those ablation
effects to the sensitivity and uncertainty artifacts. The report contributes
{{ablation_sensitivity_row_count}} source-backed rows, with source-backed status
`{{ablation_sensitivity_source_backed}}`, so the appendix heatmap is a rendered
view of validated JSON rather than a decorative restatement.

<!-- sheaf-track:gnn -->

GNN declarations: `gnn/bernoulli_toy.gnn.md` and `gnn/si_tmaze.gnn.md` [@gnn2023]. [@fig:gnn_ontology_concordance] and [@sec:methods_analytical] document ontology concordance for the Bernoulli toy; SI notation extends the same pattern under [@sec:methods_pymdp].

<!-- sheaf-track:ontology -->

### Ontology bindings

- `belief_entropy` → **BeliefEntropy**
- `expected_free_energy` → **ExpectedFreeEnergy**
- `location` → **HiddenState**
- `observation` → **ObservationLikelihood**
- `policy` → **PolicyPosterior**
- `sheaf_track` → **SheafFragment**


<!-- sheaf-track:animation -->

Animation is an **extension** sheaf track backed by a deterministic GIF from `scripts/render_animation.py`. This appendix row documents the track binding only; default publication still uses static SI figures ([@sec:results_si_tmaze], [@fig:si_tmaze_actions]) while the GIF remains an auditable generated artifact.

<!-- sheaf-track:animation_delta -->

The appendix `animation_delta` row points to `output/data/animation_frame_deltas.json`. The manifest records {{animation_delta_count}} adjacent-frame deltas, with `{{animation_deltas_all_nonzero}}` as the hydrated evidence that the GIF is trace-derived rather than a duplicated static frame.

<!-- sheaf-track:release_notes -->

### Appendix track: release notes evidence

`release_notes` binds `output/reports/release_notes_evidence.json` into the full
sheaf appendix. Rows: {{release_notes_row_count}}. Source-backed:
`{{release_notes_source_backed}}`.

Release notes are treated as claims, not as informal changelog prose. Each row
names a source artifact and a pass/deferred status, so the release note can say
only what validation, bundle, or semantic artifacts support. The validator
re-derives support from rows; flipping the summary bit without fixing a failed
row still fails.

`output/reports/release_attestation.json` is the compact final view over the
same boundary. It records {{release_attestation_row_count}} attestation rows for
validation, release bundle hash, license audit, semantic certificate, and
blocked-scope status, with all-attested flag `{{release_attestation_all_attested}}`.
