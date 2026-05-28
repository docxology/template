# Manuscript Notes

The numbered section files (except `00_abstract.md`, `17_conclusion.md`, and `99_references.md`) are **composed outputs** — edit fragments under `sections/imrad/` and `sheaf/manifest.yaml`, then recompose via `../scripts/compose_manuscript.py`.

`00_00_sheaf_coverage.md` is **regenerated** at compose time from `src/manuscript/sheaf/report.py` and `manuscript/sheaf/coverage.yaml`.

Run-derived numbers are hydrated tokens from `output/data/`. `config.yaml` carries publication metadata and the `sheaf:` configuration block.
