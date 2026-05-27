# Analysis scripts

Thin orchestrators that import from `../src/` and handle I/O only.

- `run_analytical_sweep.py` — closed-form sweep over hyperparameters.
- `simulate_si_tmaze.py` — run the pymdp sophisticated-inference T-maze.
- `generate_figures.py` — render figures from generated data.
- `inject_variables.py` / `z_generate_manuscript_variables.py` — hydrate
  manuscript variables from run outputs.
- `compose_manuscript.py` — sheaf-compose the multi-track sections.
- `validate_outputs.py` — run the validation gates over generated outputs.
