# Agent Instructions — Active Inference Exemplar

## Operational Constraints

1. **Multi-track consistency.** Changes to one track (analytical, simulation,
   GNN, sheaf) must be validated against the others — tracks share claims.
2. **Regeneration order matters.** Run tracks in the declared order:
   toy-sweep → formal-interop → integration-audit → sheaf → variables.
3. **Registry source of truth.** Figure captions, alt text, and claim
   boundaries come from `figures.yaml`, not hand-authored prose.
4. **No hand-edited output.** Generated manuscript, figures, and variables
   are disposable — regenerate from source registries.

## Workflow

1. To add or modify a track's definition, edit the pipeline-gate entry in
   [`tracks.yaml`](../tracks.yaml) (id, paths, gate) and/or the sheaf
   fragment entry in [`manuscript/sheaf/tracks.yaml`](../manuscript/sheaf/tracks.yaml)
   (order, renderer, label); bind it to a manuscript section in
   [`manuscript/sheaf/manifest.yaml`](../manuscript/sheaf/manifest.yaml).
2. Regenerate the roadmap-track evidence in this exact order (matches
   [`AGENTS.md`](../AGENTS.md#regeneration-order)):
   ```bash
   uv run python scripts/generate_toy_sweep_tracks.py
   uv run python scripts/generate_formal_interop_tracks.py
   uv run python scripts/generate_integration_audit.py
   uv run python scripts/generate_sheaf_tracks.py
   uv run python scripts/z_generate_manuscript_variables.py
   ```
3. Recompose and validate the manuscript against the regenerated evidence:
   ```bash
   uv run python scripts/compose_manuscript.py
   uv run python scripts/compose_manuscript.py --validate-only --strict
   uv run python scripts/validate_outputs.py
   uv run python scripts/check_documentation_contract.py --check
   ```
4. Run the full test suite with the coverage gate:
   ```bash
   uv run pytest tests/ --cov=src --cov-fail-under=90
   ```
   (For a fast inner loop instead: `uv run pytest tests/ -k "not gate and not
   figure" --no-cov`, or the combined verification wrapper
   `uv run python scripts/run_full_verification.py`.)

For the full pipeline (analytical/pymdp/figures/animation/method-inventory
scripts in addition to the five roadmap-track generators above), see the
Quick start section of [`README.md`](../README.md#quick-start) or
[`docs/quickstart.md`](quickstart.md).
