# Lean track

Lean 4 formalization of the exemplar's Active Inference statements — the
machine-checked formalism track.

- `TemplateActiveInference.lean` — top-level module.
- `TemplateActiveInference/` — proof modules (Bernoulli toy, sophisticated inference).
- `lakefile.lean`, `lean-toolchain` — Lake build configuration and pinned toolchain.

Build with `lake build` when `lean/lakefile.lean` is present (required pipeline track in `tracks.yaml`). Projects without a Lean tree skip the gate cleanly.
