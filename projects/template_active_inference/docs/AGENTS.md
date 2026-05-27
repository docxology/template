# Agent Notes

`projects/template_active_inference/docs/` is documentation only. Keep business
logic in `../src/`, orchestration in `../scripts/`, and generated artifacts
under `../output/`.

When adding a track (analytical, pymdp, Lean, GNN, ontology) or sheaf section:

- Update `../manuscript/sheaf/tracks.yaml` (registry) and `../manuscript/sheaf/manifest.yaml` (bindings).
- Update section bundles under `../manuscript/sections/`.
- Update `../tracks.yaml` pipeline gates when a track gains artifacts or scripts.
- Update project tests under `../tests/` and
  `tests/infra_tests/project/test_active_inference_project_contract.py` when
  public layout changes.
- Keep pymdp simulation claims aligned with what `src/simulation/si_runner.py`
  actually logs (default T-maze via `simulate_si_tmaze.py`; `policy_inference` mode).
- Extension tracks in `../tracks.yaml` `extension_tracks`: `render_animation.py`
  writes a placeholder GIF; `simulate_si_graph_world.py` writes
  `status: not_implemented` JSON — do not claim full graph-world SI in prose.

Do not add network calls or LLM calls to the default exemplar path.
