# Contributions {#sec:intro_contributions}

<!-- sheaf-track:prose -->

## Scientific contributions

1. **Analytical oracle** ([@sec:methods_analytical]): closed-form mutual information and free-energy decomposition on a symmetric Bernoulli–Ising toy with Monte Carlo cross-checks ([@sec:results_mi_sweep], [@sec:results_free_energy]).
2. **Sophisticated-inference harness** ([@sec:methods_pymdp]): deterministic pymdp T-maze rollout with logged beliefs, actions, and merged invariant gates ([@sec:results_si_tmaze], [@sec:results_invariants]).
3. **Sheaf-indexed composition** ([@sec:methods_sheaf]): 10 optional fragment types bind to 16 manifest rows under [@eq:coverage_cell], with a 9-track appendix composability proof ([@sec:appendix_full_sheaf]).

[@fig:multi_track_architecture] maps the three scientific tracks to 7 pipeline gates and 10 composable fragment renderers. Measured invariant checks: 12 / 12 passed.

Ontology-facing symbols in the analytical track—`location`, `observation`, `policy`, and `expected_free_energy`—map to **HiddenState**, **ObservationLikelihood**, **PolicyPosterior**, and **ExpectedFreeEnergy** in the GNN concordance figure ([@fig:gnn_ontology_concordance], [@sec:methods_analytical]).

<!-- sheaf-track:visualization -->

![Process diagram linking three scientific tracks to 7 pipeline gates and 10 sheaf fragment types across 16 manifest rows.](../output/figures/multi_track_architecture.png){#fig:multi_track_architecture width=95%}

*Figure I1 (intro). Multi-track architecture: analytical, pymdp, and sheaf composition lanes mapped to 7 pipeline gates and 10 composable fragment types.*

<!-- sheaf-track:ontology -->

### Ontology bindings

- `expected_free_energy` → **ExpectedFreeEnergy**
- `location` → **HiddenState**
- `observation` → **ObservationLikelihood**
- `policy` → **PolicyPosterior**

