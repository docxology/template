# Analysis scripts

Thin orchestrators that import from `../src/` and handle I/O only.

- `run_analytical_sweep.py` — closed-form sweep over hyperparameters.
- `simulate_si_tmaze.py` — run the pymdp sophisticated-inference T-maze, policy comparison, posterior grid, and runtime diagnostics.
- `simulate_si_graph_world.py` — write deterministic graph-world summary/trace artifacts.
- `generate_figures.py` — render figures from generated data.
- `render_animation.py` — render the trace-derived belief trajectory GIF.
- `generate_validation_spine.py` — write provenance, deterministic replay,
  and counterexample matrix artifacts.
- `generate_toy_sweep_tracks.py` — write sensitivity, uncertainty, benchmark,
  measured policy-grid, EFE, analytical-observable, graph-world topology-trace,
  graph-world invariant, state-space catalog, and causal-ablation artifacts.
- `generate_formal_interop_tracks.py` — write model-checking, GNN, ontology,
  interop, Lean theorem inventory, and proof-extraction artifacts.
- `generate_integration_audit.py` — write producer/stale/token/figure/scope/claim/adversarial, diffoscope, license, and release-note audit artifacts.
- `generate_sheaf_tracks.py` — write the canonical semantic certificate,
  dependency graph, evidence-field index, release-bundle manifest, theorem
  traceability matrix, gate index, artifact diffoscope, proof extraction index,
  state-space catalog, causal-ablation matrix, artifact license audit,
  release-note evidence, track-improvement scope, blocked-scope manifest, and
  consolidated promoted track artifacts.
- `generate_method_inventory.py` — regenerate `docs/reference/method-inventory.md`
  from the live `src/` and `scripts/` AST so every `def` and `class` has a
  documented reference entry.
- `inject_variables.py` / `z_generate_manuscript_variables.py` — hydrate
  manuscript variables from run outputs.
- `compose_manuscript.py` — sheaf-compose the multi-track sections.
- `validate_outputs.py` — run the validation gates over generated outputs.
