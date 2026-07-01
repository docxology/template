# `tests/regression/projects/template_newspaper/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_newspaper` go under `tables/`.
Use the `pinned_values` fixture; do not hardcode expected numbers in
test bodies. Load the project's own `src` package via the
`_load_src_package` helper in
`tables/test_layout_statistics_claims.py` (registers it under the
`_newspaper_src` alias) rather than a bare `sys.path.insert` +
`from src...` import at module level — every exemplar ships a
top-level `src` package, and the bare pattern collides across
projects once more than one is collected in the same pytest session.

This exemplar is a *layout/rendering* engine, not a scientific-results
manuscript, so the pinned claims are deterministic layout statistics:
the edition page count, the trim dimensions in points, and the
generated-figure count. Each is re-derived from `src` exactly as the
real render path (`newspaper.engine.build_and_render`) derives it —
`load_edition(...).page_count`,
`load_newspaper_config(...).geometry().{width,height}`, and
`len(figures.generate_all(...))` — and matches both
`manuscript/04_reproducibility.md` and `data/claim_ledger.yaml`.
