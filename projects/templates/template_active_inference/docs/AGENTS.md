# Agent Notes

`projects/templates/template_active_inference/docs/` is documentation only. Keep business
logic in `../src/`, orchestration in `../scripts/`, and generated artifacts
under `../output/`.

When adding a track (analytical, pymdp, Lean, GNN, ontology, provenance,
replay matrix, counterexample, sensitivity, uncertainty, benchmark,
model-checking, interop, adversarial audit, evidence fields, release bundle,
theorem traceability, gate ergonomics, assumption index, animation delta,
manuscript staleness) or sheaf section:

- Update `../manuscript/sheaf/tracks.yaml` (registry) and `../manuscript/sheaf/manifest.yaml` (bindings).
- Update section bundles under `../manuscript/sections/`.
- Update `../tracks.yaml` pipeline gates when a track gains artifacts or scripts.
- Update project tests under `../tests/` and
  `tests/infra_tests/project/test_active_inference_project_contract.py` when
  public layout changes.
- Update `reference/rendering-reproducibility.md` when producer order,
  hydration, figure rendering, copied output parity, or sheaf reproducibility
  contracts change.
- Keep pymdp simulation claims aligned with what `src/simulation/si_runner.py`
  actually logs (default T-maze via `simulate_si_tmaze.py`; `policy_inference` mode).
- Extension tracks in `../tracks.yaml` `extension_tracks`: `render_animation.py`
  writes a deterministic trace-derived GIF and frame-delta manifest; `simulate_si_graph_world.py` writes
  deterministic graph-world summary/trace JSON. Do not claim non-toy graph-world
  SI or empirical biological behavior in prose.
- Validation-spine and promoted roadmap tracks are live: `generate_validation_spine.py`,
  `generate_toy_sweep_tracks.py`, `generate_formal_interop_tracks.py`,
  `generate_integration_audit.py`, and `generate_sheaf_tracks.py` write the
  canonical provenance, replay matrix, counterexample, sensitivity, uncertainty,
  benchmark, model-checking, interop, adversarial audit, evidence-field,
  release-bundle, theorem-traceability, gate-index, semantic certificate,
  dependency graph, track-improvement, blocked-scope, and manuscript-staleness
  artifacts. Future tracks should improve canonical IDs and satisfy the same
  producer/artifact/claim/gate/negative-control promotion rule recorded in
  `../TODO.md`.

Do not add network calls or LLM calls to the default exemplar path.
