# `tests/regression/projects/template_methods_paper/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_methods_paper` go under `tables/`.
Use the `load_pinned_values` fixture; do not hardcode expected numbers
in test bodies. Load the project's own `src` package via the
`_load_src_package` helper in
`tables/test_compiled_plan_claims.py` (registers it under the
`_methods_paper_src` alias) rather than a bare `sys.path.insert` +
`from src...` import at module level — every exemplar ships a top-level
`src` package, and the bare pattern collides across projects once more
than one is collected in the same pytest session.

The strongest pins here are the two full SHA-256 plan hashes: they are
byte-exact and reproducible across processes/platforms because
`compile_method` uses a canonical sorted-key JSON encoding plus Kahn's
topological sort. Any change to a step, its order/kind/target, or the
method target/version flips the hash — an ideal regression sentinel.
