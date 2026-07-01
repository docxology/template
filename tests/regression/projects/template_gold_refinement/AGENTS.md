# `tests/regression/projects/template_gold_refinement/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_gold_refinement` go under `tables/`.
Use the `pinned_values` fixture; do not hardcode expected numbers in
test bodies. Load the project's own `src` package via the
`_load_src_package` helper in
`tables/test_refinery_certification_claims.py` (registers it under the
`_gold_refinement_src` alias) rather than a bare `sys.path.insert` +
`from src...` import at module level — every exemplar ships a top-level
`src` package, and the bare pattern collides across projects once more
than one is collected in the same pytest session.
