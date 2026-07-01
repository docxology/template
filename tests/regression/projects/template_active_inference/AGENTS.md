# `tests/regression/projects/template_active_inference/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_active_inference` go under `tables/`.
Use the `pinned_values` fixture; do not hardcode expected numbers in
test bodies. Load the project's own `src` package via the
`_load_src_package` helper in
`tables/test_analytical_sweep_claims.py` (registers it under the
`_active_inference_src` alias) rather than a bare `sys.path.insert` +
`from src...` import at module level — every exemplar ships a top-level
`src` package, and the bare pattern collides across projects once more
than one is collected in the same pytest session.

**Root-venv constraint (deliberate).** This exemplar's `jax`/`pymdp`
tracks are not importable from the repo root `.venv` (numpy + scipy
only). The pins here are therefore drawn exclusively from the
numpy/scipy-only **analytical** track (`src/analytical/*`) so the tests
collect and pass under the root venv alongside every other exemplar's
regression tests. Do not add a pin whose verifier imports `jax`,
`pymdp`, or any `src/simulation/*` module that transitively needs them,
or the suite will fail to collect from the root checkout.
