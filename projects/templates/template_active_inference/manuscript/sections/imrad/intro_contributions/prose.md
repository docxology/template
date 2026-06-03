## Scientific contributions

1. **Analytical oracle** ([@sec:methods_analytical]): closed-form mutual information and free-energy decomposition on a symmetric Bernoulli–Ising toy with an independent exact-recomputation cross-check ([@sec:results_mi_sweep], [@sec:results_free_energy]).
2. **Active-inference harness** ([@sec:methods_pymdp]): deterministic pymdp T-maze rollout — default `state_inference` belief filtering, with sophisticated expected-free-energy policy inference selectable via `mode: policy_inference` — with logged beliefs, actions, and merged invariant gates ([@sec:results_si_tmaze], [@sec:results_invariants]).
3. **Sheaf-indexed composition** ([@sec:methods_sheaf]): {{sheaf_track_count}} optional fragment types bind to {{imrad_manifest_rows}} manifest rows under [@eq:coverage_cell], with a {{appendix_sheaf_track_count}}-track appendix composability proof ([@sec:appendix_full_sheaf]).

[@fig:multi_track_architecture] maps the three scientific tracks to {{pipeline_track_count}} pipeline gates and {{sheaf_track_count}} composable fragment renderers. Measured invariant checks: {{invariants_passed}} / {{invariants_total}} passed.

Ontology-facing symbols in the analytical track—`location`, `observation`, `policy`, and `expected_free_energy`—map to **HiddenState**, **ObservationLikelihood**, **PolicyPosterior**, and **ExpectedFreeEnergy** in the GNN concordance figure ([@fig:gnn_ontology_concordance], [@sec:methods_analytical]).
