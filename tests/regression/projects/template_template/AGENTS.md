# `tests/regression/projects/template_template/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_template` go under `tables/`.
Use the `pinned_values` fixture; do not hardcode expected numbers in
test bodies. Load the project's own `src` package via the
`_load_src_package` helper in `tables/test_introspection_metrics_claims.py`
(registers it under the `_template_template_src` alias) rather than a bare
`sys.path.insert` + `from src...` import at module level — every
exemplar ships a top-level `src` package, and the bare pattern collides
across projects once more than one is collected in the same pytest
session.

This exemplar introspects the LIVE repository, so re-derive every value
by calling the real `template_template.introspection` functions (and
`infrastructure.project.public_scope.public_project_names`) on the repo
root — never copy a rendered `${token}` value. Frozen structural counts
(pipeline DAG, public exemplar roster) are pinned at tolerance 0; the
live `module_count` carries an `abs_tolerance` band per the exemplar's own
convention (`manuscript/AGENTS.md` defers rotating layout facts to
`docs/_generated/COUNTS.md`). Any value edit needs a paired
`_provenance.<key>` entry.
