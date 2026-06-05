# pymdp simulation harness {#sec:methods_pymdp}

<!-- sheaf-track:prose -->

**Sophisticated inference (planning horizon).** This section documents a **pymdp state-inference harness** on a minimal T-maze ([@fig:tmaze_schematic]) with planning horizon `policy_len = {{si_tmaze_policy_len}}`. The discrete-state active-inference framing follows the finite POMDP treatment in the synthesis and tutorial literature [@dacosta2020discrete; @smith2022tutorial], while the implementation anchor is pymdp [@pymdp2024]. Default mode is `{{pymdp_mode}}` (T-maze rollout via `simulate_si_tmaze.py`). The Agent constructs a multi-step policy set (`num_policies` logged in SI artifacts); per-step **belief entropy** is aggregated as `mean_belief_entropy`. Selecting `mode: policy_inference` enables expected-free-energy policy selection; on the default minimal T-maze (2 states / 2 observations / 2 actions, horizon 2) this yields a constant-action policy that does not reach the goal — the toy is deliberately too small to exercise sophisticated inference's advantage, so richer state spaces and longer horizons are needed for it to differ from belief filtering.

Graph-world artifacts are deterministic extension outputs declared in `tracks.yaml` `extension_tracks.graph_world`. For the reference workflow, see [@sec:intro_motivation]; measured rollouts appear in [@sec:results_si_tmaze].

Mean belief entropy across steps: {{si_tmaze_mean_belief_entropy_formatted}}.

The comparison artifact `output/data/si_policy_comparison.json` runs both `state_inference` and `policy_inference` over the declared toy horizons and seeds without replacing the default rollout. It records {{si_policy_comparison_run_count}} deterministic comparison rows, complete-grid flag {{si_policy_comparison_complete_grid}}, and {{si_policy_comparison_goal_reached_count}} goal-reaching rows under the toy transition model.

Agent construction is audited in `output/reports/pymdp_runtime_diagnostics.json`: {{pymdp_runtime_construction_count}} constructions, {{pymdp_runtime_known_warning_count}} known third-party JAX static-array warnings, and {{pymdp_runtime_unexpected_warning_count}} unexpected warnings. Policy posterior evidence is written separately to `output/data/pymdp_policy_posterior_grid.json` with {{pymdp_policy_posterior_row_count}} rows and normalized-posterior flag {{pymdp_policy_posteriors_normalized}}.

The graph-world extension is deterministic: `simulate_si_graph_world.py` writes `si_graph_world_summary.json` and `si_graph_world_trace.json` for a four-node graph-world path. The regenerated summary reports {{si_graph_world_node_count}} nodes, {{si_graph_world_steps}} steps, and goal-reached flag {{si_graph_world_goal_reached}}. The topology-trace extension records {{si_graph_world_topology_trace_count}} topology traces with agreement flag {{si_graph_world_topology_traces_agree}}.

<!-- sheaf-track:formalism -->

Given generative matrices $A,B,C,D$, pymdp computes state beliefs $q(s)$ via variational inference (`infer_states`). The Agent is configured with planning horizon $H =$ {{si_tmaze_policy_len}}, which defines the **policy depth** used when constructing candidate policies (logged as `num_policies` in the SI summary artifact; see [@sec:results_si_tmaze]).

The default harness records belief entropy per step; extending to full expected-free-energy policy selection (`infer_policies`) is documented as a follow-on track in [@sec:discussion_outlook].

<!-- sheaf-track:pymdp -->

SI artifacts (summary, trace, optional JSONL log) record step count, actions, observations, and belief entropy for [@sec:results_si_tmaze]. Steps recorded: {{si_tmaze_steps}}.

<!-- sheaf-track:interop -->

The `interop` fragment treats the GNN files, JSON views, and ontology bindings as a round-trip contract rather than parallel documentation. `output/data/interop_roundtrip_report.json` records {{interop_check_count}} deterministic checks; the manuscript only claims losslessness when `{{interop_all_lossless}}` is true.

The stricter lint artifacts are adjacent evidence, not new model claims: `output/data/gnn_roundtrip_report.json`, `output/reports/gnn_lint_report.json`, `output/data/ontology_alias_index.json`, and `output/data/ontology_profile_matrix.json` must agree before the interop row passes. A missing GNN variable, duplicate ontology alias, dropped JSON field, shape diff, or dtype diff is therefore a validation failure before rendering.

<!-- sheaf-track:visualization -->

![T-maze generative model schematic ({{si_tmaze_policy_len}}-step policy horizon, {{pymdp_mode}} mode).](../output/figures/tmaze_schematic.png){#fig:tmaze_schematic width=85% fig-alt="Schematic of the minimal T-maze POMDP with start and goal states, discrete actions and observations, and planning horizon policy_len = {{si_tmaze_policy_len}}."}

<!-- sheaf-track:gnn -->

See `gnn/si_tmaze.gnn.md` for a GNN view of the T-maze hidden state, observation, and policy variables with ontology bindings.

<!-- sheaf-track:ontology -->

### Ontology bindings

- `belief_entropy` → **BeliefEntropy**
- `loc` → **HiddenState**
- `obs` → **ObservationLikelihood**
- `pi` → **PolicyPosterior**

