# Source Modules

Reusable logic for the Active Inference multi-track exemplar (7 pipeline tracks, 10 sheaf fragment types). Scripts under `../scripts/` are thin orchestrators that
import from here.

- `analytical/` — closed-form Active Inference math (free energy, Bernoulli toy,
  coupling, decomposition, joint distributions, hyperparameters).
- `gnn/` — Generalized Notation Notation (GNN) model parsing, the model object,
  and cross-track concordance checks.
- `simulation/` — pymdp sophisticated-inference T-maze model and deterministic runner.
- `manuscript/` — sheaf composition and run-derived manuscript variable hydration.
- `ontology/` — shared ontology-term bindings used to keep tracks consistent.
- `orchestration/` — pipeline manifest describing the analysis stages.
- `gates/` — validation gates over generated outputs.
- `visualizations/` — deterministic figure generation.
- `analysis.py`, `invariants.py` — top-level analysis entry points and invariant checks.
