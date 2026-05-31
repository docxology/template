# Contributions {#sec:intro_contributions}

<!-- sheaf-track:prose -->

## Scientific contributions

1. **Analytical oracle** ([@sec:methods_analytical]): closed-form mutual information and free-energy decomposition on a symmetric Bernoulli–Ising toy with Monte Carlo cross-checks ([@sec:results_mi_sweep], [@sec:results_free_energy]).
2. **Active-inference harness** ([@sec:methods_pymdp]): deterministic pymdp T-maze rollout — default `state_inference` belief filtering, with sophisticated expected-free-energy policy inference selectable via `mode: policy_inference` — with logged beliefs, actions, and merged invariant gates ([@sec:results_si_tmaze], [@sec:results_invariants]).
3. **Sheaf-indexed composition** ([@sec:methods_sheaf]): 13 optional fragment types bind to 17 manifest rows under [@eq:coverage_cell], with a 12-track appendix composability proof ([@sec:appendix_full_sheaf]).

[@fig:multi_track_architecture] maps the three scientific tracks to 10 pipeline gates and 13 composable fragment renderers. Measured invariant checks: 12 / 12 passed.

Ontology-facing symbols are checked per model: the Bernoulli toy binds `pi1`, `pi2`, `J`, `gamma`, and `q_joint`, while the SI T-maze binds `location`, `observation`, `policy`, and `belief_entropy` to **HiddenState**, **ObservationLikelihood**, **PolicyPosterior**, and **BeliefEntropy** ([@fig:gnn_ontology_concordance], [@sec:methods_pymdp]).

<!-- sheaf-track:visualization -->

![Process diagram linking three scientific tracks to 10 pipeline gates and 13 sheaf fragment types across 17 manifest rows.](../output/figures/multi_track_architecture.png){#fig:multi_track_architecture width=95%}

*Figure I1 (intro). Multi-track architecture: analytical, pymdp, and sheaf composition lanes mapped to 10 pipeline gates and 13 composable fragment types.*

<!-- sheaf-track:ontology -->

### Ontology bindings

- `expected_free_energy` → **ExpectedFreeEnergy**
- `location` → **HiddenState**
- `observation` → **ObservationLikelihood**
- `policy` → **PolicyPosterior**

