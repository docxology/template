# template_active_inference

Public exemplar: **sheaf-composed** Active Inference manuscript with configurable multi-track sections (analytical, pymdp, GNN, ontology, Lean, visualizations, provenance, replay matrix, counterexamples, sensitivity, uncertainty, benchmark, model-checking, interop, adversarial audit, evidence fields, scholarship, release bundle, theorem traceability, gate ergonomics, assumption indexing, animation deltas, and manuscript staleness).

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
uv run python scripts/generate_toy_sweep_tracks.py
uv run python scripts/generate_formal_interop_tracks.py
uv run python scripts/generate_integration_audit.py
uv run python scripts/generate_sheaf_tracks.py
uv run python scripts/z_generate_manuscript_variables.py
uv run python scripts/generate_method_inventory.py
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
The promoted validation-spine and canonical roadmap artifacts cover provenance,
replay, counterexamples, toy sweeps, uncertainty summaries, benchmark rows,
finite model-checking witnesses, interop reports, semantic gluing, dependency
graphs, evidence-field indexing, release-bundle parity, theorem traceability,
gate ergonomics, scholarship source mapping, artifact diffing, Lean proof extraction, finite state-space
catalogs, causal ablations, artifact license checks, release-note evidence,
track-improvement scope, and adversarial/scope audits. Live track IDs are stable
canonical names; future work improves those tracks rather than adding `_vN`
siblings.

Section [`16_appendix_full_sheaf.md`](manuscript/16_appendix_full_sheaf.md) binds the appendix manifest row as a composability proof; live counts are injected through manuscript variables, not hand-authored in this README. Optional `layers` is methods-only; `animation` is bound in the appendix row as a sheaf fragment.

The reproducible rendering contract is documented in
[`docs/reference/rendering-reproducibility.md`](docs/reference/rendering-reproducibility.md):
authored fragments/configs generate deterministic data, figures, composed
Markdown, hydrated Markdown, PDF/web outputs, and copied root outputs through one
hydration boundary.

```bash
uv run python scripts/compose_manuscript.py --list-tracks
uv run python scripts/compose_manuscript.py --section methods_analytical --tracks prose,formalism
uv run python scripts/compose_manuscript.py --validate-only --strict
```

Per-section overrides: `track_order`, `include_tracks`, `exclude_tracks`. See [`AGENTS.md`](AGENTS.md).

## pymdp anchor

T-maze sophisticated inference uses planning horizon `policy_len` from measured `si_tmaze_summary.json` (see manuscript variables). `simulate_si_tmaze.py` also writes `si_policy_comparison.json`, `pymdp_policy_posterior_grid.json`, and `pymdp_runtime_diagnostics.json`; the last file captures the known third-party JAX static-array warning and fails validation on unexpected construction warnings. Reference: [pymdp sophisticated_inference examples](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference). Logs: `output/logs/pymdp_runs.jsonl`.

## Pipeline tracks

See [`tracks.yaml`](tracks.yaml). **Pipeline:** required tracks are declared there, including the core analytical/pymdp/formal/notation/visual tracks, validation spine, and canonical promoted roadmap tracks. **Sheaf registry:** fragment types live in [`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml); the appendix binds the full proof row except `layers`, which is methods-only. **Deterministic extension artifacts** (thin scripts -> `src/`): `simulate_si_tmaze.py` writes policy comparison, posterior-grid, and runtime-diagnostic artifacts; `simulate_si_graph_world.py` writes graph-world summary/trace artifacts; `render_animation.py` writes a trace-derived multi-frame GIF plus frame-delta manifest; `generate_validation_spine.py`, `generate_toy_sweep_tracks.py`, `generate_formal_interop_tracks.py`, `generate_integration_audit.py`, and `generate_sheaf_tracks.py` write the canonical validation spine, semantic certificate, dependency graph, evidence-field index, release-bundle manifest, theorem traceability matrix, gate index, artifact diffoscope, proof extraction index, state-space catalog, causal-ablation matrix, artifact license audit, release-note evidence, and promoted audit artifacts.

Non-blocking future work is tracked in [`TODO.md`](TODO.md); current publication claims remain confined to deterministic toy Active Inference artifacts.

## Method inventory

Every Python `def` and `class` under `src/` and `scripts/` is documented in the
generated reference [`docs/reference/method-inventory.md`](docs/reference/method-inventory.md).
Regenerate it after method, script, or module changes:

```bash
uv run python scripts/generate_method_inventory.py
```

The inventory distinguishes inline docstrings from inventory fallbacks, so missing
docstrings remain visible without bloating internal helper code.
