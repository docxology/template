# `tests/regression/projects/template_gold_refinement/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_gold_refinement` go under `tables/`.
Use the `pinned_values` fixture; do not hardcode expected numbers in
test bodies. Import the project's unique `src/template_gold_refinement` package directly via the `_submodule` helper in `tables/test_refinery_certification_claims.py` (plain `importlib.import_module` with `src/` on `sys.path`) — the package name is project-unique, so the former alias-loader collision workaround is no longer needed.path.insert` +
`from src...` import at module level — every exemplar ships a top-level
`src` package, and the bare pattern collides across projects once more
than one is collected in the same pytest session.
