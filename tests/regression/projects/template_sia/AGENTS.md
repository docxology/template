# `tests/regression/projects/template_sia/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_sia` go under `tables/`.
Use the `pinned_values` fixture; do not hardcode expected numbers in
test bodies. Re-derive every value by running the real deterministic
fixture-replay loop (`infrastructure.sia.run_sia_loop` with
`live=False`), never a live/non-deterministic mode and never by
reading a rendered manuscript token. Load the project's own `src`
package via the `_load_src_package` helper in
`tables/test_generation_metrics_claims.py` (registers it under the
`_sia_src` alias) rather than a bare `sys.path.insert` +
`from src...` import at module level — every exemplar ships a
top-level `src` package, and the bare pattern collides across
projects once more than one is collected in the same pytest session.
