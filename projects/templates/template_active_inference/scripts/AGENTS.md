# Script Notes

Scripts contain no business logic — parse arguments, resolve paths, call `../src/`
functions, print output paths to stdout for manifest collection. Use
`MPLBACKEND=Agg` and fixed seeds. The `z_`-prefixed script runs last in
lexicographic analysis order (it depends on prior outputs).

Extension scripts (`render_animation.py`, `simulate_si_graph_world.py`) delegate to
`src/visualizations/animation.py` and `src/simulation/graph_world.py`.
`generate_validation_spine.py` delegates to `src/validation_spine/` and must run
before `z_generate_manuscript_variables.py` so the semantic certificate can bind
the promoted validation-spine artifacts. The legacy `inject_variables.py`
forwarder shells out to `z_generate_manuscript_variables.py`.
