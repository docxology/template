# Lean formalization boundary {#sec:methods_lean}

<!-- sheaf-track:prose -->

The Lean method is a boundary witness track, not a broad formalization of active inference. `lake build` checks declarations under `lean/TemplateActiveInference/`; [@fig:lean_boundary_status] renders the proved/deferred surface, while generated inventories carry theorem names, constructive-token status, and axiom checks.

The theorem set links back to the finite analytical and pymdp toys. Horizon witnesses constrain the planning-depth examples, and `efe_additive_identity_from_relations` proves `(risk + ambiguity) + (pragmatic + epistemic) = 0` from the definitional relations using core integer arithmetic (`omega`). These rows join {{theorem_traceability_row_count}} linked theorem-traceability entries with all-linked flag `{{theorem_traceability_linked}}`; no prose claim is promoted unless the generated theorem, witness, and evidence-field rows agree.

<!-- sheaf-track:visualization -->

![Lean formalization boundary: module witnesses checked by lake build.](../output/figures/lean_boundary_status.png){#fig:lean_boundary_status width=90% fig-alt="Table figure listing Lean modules, declaration kinds, names, and proved versus sorry status under lean/TemplateActiveInference/."}

<!-- sheaf-track:lean -->

Lean module `TemplateActiveInference.SophisticatedInference` declares the planning-horizon parameter `defaultPolicyLen` and finite T-maze boundary witnesses: `sophisticated_requires_horizon : defaultPolicyLen > 1`, `tmaze_two_forward_steps_reach_goal`, and `tmaze_goal_absorbing`. It also contains constructive finite witnesses for graph-world reachability, finite policy enumeration, two-state belief weights, and two-policy posterior weights. These theorems formalize small finite boundaries shared with generated artifacts; they do *not* prove that the toy policy posterior is a general model of sophisticated inference. Axioms are audited with `#print axioms` (the gate whitelists only `propext`, `Classical.choice`, `Quot.sound`); see the Lean track gate.

Build via `lake build` under `lean/`.

<!-- sheaf-track:model_checking -->

The `model_checking` fragment complements Lean with finite exhaustive witnesses. `output/reports/model_checking_witnesses.json` records {{model_checking_witness_count}} toy-state witnesses and reports `{{model_checking_all_passed}}` only when no counterexample is found in the enumerated state/action space.

This is deliberately narrower than a semantic proof of all Active Inference programs. It checks the finite T-maze and graph-world boundary objects used by this manuscript and exposes the witness inventory to the same artifact and claim gates as the Lean theorem inventory. The Lean graph-world inventory witnesses {{lean_graph_world_topology_witness_count}} generated toy topology ids, with all-topologies-witnessed flag `{{lean_graph_world_all_topologies_witnessed}}`; theorem traceability contributes {{theorem_traceability_row_count}} linked rows.

<!-- sheaf-track:theorem_traceability -->

The `theorem_traceability` fragment binds Lean theorem inventory rows to finite model-checking witnesses, manuscript claims, and evidence fields. `output/data/theorem_traceability_matrix.json` records {{theorem_traceability_row_count}} traceability rows and passes only when every theorem row is linked (`{{theorem_traceability_linked}}`).

<!-- sheaf-track:proof_extraction -->

### Proof extraction track

The `proof_extraction` track extracts Lean theorem statements and proof-source
metadata into `output/data/proof_extraction_index.json`. The index currently
contains {{proof_extraction_theorem_count}} extracted theorem rows, with
constructive-token status `{{proof_extraction_all_constructive}}`.
