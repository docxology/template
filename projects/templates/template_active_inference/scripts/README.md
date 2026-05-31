# Analysis scripts

Thin orchestrators that import from `../src/` and handle I/O only.

- `run_analytical_sweep.py` — closed-form sweep over hyperparameters.
- `simulate_si_tmaze.py` — run the pymdp sophisticated-inference T-maze.
- `simulate_si_graph_world.py` — write deterministic graph-world summary/trace artifacts.
- `generate_figures.py` — render figures from generated data.
- `render_animation.py` — render the trace-derived belief trajectory GIF.
- `generate_validation_spine.py` — write provenance, reproducibility replay,
  and counterexample matrix artifacts.
- `inject_variables.py` / `z_generate_manuscript_variables.py` — hydrate
  manuscript variables from run outputs.
- `compose_manuscript.py` — sheaf-compose the multi-track sections.
- `validate_outputs.py` — run the validation gates over generated outputs.
