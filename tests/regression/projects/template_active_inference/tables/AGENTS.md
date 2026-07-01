# tables/ — agent guide

One test file per manuscript claim group (currently
`test_analytical_sweep_claims.py`). Use the `pinned_values` fixture;
load values from the per-project JSON. Provenance discipline per
[`../../../AGENTS.md`](../../../AGENTS.md).

Keep verifiers inside the numpy/scipy-only analytical track
(`src/analytical/*`) so the suite collects under the root `.venv` — see
[`../AGENTS.md`](../AGENTS.md).
