# `tests/regression/projects/template_madlib/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_madlib` go under `tables/`.
Use the `pinned_values` fixture; do not hardcode expected numbers in
test bodies. Load the project's own `src` package via the
`_load_src_package` helper in `tables/test_configuration_counts_claims.py`
(registers it under the `_madlib_src` alias) rather than a bare
`sys.path.insert` + `from src...` import at module level — every
exemplar ships a top-level `src` package, and the bare pattern collides
across projects once more than one is collected in the same pytest
session.

**Madlib caveat (bare intra-package imports).** Unlike the other
exemplars, `template_madlib`'s `src` package uses *bare* intra-package
imports (`from config import ...`, `from analysis import ...`), not
relative imports, and it ships `config.py` / `analysis.py` / `tokens.py`
/ `manuscript_variables.py` — names that also exist in other exemplars.
The `_load_src_package` helper here therefore loads the bare submodules
in dependency order with `src/` temporarily on `sys.path`, re-homes them
under the `_madlib_src.` alias namespace, and pops the bare names back
out of `sys.modules` afterward so nothing collides. Keep that
clean-up — a plain alias `spec_from_file_location` exec (the
autoscientists shape) raises `ModuleNotFoundError: No module named
'config'` on this exemplar.
