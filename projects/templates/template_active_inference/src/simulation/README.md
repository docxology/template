# Simulation (pymdp track)

Deterministic pymdp and toy graph-world simulation surfaces for the Active
Inference exemplar. These modules produce finite, public, toy-only artifacts;
they do not support empirical or non-toy claims.

- `tmaze_model.py`, `cue_tmaze_model.py` — finite generative models used by
  the T-maze tracks.
- `si_runner.py` — facade for deterministic sophisticated-inference rollout and
  artifact persistence.
- `si_belief.py`, `si_policy.py`, `si_loop.py`, `si_artifacts.py` — belief,
  policy, rollout, and JSON artifact helpers.
- `pymdp_config.py`, `pymdp_runtime.py` — config hashing and scoped runtime
  diagnostics, including expected-warning/fallback rows.
- `graph_world.py` — deterministic finite graph-world summary and trace
  producer.
- `precision_sweep.py`, `efe_decomposition.py`, `dirichlet_learning.py` —
  supporting toy sweeps used by figures and manuscript tokens.
- `statistics.py`, `invariants.py`, `logging_utils.py` — run summaries,
  invariant checks, and JSONL logging.
