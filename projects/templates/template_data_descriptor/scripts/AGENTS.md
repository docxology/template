# scripts - AGENTS.md

Keep scripts thin and delegate all validation, figure-data preparation, and
verification to `src/data_descriptor/`. `generate_figures.py` sets
`MPLBACKEND=Agg` before importing pyplot, calls tested preparers, and writes PNGs
to `manuscript/figures/`; `generate_release_artifacts.py` serializes tested
report/manifest objects to `output/reports/`. Neither script may implement
validation logic, compute checksums inline, or hardcode dataset values — every
number must come from a tested `src/` function.

`generate_figures.py` mirrors the complete PNG set to `output/figures/` and
writes `figure_registry.json` from `DESCRIPTOR_FIGURE_SPECS`. It validates the
full source set before copying, so a missing renderer output cannot produce a
partial registry.
