# tests - AGENTS.md

Zero-mock test suite over real fixture descriptors, real temporary files, and
real generated PNGs. Never replace validator behavior with stand-ins; every
test exercises the actual `src/data_descriptor/` functions.

## Test files

| File | Covers |
| --- | --- |
| `test_descriptor.py` | Descriptor validation, negative controls, schema fingerprints, readiness scoring, field-constraint summaries, and the metadata-only release manifest. |
| `test_verification.py` | Byte-level digest/row reconciliation against real temporary CSV files: absent, checksum-mismatch, and row-mismatch cases. |
| `test_figures.py` | Plot-ready data preparers (schema rows, inventory rows, provenance steps, severity counts) and the demonstration perturbation. |
| `test_registry.py` | Project-local fail-closed figure-registry publisher: deterministic registry building, missing-file rejection, atomic publish, byte-identical output. |
| `test_generate_figures_script.py` | End-to-end integration: runs the figure script against a temporary project root and asserts real PNGs plus the figure registry are written. |
| `test_generate_release_artifacts_script.py` | End-to-end integration: runs `scripts/generate_release_artifacts.py` as a subprocess against the shipped and a deliberately-broken descriptor, and asserts the declared `output/reports/*.json` artifacts (or fail-closed absence) match. |
| `conftest.py` | Puts `src/` on `sys.path` for the suite. |

Run from the monorepo root:

```bash
uv run pytest projects/templates/template_data_descriptor/tests --cov=projects/templates/template_data_descriptor/src --cov-fail-under=90
```

See [`README.md`](README.md) for the quick reference.
