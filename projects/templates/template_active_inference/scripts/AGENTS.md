# Script Notes

Scripts contain no business logic — parse arguments, resolve paths, call `../src/`
functions, print output paths to stdout for manifest collection. Use
`MPLBACKEND=Agg` and fixed seeds. The `z_`-prefixed script runs last in
lexicographic analysis order (it depends on prior outputs).

Extension scripts (`render_animation.py`, `simulate_si_graph_world.py`) delegate to
`src/visualizations/animation.py` and `src/simulation/graph_world.py`.
`generate_validation_spine.py` delegates to `src/validation_spine/` and must run
before the promoted roadmap scripts. `generate_toy_sweep_tracks.py`,
`generate_formal_interop_tracks.py`, `generate_integration_audit.py`, and
`generate_sheaf_tracks.py` must run before
`z_generate_manuscript_variables.py` so semantic certificates, dependency
graphs, canonical promoted artifacts, and hydrated variables bind the promoted
artifacts. The canonical generators also emit diffoscope, proof-extraction,
finite state-space, causal-ablation, license-audit, and release-note evidence
artifacts; do not reintroduce parallel versioned producer scripts for the same
track families. The legacy `inject_variables.py` forwarder shells out to
`z_generate_manuscript_variables.py`.
