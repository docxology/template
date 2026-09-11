# `tests/regression/projects/template_template/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_template` go under `tables/`.
Use the `pinned_values` fixture; do not hardcode expected numbers in
test bodies. Import the project's package directly via its unique nested
name (`from template_template.core.introspection import ...`) — the repo
conftest places every `projects/*/src` on `sys.path`, so the old
`_load_src_package` alias loader (which existed to avoid a bare
`sys.modules['src']` collision under the pre-split flat layout) is retired.

This exemplar introspects the LIVE repository, so re-derive every value
by calling the real `template_template.core.introspection` functions (and
`infrastructure.project.public_scope.public_project_names`) on the repo
root — never copy a rendered `${token}` value. Frozen structural counts
(pipeline DAG, public exemplar roster) are pinned at tolerance 0; the
live `module_count` carries an `abs_tolerance` band per the exemplar's own
convention (`manuscript/AGENTS.md` defers rotating layout facts to
`docs/_generated/COUNTS.md`). Any value edit needs a paired
`_provenance.<key>` entry.
