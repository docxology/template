# Validation invariants {#sec:results_invariants}

<!-- sheaf-track:prose -->

The analytical invariant registry runs before PDF rendering ([@sec:methods_analytical]). On a clean checkout **{{invariants_passed}} / {{invariants_total}}** checks pass in the merged validation report, which records simulation invariants when the pymdp harness ran ([@sec:results_si_tmaze]).

[@fig:invariant_dashboard] lists each analytical and simulation gate; failures block publication artifacts. See [@sec:methods_sheaf] for how invariant counts hydrate manuscript tokens.

<!-- sheaf-track:simulation -->

Simulation invariants merge into the analytical report after the pymdp harness runs ([@sec:results_si_tmaze]). [@fig:invariant_dashboard] summarizes pass/fail status for both domains on the clean tree.

<!-- sheaf-track:replay_matrix -->

The replay matrix exposes deterministic rerun comparison as table data rather than prose. It contains {{replay_matrix_row_count}} producer rows, uses explicit replay-or-fingerprint methods, and every row must match its saved artifact hash (`{{replay_matrix_all_matched}}`).

<!-- sheaf-track:sensitivity -->

The `sensitivity` fragment binds the deterministic toy sweep to the canonical sheaf track. `output/data/sensitivity_sweep.json` contains {{sensitivity_cell_count}} cells across toy parameters, policy modes, seeds, horizons, and graph topologies; the hydrated flag `{{sensitivity_complete_grid}}` is the only manuscript claim about coverage.

The companion `output/data/si_policy_grid.json` records measured policy-mode rows derived from `si_policy_comparison.json`, not a synthetic grid. Missing cells fail the artifact schema before they can become prose; the topology trace artifact contributes {{si_graph_world_topology_trace_count}} deterministic topology traces.

<!-- sheaf-track:uncertainty -->

The `uncertainty` fragment reports only normalized toy summaries. `output/data/uncertainty_summary.json` contains {{uncertainty_row_count}} belief and policy-posterior rows plus {{uncertainty_bin_count}} finite entropy bins, and `{{uncertainty_all_normalized}}` is false if any posterior row fails to sum to one within the deterministic tolerance.

Policy uncertainty is recorded in generated policy artifacts rather than hand-entered into the manuscript. The posterior grid contributes {{pymdp_policy_posterior_available_count}} available posterior rows; the EFE values artifact reports availability-or-measured-fallback flag {{si_policy_efe_rows_explained}}. The fragment is therefore a validation surface, not an empirical uncertainty claim.

<!-- sheaf-track:benchmark -->

The `benchmark` fragment adds a compact toy matrix over the Bernoulli, T-maze, and graph-world artifacts. `output/data/toy_benchmark_matrix.json` reports {{benchmark_model_count}} model rows and `{{benchmark_all_models_complete}}` only when each row names an artifact, metric, and passing gate.

The matrix is scoped to deterministic exemplar models. It is useful as a cross-track smoke test, not as a performance benchmark for biological or deployed systems.

<!-- sheaf-track:visualization -->

![Invariant dashboard: {{invariants_passed}} / {{invariants_total}} merged analytical and simulation checks from the validation registry.](../output/figures/invariant_dashboard.png){#fig:invariant_dashboard width=90% fig-alt="Horizontal bar checklist of analytical and simulation invariant names with pass or fail status. {{invariants_passed}} of {{invariants_total}} checks pass on the merged report."}

<!-- sheaf-track:state_space_catalog -->

### State-space catalog track

The `state_space_catalog` track enumerates finite state spaces, action spaces,
and policy counts for the deterministic toy models. The catalog artifact is
`output/data/state_space_catalog.json`: it currently records
{{state_space_catalog_row_count}} rows, with finite-space status
`{{state_space_catalog_all_finite}}`.

<!-- sheaf-track:causal_ablation -->

### Causal ablation track

The `causal_ablation` track records deterministic toy ablations over finite
preferences, likelihood-noise settings, and graph-topology perturbations. The
matrix artifact is `output/data/causal_ablation_matrix.json`: it currently
records {{causal_ablation_row_count}} cells, with complete-grid status
`{{causal_ablation_complete_grid}}`.
