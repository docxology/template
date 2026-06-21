# Simulation Track Notes

Deterministic simulation support for the SI T-maze, pymdp/JAX integration,
graph-world traces, policy posteriors, runtime diagnostics, and simulation
invariants.

## Where To Look

| Task | Location |
| --- | --- |
| YAML config, hash, overrides | `pymdp_config.py` |
| pymdp/JAX availability and warnings | `pymdp_runtime.py` |
| T-maze generative model | `tmaze_model.py`, `cue_tmaze_model.py` |
| Sophisticated-inference loop | `si_runner.py`, `si_belief.py`, `si_policy.py`, `si_loop.py`, `si_artifacts.py` |
| Graph-world extension | `graph_world.py` |
| EFE/precision/Dirichlet tracks | `efe_decomposition.py`, `precision_sweep.py`, `dirichlet_learning.py` |
| Run summaries and invariants | `statistics.py`, `invariants.py`, `logging_utils.py` |

## Contracts

- Runs must be reproducible: fixed seed, fixed horizon/policy depth, stable JSON
  key order where artifacts are compared by gates.
- Keep `pymdp.yaml` and `pymdp_config.py` in sync; manuscript variables expose
  `pymdp_mode` and `pymdp_config_hash`.
- `si_runner.py` is the public facade. Keep heavy loop, policy, belief, and
  artifact logic in the split `si_*` modules.
- The sophisticated-inference model must stay concordant with `gnn/si_tmaze.gnn.md`
  and ontology bindings; update all three lanes together.
- Runtime diagnostics distinguish known optional-dependency warnings from
  unexpected warnings. Do not hide unexpected warnings to green validation.

## Commands

```bash
uv run python scripts/simulate_si_tmaze.py --seed 0 --mode state_inference
uv run python scripts/simulate_si_graph_world.py
uv run python scripts/compute_statistics.py
uv run pytest tests/test_pymdp_config.py tests/test_si_runner.py tests/test_simulation_invariants.py
```

## Outputs

- `output/logs/pymdp_runs.jsonl`
- `output/reports/si_tmaze_run_report.json`
- `output/reports/pymdp_runtime_diagnostics.json`
- `output/data/si_policy_comparison.json`
- `output/data/pymdp_policy_posterior_grid.json`
- `output/data/si_graph_world_summary.json`
- `output/data/si_graph_world_trace.json`
