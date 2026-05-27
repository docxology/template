# Manuscript Composition Notes

Manuscript numbers must be tokens hydrated from generated artifacts, never
hand-typed — this keeps prose claims traceable to evidence. The sheaf
composition is deterministic: the same section fragments and manifest always
produce the same manuscript.

## Variable injection

| Token | Source |
| --- | --- |
| `pipeline_track_count` | required tracks in `tracks.yaml` |
| `sheaf_track_count` | `manuscript/sheaf/tracks.yaml` registry size |
| `appendix_sheaf_track_count` | tracks bound in `appendix_full_sheaf` manifest row |
| `imrad_manifest_rows`, `composed_section_count`, `imrad_group_count` | live manifest (`manuscript/sheaf/counts.py`) |
| `coverage_present`, `coverage_bound`, `coverage_missing` | coverage matrix at variable generation |
| `ising_mi_saturation` | max closed-form MI on `parameter_sweep.csv` |
| `invariants_*`, `si_tmaze_*`, `sweep_*`, `pymdp_*` | analysis artifacts (`generate_variables`) |

Compose emits `{{token}}` placeholders. `scripts/z_generate_manuscript_variables.py` resolves them into `output/manuscript/` (fail-closed).

## Editing workflow

1. Edit fragments under `manuscript/sections/imrad/` and `manuscript/sheaf/manifest.yaml`.
2. `uv run python scripts/compose_manuscript.py`
3. `uv run python scripts/z_generate_manuscript_variables.py` (or pipeline stage)

Manual sections: `00_abstract.md`, `17_conclusion.md`, `99_references.md`.
