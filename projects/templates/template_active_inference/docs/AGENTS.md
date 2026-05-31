# Agent Notes

`projects/templates/template_active_inference/docs/` is documentation only. Keep business
logic in `../src/`, orchestration in `../scripts/`, and generated artifacts
under `../output/`.

When adding a track (analytical, pymdp, Lean, GNN, ontology, provenance,
reproducibility, counterexample) or sheaf section:

- Update `../manuscript/sheaf/tracks.yaml` (registry) and `../manuscript/sheaf/manifest.yaml` (bindings).
- Update section bundles under `../manuscript/sections/`.
- Update `../tracks.yaml` pipeline gates when a track gains artifacts or scripts.
- Update project tests under `../tests/` and
  `tests/infra_tests/project/test_active_inference_project_contract.py` when
  public layout changes.
- Keep pymdp simulation claims aligned with what `src/simulation/si_runner.py`
  actually logs (default T-maze via `simulate_si_tmaze.py`; `policy_inference` mode).
- Extension tracks in `../tracks.yaml` `extension_tracks`: `render_animation.py`
  writes a deterministic trace-derived GIF; `simulate_si_graph_world.py` writes
  deterministic graph-world summary/trace JSON. Do not claim non-toy graph-world
  SI or empirical biological behavior in prose.
- Validation-spine tracks are live: `generate_validation_spine.py` writes
  provenance, reproducibility replay, and counterexample matrix artifacts.
  Future tracks should satisfy the same producer/artifact/claim/gate/negative
  control promotion rule recorded in `../TODO.md`.

Do not add network calls or LLM calls to the default exemplar path.
