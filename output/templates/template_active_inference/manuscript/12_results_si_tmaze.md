# T-maze active-inference rollout {#sec:results_si_tmaze}

<!-- sheaf-track:prose -->

The pymdp harness rolls out a T-maze active-inference agent in `state_inference` mode with planning horizon 2. The default `state_inference` mode is belief filtering with a goal-seeking action rule; sophisticated policy inference (an expected-free-energy policy posterior) is selectable via `mode: policy_inference` ([@sec:methods_pymdp]). Summary metrics land in `output/data/si_tmaze_summary.json`.

Steps recorded: 2. Mean belief entropy: 0.3251.

Policy-comparison rows: 4 across state-inference and policy-inference modes; goal-reaching rows: 3. Graph-world extension rows: 4 over 4 nodes, with goal-reached flag 1.

<!-- sheaf-track:pymdp -->

Rollout trace: `output/data/si_tmaze_trace.json`. JSONL run log: `output/logs/pymdp_runs.jsonl`.

<!-- sheaf-track:visualization -->

![Line plot of belief entropy in nats versus timestep for the pymdp T-maze rollout. Entropy ranges from 0.3251 to 0.3251 nats across 2 steps in state_inference mode.](../output/figures/si_belief_entropy_curve.png){#fig:si_belief_entropy_curve width=90%}

*Figure 3a (results). Belief entropy over time for the T-maze rollout (mean 0.3251 nats).*

![Dual-panel plot of observation index and action index versus timestep for the pymdp T-maze rollout. The upper panel shows discrete observations; the lower panel shows actions. Goal reached flag is 1.](../output/figures/si_obs_action_trace.png){#fig:si_obs_action_trace width=90%}

*Figure 3b (results). Observation and action traces for the T-maze rollout (action diversity 2).*

![Step plot of discrete action index versus timestep for the pymdp T-maze rollout in state_inference mode. Actions change at each timestep with light fill under the step trace; policy depth is 2 steps.](../output/figures/si_tmaze_actions.png){#fig:si_tmaze_actions width=90%}

*Figure 3c (results). Discrete action index over time for the pymdp T-maze rollout (policy length 2).*
