# pymdp simulation harness {#sec:methods_pymdp}

<!-- sheaf-track:prose -->

**Sophisticated inference (planning horizon).** This section documents a **pymdp state-inference harness** on a minimal T-maze ([@fig:tmaze_schematic]) with planning horizon `policy_len = 2`. Default mode is `state_inference` (T-maze rollout via `simulate_si_tmaze.py`). The Agent constructs a multi-step policy set (`num_policies` logged in SI artifacts); per-step **belief entropy** is aggregated as `mean_belief_entropy`.

Graph-world `infer_policies` is an opt-in extension stub — see `tracks.yaml` `extension_tracks.graph_world`. For the reference workflow, see [@sec:intro_motivation]; measured rollouts appear in [@sec:results_si_tmaze].

Mean belief entropy across steps: 0.3251.

<!-- sheaf-track:formalism -->

Given generative matrices $A,B,C,D$, pymdp computes state beliefs $q(s)$ via variational inference (`infer_states`). The Agent is configured with planning horizon $H =$ 2, which defines the **policy depth** used when constructing candidate policies (logged as `num_policies` in the SI summary artifact; see [@sec:results_si_tmaze]).

The default harness records belief entropy per step; extending to full expected-free-energy policy selection (`infer_policies`) is documented as a follow-on track in [@sec:discussion_outlook].

<!-- sheaf-track:pymdp -->

SI artifacts (summary, trace, optional JSONL log) record step count, actions, observations, and belief entropy for [@sec:results_si_tmaze]. Steps recorded: 2.

<!-- sheaf-track:visualization -->

![Schematic of the minimal T-maze POMDP with start and goal states, discrete actions and observations, and planning horizon policy_len = 2.](../output/figures/tmaze_schematic.png){#fig:tmaze_schematic width=85%}

*Figure M1 (methods). T-maze generative model schematic (2-step policy horizon, state_inference mode).*

<!-- sheaf-track:gnn -->

See `gnn/si_tmaze.gnn.md` for a GNN view of the T-maze hidden state, observation, and policy variables with ontology bindings.

<!-- sheaf-track:ontology -->

### Ontology bindings

- `belief_entropy` → **BeliefEntropy**
- `loc` → **HiddenState**
- `obs` → **ObservationLikelihood**
- `pi` → **PolicyPosterior**

