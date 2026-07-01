# `tests/regression/projects/template_textbook/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_textbook` go under `tables/`. These
bind the **structural counts** the manuscript states (parts, chapters,
chapters-per-part, labs, question banks) to the single source of truth,
`manuscript/config.yaml`, re-derived through the tested loaders
`textbook.config.unit_blocks` / `iter_chapters` / `load_config` and
`textbook.toc.build_toc` — never hardcode the expected numbers in the
test bodies; use the `pinned_values` fixture.

Load the project's own `src` package via the `_load_src_package` helper
in `tables/test_structure_claims.py` (registers it under the
`_textbook_src` alias) rather than a bare `sys.path.insert` +
`from src...` import at module level — every exemplar ships a top-level
`src` package, and the bare pattern collides across projects once more
than one is collected in the same pytest session.
