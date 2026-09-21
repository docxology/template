# `tests/regression/projects/template_madlib/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_madlib` go under `tables/`.
Use the `pinned_values` fixture; do not hardcode expected numbers in
test bodies. Import the exemplar's modules via the `_submodule` helper
in `tables/test_configuration_counts_claims.py`: it wraps
`importlib.import_module` and uses `spec_from_file_location` to
register `src/template_madlib/__init__.py` in `sys.modules` under the
transient `_madlib_src` alias (with `submodule_search_locations` at
`src/template_madlib/`), so the exemplar's modules import under their
unique package. The alias is still required: every exemplar ships a
top-level `src` package, and bare `from src...` imports collide across
exemplars once more than one is collected in the same pytest session.
