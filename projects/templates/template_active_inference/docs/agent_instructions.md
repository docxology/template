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

1. Edit track config in `tracks.yaml` or `manuscript/sheaf/tracks.yaml`.
2. Regenerate tracks in order (see AGENTS.md).
3. Run: `uv run pytest tests/ --cov=src --cov-fail-under=90`.
