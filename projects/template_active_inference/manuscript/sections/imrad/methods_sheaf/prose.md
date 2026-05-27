Sheaf composition glues registered fragment tracks into flat manuscript sections using `manuscript/sheaf/manifest.yaml` and `manuscript/sheaf/tracks.yaml`.

The layers overview figure (registry caption in `figures.yaml` `section_figures.methods_sheaf`) summarizes the {{sheaf_track_count}} fragment layer types and their IMRAD bindings in one panel (registry stack plus binding heatmap). The tables below list every track definition and section×track binding from the live manifest at compose time.

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
```

Each compose run emits `output/data/sheaf_coverage_matrix.json` and regenerates coverage artifacts. Partial compose (`--section`) is draft-only; the matrix always reflects the full manifest.

Coverage semantics: **black / P** = present (bound and file exists); **white / —** = absent (not bound); **gray / M** = missing (bound but file absent). Discussion limitations reference the same matrix counts (`{{coverage_present}}` / `{{coverage_bound}}` / `{{coverage_missing}}`).
