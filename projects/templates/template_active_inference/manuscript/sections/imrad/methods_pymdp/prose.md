**Sophisticated inference (planning horizon).** This section documents a **pymdp state-inference harness** on a minimal T-maze ([@fig:tmaze_schematic]) with planning horizon `policy_len = {{si_tmaze_policy_len}}`. Default mode is `{{pymdp_mode}}` (T-maze rollout via `simulate_si_tmaze.py`). The Agent constructs a multi-step policy set (`num_policies` logged in SI artifacts); per-step **belief entropy** is aggregated as `mean_belief_entropy`.

Graph-world `infer_policies` is an opt-in extension stub — see `tracks.yaml` `extension_tracks.graph_world`. For the reference workflow, see [@sec:intro_motivation]; measured rollouts appear in [@sec:results_si_tmaze].

Mean belief entropy across steps: {{si_tmaze_mean_belief_entropy_formatted}}.
