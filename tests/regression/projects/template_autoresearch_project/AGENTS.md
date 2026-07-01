# `tests/regression/projects/template_autoresearch_project/` — agent guide

Read [`../../AGENTS.md`](../../AGENTS.md) first.

New regression tests for `template_autoresearch_project` go under
`tables/`. Use the `pinned_values` fixture; do not hardcode expected
numbers in test bodies. Import the project's own `src` package via the
`_load_project_src` helper in `tables/test_candidate_outcome_claims.py`
(inserts `PROJECT_ROOT`, imports fresh, then purges `src`/`src.*` from
`sys.modules` and `sys.path` again) rather than a bare `sys.path.insert`
+ `from src...` import at module level — every exemplar ships a
top-level `src` package, and the bare pattern collides across projects
once more than one is collected in the same pytest session.
