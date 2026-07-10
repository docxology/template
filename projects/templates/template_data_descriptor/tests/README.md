# tests - template_data_descriptor

Zero-mock tests over real fixture dictionaries and real temporary files:

- `test_descriptor.py` — descriptor validation, negative controls, schema
  fingerprints, readiness scoring, and the release manifest.
- `test_verification.py` — byte-level digest/row reconciliation against real
  temporary CSV files, including absent, checksum-mismatch, and row-mismatch cases.
- `test_figures.py` — plot-ready data preparers and the demonstration perturbation.
- `test_generate_figures_script.py` — end-to-end integration: runs the figure
  script against a temporary project root and asserts real PNGs are written.

Run from the monorepo root:

```bash
uv run pytest projects/templates/template_data_descriptor/tests --cov=projects/templates/template_data_descriptor/src --cov-fail-under=90
```
