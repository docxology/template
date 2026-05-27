**Sophisticated inference (planning horizon).** This section documents a **real pymdp state-inference harness** on a minimal T-maze with planning horizon `policy_len = {{si_tmaze_policy_len}}`. Default mode is `{{pymdp_mode}}` (T-maze rollout via `simulate_si_tmaze.py`). The Agent constructs a multi-step policy set (`num_policies` logged in artifacts); per-step **belief entropy** is recorded in `output/logs/pymdp_runs.jsonl` and aggregated as `mean_belief_entropy`.

Graph-world `infer_policies` is an opt-in extension stub — see `tracks.yaml` `extension_tracks.graph_world` and `scripts/simulate_si_graph_world.py`. Reference notebooks: [pymdp sophisticated_inference](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference).

Mean belief entropy across steps: {{si_tmaze_mean_belief_entropy_formatted}}.
