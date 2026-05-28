# Abstract {#sec:abstract}

We study a minimal Active Inference stack on toy models: a Bernoulli–Ising analytical oracle, a pymdp T-maze rollout, and a sheaf-indexed compose contract that binds {{sheaf_track_count}} fragment tracks into {{composed_section_count}} flat IMRAD sections. Claims are limited to those models and their generated artifacts.

[@sec:sheaf_coverage] reports a {{imrad_manifest_rows}}-row coverage matrix ({{imrad_group_count}} IMRAD group headers) regenerated from the live manifest at compose time. [@sec:methods_pymdp] documents the T-maze harness aligned with [pymdp sophisticated_inference examples](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference).

[@sec:results_invariants] records {{invariants_passed}} / {{invariants_total}} invariant checks passed. SI planning horizon: {{si_tmaze_policy_len}} steps. Sweep RMSE {{sweep_rmse_mi}} nats bounds analytical–empirical agreement on the coupling grid.
