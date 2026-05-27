# pymdp sophisticated inference harness

<!-- sheaf-track:prose -->

**Sophisticated inference (planning horizon).** This section documents a **real pymdp state-inference harness** on a minimal T-maze with planning horizon `policy_len = {{si_tmaze_policy_len}}`. Default mode is `{{pymdp_mode}}` (T-maze rollout via `simulate_si_tmaze.py`). The Agent constructs a multi-step policy set (`num_policies` logged in artifacts); per-step **belief entropy** is recorded in `output/logs/pymdp_runs.jsonl` and aggregated as `mean_belief_entropy`.

Graph-world `infer_policies` is an opt-in extension stub — see `tracks.yaml` `extension_tracks.graph_world` and `scripts/simulate_si_graph_world.py`. Reference notebooks: [pymdp sophisticated_inference](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference).

Mean belief entropy across steps: {{si_tmaze_mean_belief_entropy_formatted}}.

<!-- sheaf-track:formalism -->

Given generative matrices $A,B,C,D$, pymdp computes state beliefs $q(s)$ via variational inference (`infer_states`). The Agent is configured with planning horizon $H =$ {{si_tmaze_policy_len}}, which defines the **policy depth** used when constructing candidate policies (logged as `num_policies` in `output/data/si_tmaze_summary.json`).

This exemplar records belief entropy per step; extending to full expected-free-energy policy selection (`infer_policies`) is documented as a follow-on track.

<!-- sheaf-track:pymdp -->

Artifact paths:

- `output/logs/pymdp_runs.jsonl` — append-only JSONL run log
- `output/data/si_tmaze_summary.json` — step count, actions, mean belief entropy
- `output/data/si_tmaze_trace.json` — rollout trace

Steps recorded: {{si_tmaze_steps}}.

<!-- sheaf-track:gnn -->

See `gnn/si_tmaze.gnn.md` for a GNN view of the T-maze hidden state, observation, and policy variables with ontology bindings.

<!-- sheaf-track:ontology -->

### Ontology bindings

- `belief_entropy` → **BeliefEntropy**
- `loc` → **HiddenState**
- `obs` → **ObservationLikelihood**
- `pi` → **PolicyPosterior**

