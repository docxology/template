# Abstract {#sec:abstract}

We study a minimal Active Inference stack on toy models: a Bernoulli–Ising analytical oracle, a pymdp T-maze rollout, and a sheaf-indexed compose contract that binds 10 fragment tracks into 12 flat IMRAD sections. Claims are limited to those models and their generated artifacts.

[@sec:sheaf_coverage] reports a 16-row coverage matrix (4 IMRAD group headers) regenerated from the live manifest at compose time. [@sec:methods_pymdp] documents the T-maze harness aligned with [pymdp sophisticated_inference examples](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference).

[@sec:results_invariants] records 12 / 12 invariant checks passed. SI planning horizon: 2 steps. Sweep RMSE 0 nats bounds analytical–empirical agreement on the coupling grid.
