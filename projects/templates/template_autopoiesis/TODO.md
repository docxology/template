# template_autopoiesis TODO

Forward-only backlog for the combinatoric-grammar exemplar that
deterministically generates whole runnable child projects (`src/`, `tests/`,
`scripts/`, `manuscript/`) with recompute-based provenance verification and a
falsifiable honesty manifest.

## Current validation evidence

- Project tests and coverage:
  `uv run pytest projects/templates/template_autopoiesis/tests/ --cov=projects/templates/template_autopoiesis/src --cov-fail-under=90`
  (add `--cov-branch` to reproduce the per-module branch figures). Test count
  and coverage move with the code — read the live numbers from
  [`docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md), not a
  literal typed here. The manuscript's `{{TEST_COUNT}}` / `{{COVERAGE_PCT}}`
  tokens come from a per-render measurement in
  `src/manuscript_variables.py::measure_test_summary`, never a hardcoded value.
- Stage-02 analysis (grammar expand, materialize, verify, figures, cover art):
  `uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_autopoiesis`
- Stage-03 manuscript render:
  `uv run python scripts/pipeline/stage_03_render.py --project templates/template_autopoiesis`

## Integrity and template-status gaps

- Keep the grammar the single source of truth in `manuscript/config.yaml`
  (`autopoiesis:` block) and all generation logic in `src/`
  (`grammar.py`, `expand.py`, `materialize.py`, `realize.py`, `sealing.py`,
  `verify.py`, `honesty.py`) — scripts stay thin orchestrators.
- Collapse the two parallel manuscript-emission paths: `src/emit_templates.py`
  is independently tested but unused in production, while
  `materialize.py::_emit_manuscript` carries its own inline stub logic. Wire
  `_emit_manuscript` through `emit_templates.emit_all()` or remove one
  implementation so a forker inherits a single tested path.
- Keep provenance recompute-based: verification must re-derive the tree hash
  from disk at check time and never trust a recorded manifest hash.

## Configurable-surface gaps

- Add per-slot documentation in `manuscript/config.yaml.example` so a forker
  can extend the grammar (new slots, options, seeds, dependency edges) without
  reading `SYNTAX.md` end to end.
- Add an optional archetype-selection filter so forks can materialize a subset
  of the combinatoric product space rather than one child per domain.

## Documentation and signposting gaps

- Keep README and `SYNTAX.md` clear that Stage 02 expands the grammar and
  materializes/verifies children, while Stage 03 renders the descriptive
  manuscript PDF.
- Finish the remaining `SPEC.md` Phase 10 items and keep them in step with the
  shipped grammar surface.

## Test and validator gaps

- Close the residual partial-branch gap at `src/figures.py:21->23`.
- Add a negative-control test that a malformed or under-specified
  `autopoiesis:` grammar block is rejected at expand time, not silently
  materialized.
- Strengthen the mutation meta-gate (`tests/test_meta_teeth.py`) with an
  additional stubbed-kernel case per domain, so green-by-construction theater
  cannot slip through as new domains are added.

## Ordered improvement ladder

1. Wire `materialize.py::_emit_manuscript` through `emit_templates.emit_all()`
   (or delete the unused implementation) so one tested emission path remains.
2. Close the `figures.py:21->23` partial branch and add the malformed-grammar
   negative control.
3. Extend the mutation meta-gate coverage across all domains and kernels.
4. Add grammar-extension docs and the archetype-selection filter to the
   configurable surface.
5. Finish `SPEC.md` Phase 10 and re-sync it with the shipped grammar.
