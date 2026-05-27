# Sheaf composition quickstart

Fragment tracks and IMRAD section bindings live in this directory. The composer writes flat `manuscript/NN_*.md` files for the PDF pipeline.

## Commands

```bash
cd projects/template_active_inference
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
uv run python scripts/compose_manuscript.py --list-tracks
```

Strict validation fails on manifest errors and gray coverage cells (bound fragment missing on disk).

## Files

| File | Role |
| --- | --- |
| [`tracks.yaml`](tracks.yaml) | Fragment registry: order, renderer id, optional flags |
| [`manifest.yaml`](manifest.yaml) | Section list, per-section `tracks:` map, optional `track_order` |
| [`coverage.yaml`](coverage.yaml) | Heatmap styling for coverage artifacts |
| [`../sections/imrad/`](../sections/imrad/) | Fragment sources (edit prose here) |

## Registry vs appendix proof

Registry track count and appendix proof size are **not hard-coded in prose**. Composed sections use `{{sheaf_track_count}}` and `{{appendix_sheaf_track_count}}`; `z_generate_manuscript_variables.py` resolves them from the live manifest and registry before PDF rendering.

## Generated output

Compose emits:

- Flat sections under `manuscript/` (e.g. `08_methods_sheaf.md`)
- `output/data/sheaf_coverage_matrix.json`
- `output/figures/sheaf_coverage_heatmap.png`
- Regenerated `manuscript/00_00_sheaf_coverage.md`

`methods_sheaf` includes the layers overview figure (Figure 6 in `figures.yaml`) and generated tables with HTML markers `sheaf-layers:registry`, `sheaf-layers:binding-matrix`, and `sheaf-layers:legend`. The coverage front page reuses the heatmap PNG with a “Coverage overview.” caption (appendix labels the same PNG as Figure 4).

Appendix binds nine fragment tracks including optional-type `animation`; only `layers` is excluded from the appendix row.

See [`AGENTS.md`](AGENTS.md) and [`../../src/manuscript/sheaf/AGENTS.md`](../../src/manuscript/sheaf/AGENTS.md) for module APIs.
