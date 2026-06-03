## What this demonstrates

The result of this manuscript is a *discipline*, not a domain claim: across three toy models every reported number is hydrated from a generated artifact, {{sheaf_law_count}} sheaf axioms are machine-checked before composition, and {{counterexample_count}} negative controls keep each failure path live. No statistic, figure, or cross-track claim here can drift from its artifact without failing a gate before the PDF is built.

## Limitations

The Bernoulli–Ising toy, T-maze harness, and sheaf composition model are pedagogical. They validate analytical consistency, artifact wiring, renderer dispatch, and manuscript hydration—not empirical claims about biological agents. Default pymdp mode is `{{pymdp_mode}}` with planning horizon {{si_tmaze_policy_len}}; the policy-comparison artifact exposes policy-inference rows without changing the default rollout ([@sec:methods_pymdp]).

## Sheaf audit and outlook

[@sec:sheaf_coverage] and [@sec:appendix_full_sheaf] make binding state auditable under strict compose validation ([@sec:methods_sheaf]). Pipeline extensions in `tracks.yaml` `extension_tracks` now write deterministic artifacts: a belief GIF via `render_animation.py` and graph-world SI summary/trace via `simulate_si_graph_world.py`. The appendix row already binds an `animation` sheaf fragment without new manifest rows.

Sweep RMSE {{sweep_rmse_mi}} nats and SI goal reached {{si_goal_reached}} summarize measured agreement on the declared grids and rollout. Future work includes full expected-free-energy policy selection, richer graph-world rollouts, and expanded Lean proofs beyond the boundary witnesses in [@sec:methods_lean].

The discussion ontology binds `coverage_semantics` to the audit matrix in [@sec:sheaf_coverage], `pedagogical_scope` to the non-empirical scope of the toy models, and `state_inference_mode` to the pymdp harness contract in [@sec:methods_pymdp].
