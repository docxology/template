# template_active_inference

Public exemplar: **sheaf-composed** Active Inference manuscript with configurable multi-track sections (analytical, pymdp, GNN, ontology, Lean, visualizations, provenance, reproducibility, counterexamples).

## Quick start

```bash
uv sync --directory projects/templates/template_active_inference --extra dev
cd projects/templates/template_active_inference
uv run python scripts/compose_manuscript.py
uv run python scripts/run_analytical_sweep.py
uv run python scripts/simulate_si_tmaze.py
uv run python scripts/simulate_si_graph_world.py
uv run python scripts/compute_statistics.py
uv run python scripts/generate_figures.py
uv run python scripts/render_animation.py
uv run python scripts/generate_validation_spine.py
uv run python scripts/z_generate_manuscript_variables.py
uv run pytest tests/ --cov=src --cov-fail-under=90
```

From repo root:

```bash
uv run python scripts/01_run_tests.py --project template_active_inference
./run.sh --project template_active_inference --pipeline --core-only
```

## Sheaf composition

Tracks are declared in [`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml) (order, renderer, optional). Sections bind fragments in [`manuscript/sheaf/manifest.yaml`](manuscript/sheaf/manifest.yaml). The composer merges them into flat `manuscript/0*.md` files for the PDF pipeline.

The first manuscript page ([`manuscript/00_00_sheaf_coverage.md`](manuscript/00_00_sheaf_coverage.md)) shows a **B/W/G heatmap** of section × track coverage (black = present, white = absent, gray = missing binding). Compose writes `output/data/sheaf_coverage_matrix.json` only; `generate_figures.py` renders the heatmap PNG and regenerates the coverage page via `ensure_coverage_artifacts`.

Hydration writes a semantic sheaf certificate at `output/data/sheaf_gluing_certificate.json`.
It also writes `output/data/sheaf_evidence_crosswalk.json` and
`output/data/validation_dependency_graph.json`. Together these artifacts bind shared
GNN/ontology symbols, typed claims, artifact producers, validation gates, and manuscript
variables so the project validates semantic agreement, not only coverage shape.
The promoted validation-spine artifacts are `output/data/artifact_provenance.json`,
`output/reports/reproducibility_replay.json`, and
`output/reports/counterexample_matrix.json`.

Section [`16_appendix_full_sheaf.md`](manuscript/16_appendix_full_sheaf.md) binds the appendix manifest row as a composability proof; live counts are injected through manuscript variables, not hand-authored in this README. Optional `layers` is methods-only; `animation` is bound in the appendix row as a sheaf fragment.

```bash
uv run python scripts/compose_manuscript.py --list-tracks
uv run python scripts/compose_manuscript.py --section methods_analytical --tracks prose,formalism
uv run python scripts/compose_manuscript.py --validate-only --strict
```

Per-section overrides: `track_order`, `include_tracks`, `exclude_tracks`. See [`AGENTS.md`](AGENTS.md).

## pymdp anchor

T-maze sophisticated inference uses planning horizon `policy_len` from measured `si_tmaze_summary.json` (see manuscript variables). Reference: [pymdp sophisticated_inference examples](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference). Logs: `output/logs/pymdp_runs.jsonl`.

## Pipeline tracks

See [`tracks.yaml`](tracks.yaml). **Pipeline:** required tracks are declared there (analytical, pymdp, Lean, GNN, ontology, visualizations, provenance, reproducibility, counterexample, manuscript). **Sheaf registry:** fragment types live in [`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml); the appendix binds the full proof row except `layers`, which is methods-only. **Deterministic extension artifacts** (thin scripts → `src/`): `simulate_si_tmaze.py` also writes `si_policy_comparison.json`; `simulate_si_graph_world.py` writes graph-world summary/trace artifacts; `render_animation.py` writes a trace-derived multi-frame GIF; `generate_validation_spine.py` writes provenance, replay, and counterexample artifacts.

Non-blocking future work is tracked in [`TODO.md`](TODO.md); current publication claims remain confined to deterministic toy Active Inference artifacts.
